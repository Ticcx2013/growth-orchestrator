"""The pipeline: event -> state -> decision -> AI/rules -> action -> audit.

`Orchestrator.handle(event)` is what the webhook calls after acknowledging. Every stage writes to the
audit log under the event id, so the trace for any event can be reconstructed end to end.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Any, Callable

from . import compliance, decision, eligibility
from .ai.interpreter import ReplyInterpreter
from .db import Database, iso, parse_dt, utcnow
from .integrations.crm import CRMClient, RateLimited
from .models import IRREVERSIBLE_ACTIONS, Action, AIResult, Decision, EventType, InboundEvent
from .outbox import Outbox
from .policy import PolicyStore


class IngestResult(dict):
    """{'status': 'accepted' | 'duplicate', 'event_id': ...}"""


class Orchestrator:
    def __init__(self, db: Database, crm: CRMClient, interpreter: ReplyInterpreter, policies: PolicyStore,
                 clock: Callable[[], datetime] = utcnow, lock: threading.RLock | None = None):
        self.db = db
        self.crm = crm
        self.interpreter = interpreter
        self.policies = policies
        self.clock = clock
        # One writer at a time for state changes. The lock is NOT held during the model call, which can take
        # seconds: the pipeline reads state, releases, asks the model, then re-reads state before deciding.
        self.lock = lock or threading.RLock()
        self.outbox = Outbox(db, crm, clock)

    # ------------------------------------------------------------------------------
    # 1. Ingest (idempotent)
    # ------------------------------------------------------------------------------
    def ingest(self, event: InboundEvent) -> IngestResult:
        with self.lock:
            return self._ingest(event)

    def _ingest(self, event: InboundEvent) -> IngestResult:
        now = iso(self.clock())
        try:
            with self.db.tx():
                self.db.exec(
                    "INSERT INTO events(event_id, type, occurred_at, received_at, payload_json, status) VALUES (?,?,?,?,?,'received')",
                    (event.event_id, event.type.value, iso(event.occurred_at), now, json.dumps(event.payload, default=str)),
                )
        except Exception as e:  # sqlite3.IntegrityError on the primary key
            if "UNIQUE" not in str(e) and "PRIMARY KEY" not in str(e):
                raise
            self.db.exec("UPDATE events SET duplicate_count = duplicate_count + 1 WHERE event_id = ?", (event.event_id,))
            self.db.audit(event.event_id, "duplicate", "event_id already seen; ignored (idempotency)", {"received_at": now})
            return IngestResult(status="duplicate", event_id=event.event_id)
        self.db.audit(event.event_id, "received", f"{event.type.value} accepted", {"occurred_at": iso(event.occurred_at), "payload": event.payload})
        return IngestResult(status="accepted", event_id=event.event_id)

    # ------------------------------------------------------------------------------
    # 2..6 Process
    # ------------------------------------------------------------------------------
    def process(self, event_id: str) -> dict[str, Any]:
        with self.lock:
            row = self.db.one("SELECT * FROM events WHERE event_id = ?", (event_id,))
            if row is None:
                raise KeyError(event_id)
            if row["status"] not in ("received", "failed"):
                return {"event_id": event_id, "status": row["status"], "note": "already processed"}
            event = InboundEvent(event_id=row["event_id"], type=EventType(row["type"]), occurred_at=parse_dt(row["occurred_at"]),
                                 payload=json.loads(row["payload_json"]))
            self.db.exec("UPDATE events SET status='processing' WHERE event_id=?", (event_id,))
        try:
            handler = {
                EventType.PROSPECT_IDENTIFIED: self._on_prospect_identified,
                EventType.REPLY_RECEIVED: self._on_reply,
                EventType.CRM_ACCOUNT_UPDATED: self._on_account_updated,
                EventType.CONTACT_UNSUBSCRIBED: self._on_unsubscribed,
            }[event.type]
            result = handler(event)  # each handler takes the lock for its state-changing sections
            with self.lock:
                status = result.get("status", "processed")
                self.db.exec("UPDATE events SET status=?, processed_at=? WHERE event_id=?", (status, iso(self.clock()), event_id))
                self.db.audit(event_id, "completed", f"event {status}", {"result": {k: v for k, v in result.items() if k != 'trace'}})
            return result
        except Exception as e:
            with self.lock:
                self.db.exec("UPDATE events SET status='failed', error=? WHERE event_id=?", (str(e), event_id))
                self.db.audit(event_id, "failed", f"unhandled error: {e}")
            raise

    def handle(self, event: InboundEvent) -> dict[str, Any]:
        ing = self.ingest(event)
        if ing["status"] == "duplicate":
            return {"event_id": event.event_id, "status": "duplicate", "trace": self.db.trace(event.event_id)}
        result = self.process(event.event_id)
        result["trace"] = self.db.trace(event.event_id)
        return result

    # ------------------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------------------
    def _load_quiet(self, event: InboundEvent) -> tuple[dict | None, dict | None]:
        contact = account = None
        cid = event.payload.get("contact_id")
        email = event.payload.get("contact_email")
        if cid:
            contact = self.db.one("SELECT * FROM contacts WHERE id = ?", (cid,))
        elif email:
            contact = self.db.one("SELECT * FROM contacts WHERE lower(email) = lower(?)", (email,))
        aid = event.payload.get("account_id") or (contact and contact["account_id"])
        if aid:
            account = self.db.one("SELECT * FROM accounts WHERE id = ?", (aid,))
        return account, contact

    def _load(self, event: InboundEvent) -> tuple[dict | None, dict | None]:
        contact = account = None
        cid = event.payload.get("contact_id")
        email = event.payload.get("contact_email")
        if cid:
            contact = self.db.one("SELECT * FROM contacts WHERE id = ?", (cid,))
        elif email:
            contact = self.db.one("SELECT * FROM contacts WHERE lower(email) = lower(?)", (email,))
        aid = event.payload.get("account_id") or (contact and contact["account_id"])
        if aid:
            account = self.db.one("SELECT * FROM accounts WHERE id = ?", (aid,))
        self.db.audit(event.event_id, "state_loaded", "account/contact state read",
                      {"account": _pick(account, "id", "name", "is_customer", "has_open_opportunity", "owner_ae_id", "state_version"),
                       "contact": _pick(contact, "id", "email", "status", "sequence_status", "last_outreach_at")})
        return account, contact

    def _on_prospect_identified(self, event: InboundEvent) -> dict[str, Any]:
        with self.lock:
            return self._on_prospect_identified_locked(event)

    def _on_prospect_identified_locked(self, event: InboundEvent) -> dict[str, Any]:
        policy = self.policies.load()
        account, contact = self._load(event)
        if account is None or contact is None:
            self.db.audit(event.event_id, "decision", "unknown account/contact: nothing to do")
            return {"status": "processed", "action": Action.NO_ACTION.value}
        elig = eligibility.evaluate(self.db, account, contact, policy, self.clock(), purpose="outreach")
        self.db.audit(event.event_id, "eligibility", "eligible" if elig.eligible else f"blocked: {', '.join(elig.blockers)}", elig.as_dict())
        d = decision.decide_prospect_identified(account, contact, elig, policy)
        return self._commit(event, account, contact, d, ai=None, policy_version=policy.version)

    def _on_reply(self, event: InboundEvent) -> dict[str, Any]:
        text = (event.payload.get("text") or "").strip()

        # Phase 1 (locked): read state, run the rules, decide whether the model is needed at all.
        with self.lock:
            policy = self.policies.load()
            account, contact = self._load(event)
            if account is None or contact is None:
                d = Decision(action=Action.ESCALATE_TO_HUMAN, automated=True, requires_review=True,
                             reason="reply from an unknown contact/account: a human maps it", trace=[])
                return self._commit(event, account, contact, d, ai=None, policy_version=policy.version)

            # Out-of-order guard: a reply that predates the last state change is still a reply, but we
            # evaluate it against CURRENT state (not the state at send time). That is the safe direction.
            state_at = parse_dt(account["state_updated_at"])
            if state_at and event.occurred_at < state_at:
                self.db.audit(event.event_id, "ordering", "reply occurred before the latest account state change; evaluating against current state",
                              {"occurred_at": iso(event.occurred_at), "state_updated_at": account["state_updated_at"]})

            elig = eligibility.evaluate(self.db, account, contact, policy, self.clock(), purpose="reply")
            self.db.audit(event.event_id, "eligibility", "eligible" if elig.eligible else f"blocked: {', '.join(elig.blockers)}", elig.as_dict())

            comp = compliance.check_reply(text)
            self.db.audit(event.event_id, "compliance",
                          ("OPT-OUT detected by rule" if comp.opt_out else "no opt-out") + ("; injection heuristics matched" if comp.injection_suspected else ""),
                          comp.as_dict())
            needs_ai = not elig.blockers or comp.opt_out  # blocked accounts are decided by rules; the model would add nothing
            context = {"account_name": account["name"], "country": account.get("country"), "employee_count": account.get("employee_count"),
                       "contact_name": contact.get("name"), "contact_email": contact["email"]}

        # Phase 2 (NOT locked): the model call. Other events keep flowing while we wait for it.
        ai: AIResult | None = None
        if needs_ai:
            ai = self.interpreter.interpret(text, event.occurred_at, context)

        # Phase 3 (locked): the state may have moved while the model was thinking. Re-read it and decide on current facts.
        with self.lock:
            return self._decide_and_commit_reply(event, text, elig, comp, ai, policy)

    def _decide_and_commit_reply(self, event: InboundEvent, text: str, elig, comp, ai: AIResult | None, policy) -> dict[str, Any]:
        account, contact = self._load_quiet(event)
        fresh_elig = eligibility.evaluate(self.db, account, contact, policy, self.clock(), purpose="reply")
        if fresh_elig.blockers != elig.blockers:
            self.db.audit(event.event_id, "state_loaded", "state changed while the model was reading; re-evaluated on current state",
                          {"before": elig.blockers, "after": fresh_elig.blockers})
            elig = fresh_elig
        if ai is not None:
            ai.ai_call_id = self._record_ai_call(event.event_id, text, ai)
            self.db.audit(event.event_id, "ai_interpretation",
                          (f"intent={ai.interpretation.intent.value} confidence={ai.interpretation.confidence:.2f} flags={[f.value for f in ai.interpretation.risk_flags]}"
                           if ai.interpretation else "no interpretation") + f" [{ai.mode}]",
                          {"valid": ai.valid, "errors": ai.validation_errors, "attempts": ai.attempts, "model": ai.model,
                           "prompt_version": ai.prompt_version, "interpretation": ai.interpretation.model_dump(mode="json") if ai.interpretation else None,
                           "tokens": {"in": ai.input_tokens, "out": ai.output_tokens}, "latency_ms": ai.latency_ms})
            self.db.audit(event.event_id, "ai_validation", "passed" if ai.valid else f"FAILED: {'; '.join(ai.validation_errors)}",
                          {"valid": ai.valid, "errors": ai.validation_errors})
        else:
            self.db.audit(event.event_id, "ai_interpretation", "skipped: rules already decided (state blocker)", {"blockers": elig.blockers})

        d = decision.decide_reply(account=account, contact=contact, elig=elig, compliance=comp, ai=ai, policy=policy, reply_at=event.occurred_at)

        # Freshness: before an irreversible action, re-read the source of truth and re-decide if it moved.
        if d.action in IRREVERSIBLE_ACTIONS and d.automated and policy.ai.freshness_check_before_irreversible:
            fresh = self._freshness_check(event, account)
            if fresh is not None:
                account = fresh
                elig = eligibility.evaluate(self.db, account, contact, policy, self.clock(), purpose="reply")
                d = decision.decide_reply(account=account, contact=contact, elig=elig, compliance=comp, ai=ai, policy=policy, reply_at=event.occurred_at)
                d.reason = "[re-decided after freshness check] " + d.reason

        return self._commit(event, account, contact, d, ai=ai, policy_version=policy.version)

    def _on_account_updated(self, event: InboundEvent) -> dict[str, Any]:
        with self.lock:
            return self._on_account_updated_locked(event)

    def _on_account_updated_locked(self, event: InboundEvent) -> dict[str, Any]:
        p = event.payload
        account = self.db.one("SELECT * FROM accounts WHERE id = ?", (p.get("account_id"),))
        if account is None:
            self.db.audit(event.event_id, "state_loaded", "unknown account; ignoring")
            return {"status": "processed", "action": Action.NO_ACTION.value}
        current = parse_dt(account["state_updated_at"])
        if current and event.occurred_at <= current:
            self.db.audit(event.event_id, "stale_event",
                          f"event occurred at {iso(event.occurred_at)} but state is already from {account['state_updated_at']}; ignored (out-of-order)",
                          {"occurred_at": iso(event.occurred_at), "state_updated_at": account["state_updated_at"], "state_version": account["state_version"]})
            return {"status": "ignored_stale", "action": Action.NO_ACTION.value}
        fields = {k: p[k] for k in ("is_customer", "has_open_opportunity", "owner_ae_id", "csm_id", "employee_count", "country") if k in p}
        if fields:
            cols = ", ".join(f"{k} = ?" for k in fields)
            self.db.exec(f"UPDATE accounts SET {cols}, state_version = state_version + 1, state_updated_at = ? WHERE id = ?",
                         (*fields.values(), iso(event.occurred_at), account["id"]))
        self.db.audit(event.event_id, "state_updated", f"account state advanced to version {account['state_version'] + 1}", {"changes": fields})
        if hasattr(self.crm, "sync_account"):
            updated = self.db.one("SELECT * FROM accounts WHERE id = ?", (account["id"],))
            self.crm.sync_account(updated)  # in the demo the CRM mock mirrors the truth the event carried

        if fields.get("is_customer") or fields.get("has_open_opportunity"):
            n = self.db.exec("UPDATE contacts SET sequence_status='paused', updated_at=? WHERE account_id=? AND sequence_status='enrolled'",
                             (iso(self.clock()), account["id"])).rowcount
            self.db.audit(event.event_id, "decision", f"account became customer/has opportunity: paused {n} active sequence(s)", {"paused": n})
        return {"status": "processed", "action": Action.NO_ACTION.value, "changes": fields}

    def _on_unsubscribed(self, event: InboundEvent) -> dict[str, Any]:
        with self.lock:
            return self._on_unsubscribed_locked(event)

    def _on_unsubscribed_locked(self, event: InboundEvent) -> dict[str, Any]:
        policy = self.policies.load()
        account, contact = self._load(event)
        if contact is None:
            return {"status": "processed", "action": Action.NO_ACTION.value}
        d = decision.decide_unsubscribed(contact, policy)
        return self._commit(event, account, contact, d, ai=None, policy_version=policy.version)

    # ------------------------------------------------------------------------------
    # Commit decision -> outbox -> dispatch -> review queue
    # ------------------------------------------------------------------------------
    def _commit(self, event: InboundEvent, account: dict | None, contact: dict | None, d: Decision, ai: AIResult | None, policy_version: int) -> dict[str, Any]:
        now = iso(self.clock())
        cur = self.db.exec(
            "INSERT INTO decisions(event_id, account_id, contact_id, action, automated, requires_review, reason, trace_json, payload_json, ai_call_id, policy_version, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (event.event_id, account and account["id"], contact and contact["id"], d.action.value, int(d.automated), int(d.requires_review),
             d.reason, json.dumps(d.trace, default=str), json.dumps(d.payload, default=str), ai.ai_call_id if ai else None, policy_version, now),
        )
        decision_id = cur.lastrowid
        self.db.audit(event.event_id, "decision", f"{d.action.value} ({'automated' if d.automated else 'not automated'}): {d.reason}",
                      {"decision_id": decision_id, "action": d.action.value, "automated": d.automated, "requires_review": d.requires_review,
                       "proposed_action": d.proposed_action.value if d.proposed_action else None, "policy_version": policy_version})

        action_row = None
        if d.action not in (Action.NO_ACTION, Action.ESCALATE_TO_HUMAN) and d.automated:
            action_row = self.outbox.enqueue(decision_id=decision_id, event_id=event.event_id, action=d.action, payload=d.payload)
            action_row = self.outbox.dispatch(action_row["idempotency_key"])

        if d.requires_review:
            # What the reviewer can approve: the explicit proposal, or the (not automated) action itself.
            proposed = d.proposed_action or (None if d.automated else d.action)
            self.db.exec(
                "INSERT INTO review_queue(decision_id, event_id, proposed_action, reason, status, created_at) VALUES (?,?,?,?,?,?)",
                (decision_id, event.event_id, proposed.value if proposed else None, d.reason, "open", now),
            )
            self.db.audit(event.event_id, "review_queued", "queued for human review", {"decision_id": decision_id,
                          "proposed_action": d.proposed_action.value if d.proposed_action else None})

        return {"status": "processed", "decision_id": decision_id, "action": d.action.value, "automated": d.automated,
                "requires_review": d.requires_review, "reason": d.reason, "policy_version": policy_version,
                "action_status": action_row["status"] if action_row else None,
                "external_ref": action_row["external_ref"] if action_row else None}

    def _freshness_check(self, event: InboundEvent, account: dict) -> dict | None:
        try:
            remote = self.crm.get_account(account["id"])
        except RateLimited as e:
            self.db.audit(event.event_id, "freshness_check", f"CRM rate-limited during freshness check ({e}); proceeding with local state", {})
            return None
        if remote is None:
            self.db.audit(event.event_id, "freshness_check", "account not found in CRM; proceeding with local state", {})
            return None
        diffs = {k: {"local": account.get(k), "crm": remote.get(k)} for k in ("is_customer", "has_open_opportunity", "owner_ae_id")
                 if (account.get(k) or 0) != (remote.get(k) or 0) and not (account.get(k) is None and remote.get(k) is None)}
        if not diffs:
            self.db.audit(event.event_id, "freshness_check", "CRM state matches local state; safe to act", {"checked": ["is_customer", "has_open_opportunity", "owner_ae_id"]})
            return None
        now = iso(self.clock())
        self.db.exec("UPDATE accounts SET is_customer=?, has_open_opportunity=?, owner_ae_id=?, state_version=state_version+1, state_updated_at=? WHERE id=?",
                     (int(bool(remote.get("is_customer"))), int(bool(remote.get("has_open_opportunity"))), remote.get("owner_ae_id"), now, account["id"]))
        self.db.audit(event.event_id, "freshness_check", "CRM state DIFFERS from local state; local updated and decision re-evaluated", {"diffs": diffs})
        return self.db.one("SELECT * FROM accounts WHERE id = ?", (account["id"],))

    def _record_ai_call(self, event_id: str, text: str, ai: AIResult) -> int:
        cur = self.db.exec(
            "INSERT INTO ai_calls(event_id, mode, model, prompt_version, attempt, input_text, raw_output, parsed_json, valid, validation_errors_json, latency_ms, input_tokens, output_tokens, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, ai.mode, ai.model, ai.prompt_version, ai.attempts, text, ai.raw_output,
             ai.interpretation.model_dump_json() if ai.interpretation else None, int(ai.valid), json.dumps(ai.validation_errors),
             ai.latency_ms, ai.input_tokens, ai.output_tokens, iso(self.clock())),
        )
        return cur.lastrowid


def _pick(row: dict | None, *keys: str) -> dict | None:
    return {k: row.get(k) for k in keys} if row else None
