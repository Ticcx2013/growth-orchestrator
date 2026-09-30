"""Transactional outbox: every external side effect is a row first, a call second.

Why: the decision and the intent to act are committed together; the call to the CRM can then fail,
time out, or be retried without ever producing two deals. The idempotency key is
`{event_id}:{action_type}`, and the mock CRM (like the production adapter) looks it up before creating.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Callable

from .db import Database, iso, utcnow
from .integrations.crm import CRMClient, PermanentError, RateLimited, UncertainOutcome
from .models import Action

MAX_ATTEMPTS = 4                     # applies to uncertain outcomes AND rate limits; then dead-letter
BACKOFF_SECONDS = [30, 120, 600]     # after attempt 1, 2, 3
IN_FLIGHT_GRACE_SECONDS = 600        # an in_flight row older than this is treated as an uncertain outcome


def idempotency_key(event_id: str, action: Action) -> str:
    return f"{event_id}:{action.value}"


class Outbox:
    def __init__(self, db: Database, crm: CRMClient, clock: Callable[[], datetime] = utcnow):
        self.db = db
        self.crm = crm
        self.clock = clock

    # -- enqueue ---------------------------------------------------------------------
    def enqueue(self, *, decision_id: int, event_id: str, action: Action, payload: dict[str, Any]) -> dict[str, Any]:
        key = idempotency_key(event_id, action)
        existing = self.db.one("SELECT * FROM actions WHERE idempotency_key = ?", (key,))
        if existing:
            self.db.audit(event_id, "action_enqueued", f"action already exists for key {key}; not duplicated", {"idempotency_key": key})
            return existing
        now = iso(self.clock())
        self.db.exec(
            "INSERT INTO actions(idempotency_key, decision_id, event_id, type, target_system, payload_json, status, attempts, next_attempt_at, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (key, decision_id, event_id, action.value, _target_system(action), json.dumps(payload, default=str), "pending", 0, now, now, now),
        )
        self.db.audit(event_id, "action_enqueued", f"{action.value} queued in outbox", {"idempotency_key": key, "payload": payload})
        return self.db.one("SELECT * FROM actions WHERE idempotency_key = ?", (key,))

    # -- dispatch --------------------------------------------------------------------
    def dispatch(self, key: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM actions WHERE idempotency_key = ?", (key,))
        if row is None:
            raise KeyError(key)
        if row["status"] in ("succeeded", "dead"):
            return row
        event_id = row["event_id"]
        action = Action(row["type"])
        payload = json.loads(row["payload_json"])
        attempt = row["attempts"] + 1
        now = self.clock()
        self._set(key, status="in_flight", attempts=attempt)

        # Reconcile first when the previous attempt had an uncertain outcome: ask the CRM whether the
        # write landed. Either way we then run the (idempotent) executor: writes that already exist are
        # returned, not duplicated; dependent writes that never happened are completed.
        if row["status"] == "uncertain":
            found = self.crm.find_by_idempotency_key(key)
            if found:
                self.db.audit(event_id, "action_reconciled",
                              f"previous attempt DID land in the CRM ({found['id']}); completing remaining writes idempotently, no second record",
                              {"idempotency_key": key, "external_ref": found["id"]})
            else:
                self.db.audit(event_id, "action_reconciled", "previous attempt did NOT land in the CRM; safe to re-send", {"idempotency_key": key})

        try:
            result = self._execute(action, payload, key)
        except RateLimited as e:
            if attempt >= MAX_ATTEMPTS:
                self._dead(key, event_id, f"still rate-limited after {attempt} attempts: {e}")
            else:
                delay = max(e.retry_after_s, _backoff(attempt))
                nxt = now + timedelta(seconds=delay)
                self._set(key, status="pending", next_attempt_at=iso(nxt), last_error=str(e))
                self.db.audit(event_id, "action_retry_scheduled", f"CRM rate-limited (429); retry #{attempt + 1} in {int(delay)}s",
                              {"idempotency_key": key, "next_attempt_at": iso(nxt)})
        except UncertainOutcome as e:
            if attempt >= MAX_ATTEMPTS:
                self._dead(key, event_id, f"uncertain after {attempt} attempts: {e}")
            else:
                nxt = now + timedelta(seconds=_backoff(attempt))
                self._set(key, status="uncertain", next_attempt_at=iso(nxt), last_error=str(e))
                self.db.audit(event_id, "action_uncertain",
                              f"{action.value}: {e}. Outcome unknown; will reconcile by idempotency key before retrying",
                              {"idempotency_key": key, "next_attempt_at": iso(nxt)})
        except PermanentError as e:
            self._dead(key, event_id, f"permanent error: {e}")
        except Exception as e:  # a bug in an executor must never strand a row in in_flight
            self._dead(key, event_id, f"unexpected error in executor: {type(e).__name__}: {e}")
        else:
            self._set(key, status="succeeded", external_ref=result.get("id"), last_error=None)
            self.db.audit(event_id, "action_dispatched", f"{action.value} succeeded -> {result.get('id')}",
                          {"idempotency_key": key, "external_ref": result.get("id"), "attempt": attempt})
            self._apply_local_effects(action, payload, event_id)
        return self.db.one("SELECT * FROM actions WHERE idempotency_key = ?", (key,))

    def process_due(self, now: datetime | None = None) -> list[dict[str, Any]]:
        """Worker loop tick: dispatch everything pending/uncertain whose time has come."""
        now = now or self.clock()
        # Rows left in_flight by a crash mid-dispatch: after a grace period, treat them as uncertain outcomes.
        stale_cutoff = iso(now - timedelta(seconds=IN_FLIGHT_GRACE_SECONDS))
        for r in self.db.all("SELECT idempotency_key, event_id FROM actions WHERE status = 'in_flight' AND updated_at <= ?", (stale_cutoff,)):
            self._set(r["idempotency_key"], status="uncertain", next_attempt_at=iso(now))
            self.db.audit(r["event_id"], "action_uncertain", "found in_flight past the grace period (worker crashed?); will reconcile", {"idempotency_key": r["idempotency_key"]})
        due = self.db.all(
            "SELECT idempotency_key FROM actions WHERE status IN ('pending','uncertain') AND (next_attempt_at IS NULL OR next_attempt_at <= ?) ORDER BY created_at",
            (iso(now),),
        )
        return [self.dispatch(r["idempotency_key"]) for r in due]

    # -- internals -------------------------------------------------------------------
    def _execute(self, action: Action, p: dict[str, Any], key: str) -> dict[str, Any]:
        if action == Action.HANDOFF_TO_AE:
            deal = self.crm.create_deal(idempotency_key=key, account_id=p["account_id"], contact_id=p["contact_id"],
                                        owner_ae_id=p.get("owner_ae_id"), notes=p.get("notes", ""))
            # Second write under a derived key: still idempotent, still reconcilable.
            self.crm.create_task(idempotency_key=f"{key}:task", owner_id=p.get("owner_ae_id"),
                                 subject="SDR handoff: prospect replied with interest",
                                 body=f"{p.get('summary','')} Proposed: {p.get('proposed_meeting') or 'n/a'}", related_to=deal["id"])
            return deal
        if action == Action.CREATE_REFERRAL_CONTACT:
            return self.crm.create_contact(idempotency_key=key, account_id=p["account_id"], email=p["email"], name=p.get("name"), source="referral_reply")
        if action == Action.SUPPRESS_CONTACT:
            return self.crm.add_to_suppression_list(idempotency_key=key, email=p["email"], reason=p.get("reason", "opt_out"))
        if action == Action.NURTURE_LONG_TERM:
            return self.crm.update_contact_lifecycle(idempotency_key=key, contact_id=p["contact_id"], lifecycle="nurture")
        if action == Action.ENROLL_IN_SEQUENCE:
            return self.crm.enroll_in_sequence(idempotency_key=key, contact_id=p["contact_id"], sequence=p["sequence"])
        if action == Action.ENRICH_CONTACT:
            return self.crm.enrich_contact(idempotency_key=key, contact_id=p["contact_id"])
        if action == Action.NOTIFY_CSM:
            return self.crm.create_task(idempotency_key=key, owner_id=p.get("csm_id"), subject="Prospect replied but account is not ours to prospect",
                                        body="Outreach suppressed by the orchestrator. Please follow up.", related_to=p["account_id"])
        if action == Action.WAIT_UNTIL:
            return {"id": f"local_wait_{p['contact_id']}"}  # local state only; no external call
        if action == Action.ESCALATE_TO_HUMAN:
            return {"id": "review_queue"}  # the queue row is created by the orchestrator
        raise PermanentError(f"no executor for {action.value}")

    def _apply_local_effects(self, action: Action, p: dict[str, Any], event_id: str) -> None:
        now = iso(self.clock())
        if action == Action.HANDOFF_TO_AE:
            self.db.exec("UPDATE contacts SET status='handed_off', sequence_status='paused', updated_at=? WHERE id=?", (now, p["contact_id"]))
            self.db.exec("UPDATE accounts SET has_open_opportunity=1, state_version=state_version+1, state_updated_at=? WHERE id=?", (now, p["account_id"]))
        elif action == Action.SUPPRESS_CONTACT:
            self.db.exec("UPDATE contacts SET status='suppressed', sequence_status='completed', updated_at=? WHERE id=?", (now, p["contact_id"]))
            self.db.exec("INSERT OR IGNORE INTO suppressions(scope, key, reason, created_at) VALUES ('contact_email', ?, ?, ?)",
                         (p["email"].lower(), p.get("reason", "opt_out"), now))
        elif action == Action.WAIT_UNTIL:
            self.db.exec("UPDATE contacts SET status='waiting', sequence_status='paused', wait_until=?, updated_at=? WHERE id=?",
                         (p["wait_until"], now, p["contact_id"]))
        elif action == Action.NURTURE_LONG_TERM:
            self.db.exec("UPDATE contacts SET status='nurture', sequence_status='completed', updated_at=? WHERE id=?", (now, p["contact_id"]))
        elif action == Action.ENROLL_IN_SEQUENCE:
            self.db.exec("UPDATE contacts SET sequence_status='enrolled', last_outreach_at=?, updated_at=? WHERE id=?", (now, now, p["contact_id"]))
        elif action == Action.ENRICH_CONTACT:
            self.db.exec("UPDATE contacts SET enriched=1, updated_at=? WHERE id=?", (now, p["contact_id"]))
        elif action == Action.NOTIFY_CSM:
            self.db.exec("UPDATE contacts SET sequence_status='completed', updated_at=? WHERE id=?", (now, p["contact_id"]))
            self.db.exec("INSERT OR IGNORE INTO suppressions(scope, key, reason, created_at) VALUES ('account', ?, 'customer_or_active_opportunity', ?)",
                         (p["account_id"], now))

    def _set(self, key: str, **fields: Any) -> None:
        fields["updated_at"] = iso(self.clock())
        cols = ", ".join(f"{k} = ?" for k in fields)
        self.db.exec(f"UPDATE actions SET {cols} WHERE idempotency_key = ?", (*fields.values(), key))

    def _dead(self, key: str, event_id: str, error: str) -> None:
        self._set(key, status="dead", last_error=error)
        self.db.audit(event_id, "action_dead", f"moved to dead-letter: {error}", {"idempotency_key": key})
        row = self.db.one("SELECT decision_id, type FROM actions WHERE idempotency_key = ?", (key,))
        self.db.exec(
            "INSERT INTO review_queue(decision_id, event_id, proposed_action, reason, status, created_at) VALUES (?,?,?,?,?,?)",
            (row["decision_id"], event_id, row["type"], f"dead-letter: {error}", "open", iso(self.clock())),
        )


def _backoff(attempt: int) -> int:
    idx = min(attempt - 1, len(BACKOFF_SECONDS) - 1)
    return BACKOFF_SECONDS[idx]


def _target_system(action: Action) -> str:
    return {
        Action.HANDOFF_TO_AE: "crm", Action.CREATE_REFERRAL_CONTACT: "crm", Action.SUPPRESS_CONTACT: "crm",
        Action.NURTURE_LONG_TERM: "crm", Action.NOTIFY_CSM: "crm", Action.ENROLL_IN_SEQUENCE: "outreach",
        Action.ENRICH_CONTACT: "enrichment", Action.WAIT_UNTIL: "local", Action.ESCALATE_TO_HUMAN: "local", Action.NO_ACTION: "local",
    }[action]
