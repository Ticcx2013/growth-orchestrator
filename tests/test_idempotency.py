"""Duplicate events and duplicate actions must never produce a second side effect."""

from growth_orchestrator.models import Action

from .conftest import INTERESTED_ES, reply, stages


def test_duplicate_event_is_ignored_and_counted(rt):
    first = reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_same")
    second = reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_same")

    assert first["action"] == Action.HANDOFF_TO_AE.value
    assert second["status"] == "duplicate"
    assert "duplicate" in stages(second)
    assert rt.db.one("SELECT duplicate_count FROM events WHERE event_id='evt_same'")["duplicate_count"] == 1
    assert rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"] == 1
    assert len(rt.crm.records_of("deal")) == 1


def test_duplicate_with_different_payload_is_still_a_duplicate(rt):
    reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_x")
    second = reply(rt, "c_lucia", "texto distinto pero mismo event_id", event_id="evt_x")
    assert second["status"] == "duplicate"


def test_outbox_enqueue_is_idempotent_per_event_and_action(rt):
    result = reply(rt, "c_lucia", INTERESTED_ES, event_id="evt_ob")
    row = rt.orchestrator.outbox.enqueue(decision_id=result["decision_id"], event_id="evt_ob", action=Action.HANDOFF_TO_AE, payload={})
    assert row["status"] == "succeeded"  # the existing, already-dispatched row is returned
    assert rt.db.one("SELECT COUNT(*) AS n FROM actions WHERE event_id='evt_ob'")["n"] == 1


def test_crm_write_with_same_key_returns_same_record(rt):
    a = rt.crm.create_deal(idempotency_key="k1", account_id="acc_andino", contact_id="c_lucia", owner_ae_id="ae_sofia", notes="")
    b = rt.crm.create_deal(idempotency_key="k1", account_id="acc_andino", contact_id="c_lucia", owner_ae_id="ae_sofia", notes="")
    assert a["id"] == b["id"]
    assert len(rt.crm.records_of("deal")) == 1
