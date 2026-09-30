"""Eligibility rules. Deterministic, testable, and deliberately NOT AI.

Whether we may talk to someone is a question of state and policy, not of language understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .db import Database, parse_dt
from .policy import Policy


@dataclass
class EligibilityResult:
    eligible: bool
    blockers: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"eligible": self.eligible, "blockers": self.blockers, "trace": self.trace}


def _rule(trace: list, name: str, passed: bool, detail: str) -> None:
    trace.append({"rule": name, "passed": passed, "detail": detail})


def evaluate(db: Database, account: dict | None, contact: dict | None, policy: Policy, now: datetime, purpose: str = "outreach") -> EligibilityResult:
    """purpose: 'outreach' (may we start/continue contacting) or 'reply' (may we act on a reply)."""
    trace: list[dict[str, Any]] = []
    blockers: list[str] = []

    if account is None:
        _rule(trace, "account_exists", False, "unknown account")
        return EligibilityResult(False, ["unknown_account"], trace)
    _rule(trace, "account_exists", True, account["name"])

    # 1. Existing customers are never prospected. If a customer replies, Customer Success owns it.
    if account["is_customer"]:
        blockers.append("already_customer")
        _rule(trace, "not_customer", False, "account is an existing customer")
    else:
        _rule(trace, "not_customer", True, "prospect")

    # 2. Active opportunity with an AE: the AE owns the conversation, the machine stays out.
    if account["has_open_opportunity"]:
        blockers.append("active_opportunity")
        _rule(trace, "no_active_opportunity", False, f"open opportunity owned by {account.get('owner_ae_id') or 'unassigned'}")
    else:
        _rule(trace, "no_active_opportunity", True, "no open opportunity")

    # 3. Suppression lists (account, domain, contact).
    sup_keys = [("account", account["id"])]
    if account.get("domain"):
        sup_keys.append(("domain", account["domain"]))
    if contact:
        sup_keys.append(("contact", contact["id"]))
        sup_keys.append(("contact_email", contact["email"].lower()))
    hits = []
    for scope, key in sup_keys:
        row = db.one("SELECT reason FROM suppressions WHERE scope = ? AND key = ?", (scope, key))
        if row:
            hits.append(f"{scope}:{key} ({row['reason']})")
    if hits:
        blockers.append("suppressed")
        _rule(trace, "not_suppressed", False, "; ".join(hits))
    else:
        _rule(trace, "not_suppressed", True, "no suppression rule matches")

    if contact:
        # 4. Contact-level status.
        if contact["status"] == "suppressed":
            blockers.append("contact_opted_out")
            _rule(trace, "contact_not_opted_out", False, "contact status is suppressed")
        else:
            _rule(trace, "contact_not_opted_out", True, f"status={contact['status']}")

        # 5. Cooldown (only matters when starting new outreach; a reply is by definition after outreach).
        if purpose == "outreach":
            last = parse_dt(contact.get("last_outreach_at"))
            if last and now - last < timedelta(days=policy.eligibility.cooldown_days):
                blockers.append("cooldown")
                _rule(trace, "cooldown", False, f"last outreach {(now - last).days}d ago < {policy.eligibility.cooldown_days}d")
            else:
                _rule(trace, "cooldown", True, "outside cooldown window" if last else "never contacted")

            # 6. Cap on concurrent active contacts per account.
            active = db.one(
                "SELECT COUNT(*) AS n FROM contacts WHERE account_id = ? AND sequence_status = 'enrolled' AND id != ?",
                (account["id"], contact["id"]),
            )["n"]
            if active >= policy.eligibility.max_active_contacts_per_account:
                blockers.append("account_contact_cap")
                _rule(trace, "contact_cap", False, f"{active} contacts already enrolled (cap {policy.eligibility.max_active_contacts_per_account})")
            else:
                _rule(trace, "contact_cap", True, f"{active} enrolled")

        # 7. Minimum data.
        if not contact.get("email"):
            blockers.append("missing_email")
            _rule(trace, "has_email", False, "contact has no email")
        else:
            _rule(trace, "has_email", True, contact["email"])

    # 8. ICP fit (soft for replies: a reply from outside ICP is still handled, but flagged).
    icp = policy.eligibility.icp
    in_icp = True
    reasons = []
    if account.get("employee_count") is not None and account["employee_count"] < icp.min_employees:
        in_icp = False
        reasons.append(f"{account['employee_count']} employees < {icp.min_employees}")
    if account.get("country") and account["country"] not in icp.countries:
        in_icp = False
        reasons.append(f"country {account['country']} not in {icp.countries}")
    if not in_icp:
        if purpose == "outreach":
            blockers.append("out_of_icp")
        _rule(trace, "icp_fit", False, "; ".join(reasons))
    else:
        _rule(trace, "icp_fit", True, "within ICP")

    return EligibilityResult(eligible=not blockers, blockers=blockers, trace=trace)


def in_icp(account: dict, policy: Policy) -> bool:
    icp = policy.eligibility.icp
    if account.get("employee_count") is not None and account["employee_count"] < icp.min_employees:
        return False
    if account.get("country") and account["country"] not in icp.countries:
        return False
    return True
