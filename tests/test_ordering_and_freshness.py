"""Out-of-order events and stale local state."""

from datetime import timedelta

from growth_orchestrator.models import Action, EventType

from .conftest import INTERESTED_ES, INTERESTED_PT, event, reply, stages


def test_stale_account_update_is_ignored(rt):
    newer = event(rt, EventType.CRM_ACCOUNT_UPDATED, {"account_id": "acc_delta", "is_customer": True}, occurred_at=rt.clock() - timedelta(hours=1))
    assert newer["status"] == "processed"
    assert rt.db.one("SELECT is_customer, state_version FROM accounts WHERE id='acc_delta'") == {"is_customer": 1, "state_version": 2}

    older = event(rt, EventType.CRM_ACCOUNT_UPDATED, {"account_id": "acc_delta", "is_customer": False}, occurred_at=rt.clock() - timedelta(days=2))
    assert older["status"] == "ignored_stale" and "stale_event" in stages(older)
    assert rt.db.one("SELECT is_customer, state_version FROM accounts WHERE id='acc_delta'") == {"is_customer": 1, "state_version": 2}


def test_reply_that_predates_state_change_is_judged_on_current_state(rt):
    event(rt, EventType.CRM_ACCOUNT_UPDATED, {"account_id": "acc_delta", "is_customer": True, "csm_id": "csm_lucia"}, occurred_at=rt.clock() - timedelta(hours=1))
    out = reply(rt, "c_sara", INTERESTED_ES, occurred_at=rt.clock() - timedelta(hours=3))
    assert "ordering" in stages(out)
    assert out["action"] == Action.NOTIFY_CSM.value
    assert rt.crm.records_of("deal") == []


def test_becoming_a_customer_pauses_active_sequences(rt):
    event(rt, EventType.CRM_ACCOUNT_UPDATED, {"account_id": "acc_delta", "is_customer": True})
    assert rt.db.one("SELECT sequence_status FROM contacts WHERE id='c_sara'")["sequence_status"] == "paused"


def test_freshness_check_catches_a_lagging_crm_webhook(rt):
    rt.crm.accounts["acc_verde"].update({"has_open_opportunity": 1, "owner_ae_id": "ae_rafael"})
    out = reply(rt, "c_joao", INTERESTED_PT)
    assert "freshness_check" in stages(out)
    assert out["action"] == Action.NOTIFY_CSM.value and out["reason"].startswith("[re-decided after freshness check]")
    assert rt.crm.records_of("deal") == []
    assert rt.db.one("SELECT has_open_opportunity FROM accounts WHERE id='acc_verde'")["has_open_opportunity"] == 1


def test_freshness_check_can_be_disabled_by_policy(rt):
    policy = rt.policies.load().model_copy(deep=True)
    policy.ai.freshness_check_before_irreversible = False
    rt.policies.replace(policy)
    rt.crm.accounts["acc_verde"].update({"has_open_opportunity": 1})
    out = reply(rt, "c_joao", INTERESTED_PT)
    assert "freshness_check" not in stages(out) and out["action"] == Action.HANDOFF_TO_AE.value


def test_freshness_check_survives_a_rate_limited_crm(rt):
    rt.crm.faults.arm("get_account", "rate_limit")
    out = reply(rt, "c_lucia", INTERESTED_ES)
    assert out["action"] == Action.HANDOFF_TO_AE.value
    assert any("rate-limited during freshness check" in t["message"] for t in out["trace"])
