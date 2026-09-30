"""Eligibility is decided by state and policy, never by the model."""


from growth_orchestrator import eligibility
from growth_orchestrator.db import iso
from growth_orchestrator.models import Action, EventType

from .conftest import INTERESTED_ES, event, reply


def _acc(rt, aid):
    return rt.db.one("SELECT * FROM accounts WHERE id=?", (aid,))


def _con(rt, cid):
    return rt.db.one("SELECT * FROM contacts WHERE id=?", (cid,))


def test_customer_is_blocked_and_reply_goes_to_csm_without_calling_the_model(rt):
    res = eligibility.evaluate(rt.db, _acc(rt, "acc_norte"), _con(rt, "c_rosa"), rt.policies.load(), rt.clock(), purpose="reply")
    assert not res.eligible and "already_customer" in res.blockers

    out = reply(rt, "c_rosa", INTERESTED_ES)
    assert out["action"] == Action.NOTIFY_CSM.value
    assert rt.db.one("SELECT COUNT(*) AS n FROM ai_calls")["n"] == 0
    assert len(rt.crm.records_of("deal")) == 0


def test_active_opportunity_forwards_to_the_ae_and_never_creates_a_second_deal(rt):
    out = reply(rt, "c_valeria", INTERESTED_ES)  # Marea Seguros has an open opp owned by ae_diego
    assert out["action"] == Action.NOTIFY_CSM.value
    task = rt.crm.records_of("task")[0]
    assert task["owner_id"] == "ae_diego"
    assert len(rt.crm.records_of("deal")) == 0


def test_suppressed_contact_is_only_logged(rt):
    out = reply(rt, "c_optout", INTERESTED_ES)
    assert out["action"] == Action.NO_ACTION.value
    assert rt.db.one("SELECT COUNT(*) AS n FROM actions")["n"] == 0


def test_domain_suppression_blocks_outreach(rt):
    rt.db.exec("UPDATE accounts SET domain='gov.mx' WHERE id='acc_andino'")
    res = eligibility.evaluate(rt.db, _acc(rt, "acc_andino"), _con(rt, "c_pedro"), rt.policies.load(), rt.clock())
    assert "suppressed" in res.blockers


def test_cooldown_blocks_new_outreach_but_not_replies(rt):
    policy = rt.policies.load()
    contact = _con(rt, "c_recent")  # contacted 3 days ago
    res_out = eligibility.evaluate(rt.db, _acc(rt, "acc_sol"), contact, policy, rt.clock(), purpose="outreach")
    res_rep = eligibility.evaluate(rt.db, _acc(rt, "acc_sol"), contact, policy, rt.clock(), purpose="reply")
    assert "cooldown" in res_out.blockers
    assert "cooldown" not in res_rep.blockers


def test_contact_cap_per_account(rt):
    policy = rt.policies.load().model_copy(deep=True)
    policy.eligibility.max_active_contacts_per_account = 1
    rt.policies.replace(policy)
    # acc_verde already has two enrolled contacts (Ana, João); a third one must wait.
    rt.db.exec("INSERT INTO contacts(id,account_id,email,name,status,sequence_status,enriched,updated_at) VALUES ('c_new','acc_verde','n@verdefoods.com.br','N','active','none',1,?)", (iso(rt.clock()),))
    res = eligibility.evaluate(rt.db, _acc(rt, "acc_verde"), _con(rt, "c_new"), policy, rt.clock())
    assert "account_contact_cap" in res.blockers


def test_out_of_icp_blocks_outreach_and_is_soft_for_replies(rt):
    policy = rt.policies.load()
    res_out = eligibility.evaluate(rt.db, _acc(rt, "acc_cafeto"), _con(rt, "c_mateo"), policy, rt.clock(), purpose="outreach")
    res_rep = eligibility.evaluate(rt.db, _acc(rt, "acc_cafeto"), _con(rt, "c_mateo"), policy, rt.clock(), purpose="reply")
    assert "out_of_icp" in res_out.blockers
    assert res_rep.eligible


def test_prospect_identified_enriches_then_enrolls(rt):
    first = event(rt, EventType.PROSPECT_IDENTIFIED, {"contact_id": "c_pedro"})
    assert first["action"] == Action.ENRICH_CONTACT.value
    second = event(rt, EventType.PROSPECT_IDENTIFIED, {"contact_id": "c_pedro"})
    assert second["action"] == Action.ENROLL_IN_SEQUENCE.value
    assert _con(rt, "c_pedro")["sequence_status"] == "enrolled"


def test_prospect_identified_for_customer_does_nothing(rt):
    out = event(rt, EventType.PROSPECT_IDENTIFIED, {"contact_id": "c_rosa"})
    assert out["action"] == Action.NO_ACTION.value
