"""CRM / outreach / enrichment integration boundary.

`CRMClient` is the interface the orchestrator talks to. `MockCRM` implements it in memory with
fault injection so we can rehearse real failure modes (timeouts after commit, rate limits).
`HubSpotCRM` is a deliberately unimplemented skeleton showing where production code plugs in.

Every write takes an `idempotency_key`. A real CRM does not offer that natively, so in production
the adapter stores the key in a custom property and looks it up before creating (same trick as here).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


class IntegrationError(Exception):
    """Base class."""


class RateLimited(IntegrationError):
    def __init__(self, retry_after_s: float = 30.0):
        super().__init__(f"rate limited, retry after {retry_after_s}s")
        self.retry_after_s = retry_after_s


class UncertainOutcome(IntegrationError):
    """The request may or may not have been applied (timeout after send, connection reset)."""


class PermanentError(IntegrationError):
    """Retrying will not help (validation error, 4xx other than 429)."""


class CRMClient(Protocol):
    def get_account(self, account_id: str) -> dict[str, Any] | None: ...
    def find_by_idempotency_key(self, key: str) -> dict[str, Any] | None: ...
    def create_deal(self, *, idempotency_key: str, account_id: str, contact_id: str, owner_ae_id: str | None, notes: str) -> dict[str, Any]: ...
    def create_task(self, *, idempotency_key: str, owner_id: str | None, subject: str, body: str, related_to: str) -> dict[str, Any]: ...
    def create_contact(self, *, idempotency_key: str, account_id: str, email: str, name: str | None, source: str) -> dict[str, Any]: ...
    def add_to_suppression_list(self, *, idempotency_key: str, email: str, reason: str) -> dict[str, Any]: ...
    def update_contact_lifecycle(self, *, idempotency_key: str, contact_id: str, lifecycle: str) -> dict[str, Any]: ...
    def enroll_in_sequence(self, *, idempotency_key: str, contact_id: str, sequence: str) -> dict[str, Any]: ...
    def enrich_contact(self, *, idempotency_key: str, contact_id: str) -> dict[str, Any]: ...


@dataclass
class FaultInjector:
    """One-shot faults keyed by operation name. `arm("create_deal", "timeout_after_commit")`."""

    armed: dict[str, list[str]] = field(default_factory=dict)
    fired: list[dict[str, str]] = field(default_factory=list)

    def arm(self, operation: str, fault: str) -> None:
        self.armed.setdefault(operation, []).append(fault)

    def clear(self) -> None:
        self.armed.clear()
        self.fired.clear()

    def pop(self, operation: str) -> str | None:
        queue = self.armed.get(operation)
        if not queue:
            return None
        fault = queue.pop(0)
        self.fired.append({"operation": operation, "fault": fault})
        return fault


class MockCRM:
    """In-memory CRM with idempotency-key lookups and fault injection."""

    def __init__(self) -> None:
        self.accounts: dict[str, dict[str, Any]] = {}
        self.records: dict[str, dict[str, Any]] = {}       # id -> record
        self.by_key: dict[str, str] = {}                    # idempotency_key -> id
        self.calls: list[dict[str, Any]] = []
        self.faults = FaultInjector()

    # -- helpers ---------------------------------------------------------------------
    def reset(self) -> None:
        self.accounts.clear()
        self.records.clear()
        self.by_key.clear()
        self.calls.clear()
        self.faults.clear()

    def sync_account(self, account: dict[str, Any]) -> None:
        """The CRM is the source of truth for account facts; the demo seeds it from the same data."""
        self.accounts[account["id"]] = dict(account)

    def records_of(self, kind: str) -> list[dict[str, Any]]:
        return [r for r in self.records.values() if r["kind"] == kind]

    def _write(self, operation: str, kind: str, idempotency_key: str, data: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"operation": operation, "idempotency_key": idempotency_key})
        fault = self.faults.pop(operation)
        if fault == "rate_limit":
            raise RateLimited(retry_after_s=30)
        if fault == "timeout_before_commit":
            raise UncertainOutcome(f"{operation}: connection timed out before the request was received")
        if fault == "permanent_error":
            raise PermanentError(f"{operation}: 400 invalid payload")

        # Real idempotency: the same key returns the same record, never a second one.
        existing_id = self.by_key.get(idempotency_key)
        if existing_id:
            return dict(self.records[existing_id])

        rec_id = f"{kind}_{uuid.uuid4().hex[:8]}"
        record = {"id": rec_id, "kind": kind, "idempotency_key": idempotency_key, **data}
        self.records[rec_id] = record
        self.by_key[idempotency_key] = rec_id

        if fault == "timeout_after_commit":
            # The write landed, but the client never saw the response. This is the scary one.
            raise UncertainOutcome(f"{operation}: read timeout after the request was sent")
        return dict(record)

    # -- CRMClient -------------------------------------------------------------------
    def get_account(self, account_id: str) -> dict[str, Any] | None:
        self.calls.append({"operation": "get_account", "account_id": account_id})
        fault = self.faults.pop("get_account")
        if fault == "rate_limit":
            raise RateLimited(retry_after_s=10)
        acc = self.accounts.get(account_id)
        return dict(acc) if acc else None

    def find_by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        self.calls.append({"operation": "find_by_idempotency_key", "idempotency_key": key})
        rec_id = self.by_key.get(key)
        return dict(self.records[rec_id]) if rec_id else None

    def create_deal(self, *, idempotency_key, account_id, contact_id, owner_ae_id, notes):
        return self._write("create_deal", "deal", idempotency_key,
                           {"account_id": account_id, "contact_id": contact_id, "owner_ae_id": owner_ae_id, "notes": notes, "stage": "sdr_qualified"})

    def create_task(self, *, idempotency_key, owner_id, subject, body, related_to):
        return self._write("create_task", "task", idempotency_key,
                           {"owner_id": owner_id, "subject": subject, "body": body, "related_to": related_to})

    def create_contact(self, *, idempotency_key, account_id, email, name, source):
        return self._write("create_contact", "contact", idempotency_key,
                           {"account_id": account_id, "email": email, "name": name, "source": source})

    def add_to_suppression_list(self, *, idempotency_key, email, reason):
        return self._write("add_to_suppression_list", "suppression", idempotency_key, {"email": email, "reason": reason})

    def update_contact_lifecycle(self, *, idempotency_key, contact_id, lifecycle):
        return self._write("update_contact_lifecycle", "lifecycle_update", idempotency_key, {"contact_id": contact_id, "lifecycle": lifecycle})

    def enroll_in_sequence(self, *, idempotency_key, contact_id, sequence):
        return self._write("enroll_in_sequence", "sequence_enrollment", idempotency_key, {"contact_id": contact_id, "sequence": sequence})

    def enrich_contact(self, *, idempotency_key, contact_id):
        return self._write("enrich_contact", "enrichment", idempotency_key, {"contact_id": contact_id, "provider": "mock-clay", "title": "Head of Finance", "employee_count": 320})


class HubSpotCRM:
    """Skeleton of the production adapter. Same interface, real HTTP.

    Not implemented on purpose (see DECISIONS.md). The shape is here so the swap is a config change:
    - idempotency via a custom property `go_idempotency_key` + search before create
    - 429 -> RateLimited(retry_after from header); 5xx/timeouts -> UncertainOutcome; 4xx -> PermanentError
    """

    def __init__(self, access_token: str):
        self._token = access_token

    def __getattr__(self, name: str):
        raise NotImplementedError(f"HubSpotCRM.{name} is a production adapter stub")
