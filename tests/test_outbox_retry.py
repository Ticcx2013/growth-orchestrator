"""Failure and retry: uncertain outcomes are reconciled, rate limits back off, permanent errors go to the DLQ."""

from growth_orchestrator.models import Action

from .conftest import INTERESTED_ES, INTERESTED_PT, reply


def _action(rt, event_id):
    return rt.db.one("SELECT * FROM actions WHERE event_id=?", (event_id,))


def test_timeout_after_commit_is_uncertain_then_reconciled_without_duplicate(rt):
    rt.crm.faults.arm("create_deal", "timeout_after_commit")
    reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_t")
    a = _action(rt, "evt_t")
    assert a["status"] == "uncertain" and a["attempts"] == 1
    assert len(rt.crm.records_of("deal")) == 1          # it DID land
    assert rt.db.one("SELECT status FROM contacts WHERE id='c_lucia'")["status"] == "active"  # local effects not applied yet

    assert rt.orchestrator.outbox.process_due() == []   # not due yet: backoff
    rt.clock.advance(31)
    rt.orchestrator.outbox.process_due()
    a = _action(rt, "evt_t")
    assert a["status"] == "succeeded" and a["attempts"] == 2
    assert len(rt.crm.records_of("deal")) == 1          # still exactly one
    assert len(rt.crm.records_of("task")) == 1          # the dependent write completed on retry
    assert any(t["stage"] == "action_reconciled" and "DID land" in t["message"] for t in rt.db.trace("evt_t"))
    assert rt.db.one("SELECT status FROM contacts WHERE id='c_lucia'")["status"] == "handed_off"


def test_timeout_before_commit_is_resent(rt):
    rt.crm.faults.arm("create_deal", "timeout_before_commit")
    reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_b")
    assert len(rt.crm.records_of("deal")) == 0 and _action(rt, "evt_b")["status"] == "uncertain"
    rt.clock.advance(31)
    rt.orchestrator.outbox.process_due()
    assert _action(rt, "evt_b")["status"] == "succeeded" and len(rt.crm.records_of("deal")) == 1
    assert any("did NOT land" in t["message"] for t in rt.db.trace("evt_b"))


def test_rate_limit_backs_off_then_succeeds(rt):
    rt.crm.faults.arm("create_deal", "rate_limit")
    reply(rt, "c_ana", INTERESTED_PT, event_id="evt_r")
    a = _action(rt, "evt_r")
    assert a["status"] == "pending" and a["next_attempt_at"] > a["created_at"]
    assert rt.orchestrator.outbox.process_due() == []
    rt.clock.advance(31)
    rt.orchestrator.outbox.process_due()
    assert _action(rt, "evt_r")["status"] == "succeeded" and len(rt.crm.records_of("deal")) == 1


def test_permanent_error_goes_to_dead_letter_and_review_queue(rt):
    rt.crm.faults.arm("create_deal", "permanent_error")
    reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_p")
    assert _action(rt, "evt_p")["status"] == "dead"
    q = rt.db.one("SELECT * FROM review_queue WHERE event_id='evt_p'")
    assert q and q["proposed_action"] == Action.HANDOFF_TO_AE.value and "dead-letter" in q["reason"]


def test_repeated_uncertain_outcomes_eventually_dead_letter(rt):
    for _ in range(4):
        rt.crm.faults.arm("create_deal", "timeout_before_commit")
    reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_u")
    for _ in range(3):
        rt.clock.advance(700)
        rt.orchestrator.outbox.process_due()
    a = _action(rt, "evt_u")
    assert a["status"] == "dead" and a["attempts"] == 4
