"""Policy engine: (event, state, rules, AI interpretation) -> Decision.

This is deterministic on purpose. The AI describes the reply; this module decides. Anyone in RevOps can
read the function top to bottom and predict what the system will do, and every branch is unit-tested.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .compliance import ComplianceResult
from .eligibility import EligibilityResult, in_icp
from .models import Action, AIResult, Decision, Intent, RiskFlag
from .policy import Policy


def _apply_mode(policy: Policy, decision: Decision) -> Decision:
    """Turn the policy's automation mode into automated/requires_review flags."""
    mode = policy.mode_for(decision.action)
    decision.trace.append({"step": "automation_mode", "action": decision.action.value, "mode": mode})
    if decision.action in (Action.NO_ACTION, Action.ESCALATE_TO_HUMAN):
        decision.automated = decision.action == Action.ESCALATE_TO_HUMAN and mode != "off"
        decision.requires_review = decision.action == Action.ESCALATE_TO_HUMAN
        return decision
    if mode == "auto":
        decision.automated = True
    elif mode == "assisted":
        decision.automated = False
        decision.requires_review = True
        decision.proposed_action = decision.action
        decision.reason += f" | '{decision.action.value}' is in assisted mode: waiting for human approval"
    else:  # off
        decision.reason += f" | '{decision.action.value}' automation is OFF: logged, not executed"
        decision.proposed_action = decision.action
        decision.action = Action.NO_ACTION
        decision.automated = False
    return decision


def _escalate(reason: str, trace: list, proposed: Action | None = None, payload: dict | None = None) -> Decision:
    return Decision(action=Action.ESCALATE_TO_HUMAN, automated=True, requires_review=True, reason=reason,
                    trace=trace, proposed_action=proposed, payload=payload or {})


# ----------------------------------------------------------------------------------
def decide_prospect_identified(account: dict, contact: dict, elig: EligibilityResult, policy: Policy) -> Decision:
    trace: list[dict[str, Any]] = [{"step": "eligibility", **elig.as_dict()}]
    if not elig.eligible:
        if "suppressed" in elig.blockers or "contact_opted_out" in elig.blockers:
            d = Decision(action=Action.NO_ACTION, automated=False, reason=f"blocked: {', '.join(elig.blockers)}", trace=trace)
        else:
            d = Decision(action=Action.NO_ACTION, automated=False, reason=f"not eligible for outreach: {', '.join(elig.blockers)}", trace=trace)
        return _apply_mode(policy, d)
    if not contact.get("enriched"):
        d = Decision(action=Action.ENRICH_CONTACT, automated=True, reason="eligible; contact lacks enrichment data", trace=trace,
                     payload={"contact_id": contact["id"]})
        return _apply_mode(policy, d)
    d = Decision(action=Action.ENROLL_IN_SEQUENCE, automated=True, reason="eligible and enriched; start outreach sequence", trace=trace,
                 payload={"contact_id": contact["id"], "sequence": f"outbound-{(account.get('country') or 'mx').lower()}-v1"})
    return _apply_mode(policy, d)


def decide_reply(
    *, account: dict, contact: dict, elig: EligibilityResult, compliance: ComplianceResult,
    ai: AIResult | None, policy: Policy, reply_at: datetime,
) -> Decision:
    trace: list[dict[str, Any]] = [
        {"step": "eligibility", **elig.as_dict()},
        {"step": "compliance", **compliance.as_dict()},
    ]

    # 1. Compliance first. A rule, not a model, decides that we stop contacting someone.
    if compliance.opt_out:
        d = Decision(action=Action.SUPPRESS_CONTACT, automated=True,
                     reason=f"opt-out detected by rule ({compliance.opt_out_matches[0]}); compliance never depends on the model",
                     trace=trace, payload={"contact_id": contact["id"], "email": contact["email"], "reason": "opt_out_reply"})
        d = _apply_mode(policy, d)
        # If the AI also saw something else (a referral, interest), a human should look, but nothing else is automated.
        if ai and ai.interpretation and ai.interpretation.intent in (Intent.MIXED, Intent.REFERRAL, Intent.INTERESTED):
            d.requires_review = True
            d.reason += " | reply also contains other signals; queued for human review with NO further automatic action"
        return d

    # 2. State first, language second. A customer or an account with an AE is not ours to touch.
    if "already_customer" in elig.blockers:
        d = Decision(action=Action.NOTIFY_CSM, automated=True,
                     reason="account is now a customer: outreach suppressed, Customer Success notified", trace=trace,
                     payload={"account_id": account["id"], "contact_id": contact["id"], "csm_id": account.get("csm_id")})
        return _apply_mode(policy, d)
    if "active_opportunity" in elig.blockers:
        d = Decision(action=Action.NOTIFY_CSM, automated=True,
                     reason=f"account has an open opportunity owned by {account.get('owner_ae_id')}: forward the reply, do not act", trace=trace,
                     payload={"account_id": account["id"], "contact_id": contact["id"], "csm_id": account.get("owner_ae_id"), "kind": "ae"})
        return _apply_mode(policy, d)
    if "suppressed" in elig.blockers or "contact_opted_out" in elig.blockers:
        return _apply_mode(policy, Decision(action=Action.NO_ACTION, automated=False,
                                            reason=f"reply from a suppressed contact/account ({', '.join(elig.blockers)}): logged only", trace=trace))

    # 3. Rule-level injection suspicion is a hard stop for automation.
    if compliance.injection_suspected:
        return _escalate("reply looks like an attempt to instruct the system (prompt injection heuristics matched); no automatic action",
                         trace)

    # 4. The AI has to have produced something valid.
    if ai is None or ai.interpretation is None or not ai.valid:
        why = "; ".join(ai.validation_errors) if ai else "no AI result"
        if ai and ai.refused:
            why = "model refused to process the reply"
        return _escalate(f"AI output unavailable or failed validation ({why}); human decides", trace)

    interp = ai.interpretation
    trace.append({"step": "ai", "intent": interp.intent.value, "confidence": interp.confidence,
                  "risk_flags": [f.value for f in interp.risk_flags], "language": interp.language, "mode": ai.mode})

    # 5. Risk flags the model raised.
    if RiskFlag.PROMPT_INJECTION in interp.risk_flags:
        return _escalate("model flagged prompt injection; no automatic action", trace)
    if RiskFlag.LEGAL_OR_COMPLAINT in interp.risk_flags:
        return _escalate("legal threat or complaint detected; humans handle this", trace)
    if RiskFlag.UNSUBSCRIBE_REQUEST in interp.risk_flags and interp.intent != Intent.UNSUBSCRIBE:
        # Model saw an opt-out the regex missed. Safer to suppress AND review than to keep going.
        d = Decision(action=Action.SUPPRESS_CONTACT, automated=True, requires_review=True,
                     reason="model detected an unsubscribe request the rules missed: suppressing and asking a human to confirm the rest",
                     trace=trace, payload={"contact_id": contact["id"], "email": contact["email"], "reason": "opt_out_reply_ai"})
        return _apply_mode(policy, d)

    # 6. Ambiguity and confidence gates.
    if interp.intent in (Intent.MIXED, Intent.UNCLEAR):
        return _escalate(f"intent '{interp.intent.value}' is not actionable automatically", trace)
    if RiskFlag.CONTRADICTORY_SIGNALS in interp.risk_flags:
        return _escalate("contradictory signals in the reply", trace, proposed=policy.intent_actions.get(interp.intent))
    threshold = policy.ai.min_confidence_auto
    if interp.intent in policy.ai.high_risk_intents:
        threshold = max(threshold, policy.ai.min_confidence_high_risk)
    if interp.confidence < threshold:
        return _escalate(f"confidence {interp.confidence:.2f} below threshold {threshold:.2f} for intent '{interp.intent.value}'",
                         trace, proposed=policy.intent_actions.get(interp.intent))

    # 7. Deterministic mapping intent -> action, with the exceptions that need state.
    action = policy.intent_actions.get(interp.intent, Action.ESCALATE_TO_HUMAN)
    payload: dict[str, Any] = {"contact_id": contact["id"], "account_id": account["id"], "summary": interp.summary}

    if interp.intent == Intent.PRICING_QUESTION and not in_icp(account, policy):
        return _escalate("pricing question from an account outside ICP: route to self-serve or a human, not to an AE",
                         trace, proposed=Action.HANDOFF_TO_AE)

    if action == Action.HANDOFF_TO_AE:
        payload.update({"owner_ae_id": account.get("owner_ae_id"), "proposed_meeting": interp.extracted.proposed_meeting,
                        "notes": interp.summary})
    elif action == Action.WAIT_UNTIL:
        raw = interp.extracted.return_date or interp.extracted.follow_up_date
        until = date.fromisoformat(raw) if raw else reply_at.date() + timedelta(days=policy.defaults.wait_days_when_no_date)
        payload.update({"wait_until": until.isoformat(), "source": "stated" if raw else "default"})
    elif action == Action.CREATE_REFERRAL_CONTACT:
        if not interp.extracted.referral_email:
            return _escalate("referral without an email address in the reply: a human finds the contact", trace, proposed=action)
        payload.update({"email": interp.extracted.referral_email, "name": interp.extracted.referral_name})
    elif action == Action.SUPPRESS_CONTACT:
        payload.update({"email": contact["email"], "reason": "unsubscribe_intent"})
    elif action == Action.NURTURE_LONG_TERM:
        payload.update({"lifecycle": "nurture", "current_tool": interp.extracted.current_tool})

    d = Decision(action=action, automated=True, reason=f"intent '{interp.intent.value}' (confidence {interp.confidence:.2f}) -> {action.value}",
                 trace=trace, payload=payload)
    return _apply_mode(policy, d)


def decide_unsubscribed(contact: dict, policy: Policy) -> Decision:
    d = Decision(action=Action.SUPPRESS_CONTACT, automated=True, reason="explicit unsubscribe event from the outreach tool",
                 trace=[], payload={"contact_id": contact["id"], "email": contact["email"], "reason": "unsubscribe_event"})
    return _apply_mode(policy, d)
