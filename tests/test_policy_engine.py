"""The policy engine decides. The model only describes. These tests pin every gate."""

from datetime import timedelta

from growth_orchestrator.compliance import check_reply
from growth_orchestrator.decision import decide_reply
from growth_orchestrator.eligibility import evaluate
from growth_orchestrator.models import Action, AIResult, ExtractedFacts, Intent, ReplyInterpretation, RiskFlag

from .conftest import (INTERESTED_ES, LATER_ES, MIXED_ES, OOO_EN_NO_DATE, OPTOUT_ES, PRICING_ES, REFERRAL_ES, UNCLEAR, reply)


def _ai(intent, confidence, flags=(), **extracted):
    interp = ReplyInterpretation(intent=intent, confidence=confidence, language="es", evidence=["x"],
                                 extracted=ExtractedFacts(**extracted), risk_flags=list(flags), summary="s")
    return AIResult(interpretation=interp, valid=True, mode="offline", model="test", prompt_version="test")


def _decide(rt, contact_id, text, ai, policy=None):
    contact = rt.db.one("SELECT * FROM contacts WHERE id=?", (contact_id,))
    account = rt.db.one("SELECT * FROM accounts WHERE id=?", (contact["account_id"],))
    policy = policy or rt.policies.load()
    elig = evaluate(rt.db, account, contact, policy, rt.clock(), purpose="reply")
    return decide_reply(account=account, contact=contact, elig=elig, compliance=check_reply(text), ai=ai, policy=policy, reply_at=rt.clock())


def test_opt_out_rule_beats_a_model_that_says_interested(rt):
    # Adversarial: the model claims "interested" with high confidence, the text asks to stop.
    d = _decide(rt, "c_lucia", OPTOUT_ES, _ai(Intent.INTERESTED, 0.99))
    assert d.action == Action.SUPPRESS_CONTACT and d.automated
    assert d.requires_review  # a human double-checks the odd disagreement, but nothing else runs


def test_low_confidence_escalates_with_the_proposed_action_attached(rt):
    d = _decide(rt, "c_lucia", INTERESTED_ES, _ai(Intent.INTERESTED, 0.6))
    assert d.action == Action.ESCALATE_TO_HUMAN and d.requires_review
    assert d.proposed_action == Action.HANDOFF_TO_AE


def test_high_risk_intents_need_the_higher_threshold(rt):
    d = _decide(rt, "c_camilo", REFERRAL_ES, _ai(Intent.REFERRAL, 0.8, referral_email="maria.torres@solenergia.co"))
    assert d.action == Action.ESCALATE_TO_HUMAN  # 0.8 < 0.85 for referral


def test_mixed_and_unclear_are_never_automated(rt):
    assert _decide(rt, "c_lucia", UNCLEAR, _ai(Intent.UNCLEAR, 0.3)).action == Action.ESCALATE_TO_HUMAN
    assert _decide(rt, "c_lucia", "texto", _ai(Intent.MIXED, 0.9)).action == Action.ESCALATE_TO_HUMAN


def test_model_prompt_injection_flag_blocks_automation(rt):
    d = _decide(rt, "c_lucia", "texto inocuo", _ai(Intent.INTERESTED, 0.95, flags=[RiskFlag.PROMPT_INJECTION]))
    assert d.action == Action.ESCALATE_TO_HUMAN


def test_model_detected_unsubscribe_missed_by_rules_suppresses_and_reviews(rt):
    d = _decide(rt, "c_lucia", "texto inocuo", _ai(Intent.INTERESTED, 0.9, flags=[RiskFlag.UNSUBSCRIBE_REQUEST]))
    assert d.action == Action.SUPPRESS_CONTACT and d.requires_review


def test_assisted_mode_proposes_instead_of_executing(rt):
    d = _decide(rt, "c_camilo", REFERRAL_ES, _ai(Intent.REFERRAL, 0.95, referral_email="maria.torres@solenergia.co"))
    assert d.action == Action.CREATE_REFERRAL_CONTACT
    assert not d.automated and d.requires_review and d.proposed_action == Action.CREATE_REFERRAL_CONTACT


def test_off_mode_logs_only(rt):
    policy = rt.policies.load().model_copy(deep=True)
    policy.automation[Action.HANDOFF_TO_AE] = "off"
    d = _decide(rt, "c_lucia", INTERESTED_ES, _ai(Intent.INTERESTED, 0.95), policy)
    assert d.action == Action.NO_ACTION and not d.automated
    assert d.proposed_action == Action.HANDOFF_TO_AE


def test_pricing_question_outside_icp_goes_to_a_human(rt):
    d = _decide(rt, "c_mateo", PRICING_ES, _ai(Intent.PRICING_QUESTION, 0.9, company_size=40))
    assert d.action == Action.ESCALATE_TO_HUMAN


def test_pricing_question_inside_icp_is_a_handoff(rt):
    d = _decide(rt, "c_lucia", "¿Cuánto cuesta?", _ai(Intent.PRICING_QUESTION, 0.9))
    assert d.action == Action.HANDOFF_TO_AE


def test_referral_without_email_needs_a_human(rt):
    d = _decide(rt, "c_lucia", "Habla con mi socio Roberto.", _ai(Intent.REFERRAL, 0.95, referral_name="Roberto"))
    assert d.action == Action.ESCALATE_TO_HUMAN and d.proposed_action == Action.CREATE_REFERRAL_CONTACT


def test_wait_uses_stated_date_or_default(rt):
    d = _decide(rt, "c_lucia", LATER_ES, _ai(Intent.LATER, 0.9, follow_up_date="2027-01-01"))
    assert d.action == Action.WAIT_UNTIL and d.payload["wait_until"] == "2027-01-01" and d.payload["source"] == "stated"
    d = _decide(rt, "c_lucia", OOO_EN_NO_DATE, _ai(Intent.OUT_OF_OFFICE, 0.9))
    expected = (rt.clock().date() + timedelta(days=rt.policies.load().defaults.wait_days_when_no_date)).isoformat()
    assert d.payload["wait_until"] == expected and d.payload["source"] == "default"


def test_end_to_end_mixed_reply_suppresses_and_reviews_without_irreversible_action(rt):
    out = reply(rt, "c_hugo", MIXED_ES)
    assert out["action"] == Action.SUPPRESS_CONTACT.value and out["requires_review"]
    assert rt.crm.records_of("deal") == [] and rt.crm.records_of("contact") == []
    assert rt.db.one("SELECT status FROM contacts WHERE id='c_hugo'")["status"] == "suppressed"


def test_compliance_suppression_ignores_the_kill_switch(rt):
    policy = rt.policies.load().model_copy(deep=True)
    policy.automation[Action.SUPPRESS_CONTACT] = "off"
    rt.policies.replace(policy)
    out = reply(rt, "c_lucia", OPTOUT_ES)
    assert out["action"] == Action.SUPPRESS_CONTACT.value and out["automated"]
    assert rt.db.one("SELECT status FROM contacts WHERE id='c_lucia'")["status"] == "suppressed"


def test_model_unsubscribe_intent_below_threshold_still_suppresses(rt):
    d = _decide(rt, "c_lucia", "texto que el regex no atrapa", _ai(Intent.UNSUBSCRIBE, 0.78, flags=[RiskFlag.UNSUBSCRIBE_REQUEST]))
    assert d.action == Action.SUPPRESS_CONTACT and d.automated and d.requires_review


def test_date_times_from_the_model_are_normalised():
    from growth_orchestrator.ai.interpreter import normalise
    interp = ReplyInterpretation(intent=Intent.OUT_OF_OFFICE, confidence=0.9, language="es", evidence=["x"],
                                 extracted=ExtractedFacts(return_date="2026-10-14T00:00:00"), risk_flags=[], summary="s")
    assert normalise(interp).extracted.return_date == "2026-10-14"
