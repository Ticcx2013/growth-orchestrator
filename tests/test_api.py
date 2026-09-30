"""HTTP contract: fast 2xx, duplicates answered 200, signature enforced when configured, review approvals execute."""

import hashlib
import hmac
import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from growth_orchestrator.api import create_app
from growth_orchestrator.models import Action

from .conftest import INTERESTED_ES, REFERRAL_ES

EVENT = {"event_id": "evt_api_1", "type": "reply.received", "occurred_at": "2026-09-30T15:00:00Z",
         "payload": {"contact_id": "c_lucia", "text": INTERESTED_ES}}


@pytest.fixture
def client(rt):
    return TestClient(create_app(rt))


def test_webhook_accepts_then_processes_in_background(client, rt):
    r = client.post("/events", json=EVENT)
    assert r.status_code == 202 and r.json()["status"] == "accepted"
    # TestClient runs background tasks before returning, so the work is done.
    assert rt.db.one("SELECT status FROM events WHERE event_id='evt_api_1'")["status"] == "processed"
    assert len(rt.crm.records_of("deal")) == 1


def test_duplicate_webhook_returns_200_and_does_nothing(client, rt):
    client.post("/events", json=EVENT)
    r = client.post("/events", json=EVENT)
    assert r.status_code == 200 and r.json()["status"] == "duplicate"
    assert len(rt.crm.records_of("deal")) == 1


def test_sync_mode_returns_the_trace(client):
    r = client.post("/events?sync=true", json=EVENT)
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == Action.HANDOFF_TO_AE.value and any(t["stage"] == "decision" for t in body["trace"])


def test_invalid_event_is_rejected(client):
    r = client.post("/events", json={"event_id": "x", "type": "not.a.type", "occurred_at": "2026-09-30T15:00:00Z"})
    assert r.status_code == 422


def test_signature_is_enforced_when_secret_is_configured(rt):
    rt.settings = replace(rt.settings, webhook_secret="s3cret")
    client = TestClient(create_app(rt))
    body = json.dumps(EVENT).encode()
    assert client.post("/events", content=body, headers={"Content-Type": "application/json"}).status_code == 401
    sig = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    assert client.post("/events", content=body, headers={"Content-Type": "application/json", "X-Signature": sig}).status_code == 202


def test_policy_roundtrip_bumps_version_and_changes_behaviour(client, rt):
    policy = client.get("/api/policy").json()
    policy["automation"]["handoff_to_ae"] = "assisted"
    saved = client.put("/api/policy", json=policy).json()
    assert saved["version"] == policy["version"] + 1
    r = client.post("/events?sync=true", json=EVENT).json()
    assert r["action"] == Action.HANDOFF_TO_AE.value and r["automated"] is False and r["requires_review"] is True
    assert rt.crm.records_of("deal") == []


def test_review_approval_executes_the_proposed_action(client, rt):
    ev = {**EVENT, "event_id": "evt_ref", "payload": {"contact_id": "c_camilo", "text": REFERRAL_ES}}
    r = client.post("/events?sync=true", json=ev).json()
    assert r["action"] == Action.CREATE_REFERRAL_CONTACT.value and r["requires_review"]
    item = client.get("/api/review").json()[0]
    assert item["proposed_action"] == Action.CREATE_REFERRAL_CONTACT.value
    out = client.post(f"/api/review/{item['id']}/approve", json={"by": "test"}).json()
    assert out["executed"]["status"] == "succeeded"
    assert rt.crm.records_of("contact")[0]["email"] == "maria.torres@solenergia.co"
    assert client.get("/api/review").json() == []


def test_console_pages_render(client):
    for path in ("/", "/policy", "/operations", "/about", "/glossary", "/static/i18n.js"):
        assert client.get(path).status_code == 200


def test_demo_scenarios_run_through_the_api(client):
    for s in client.get("/api/demo/scenarios").json():
        out = client.post(f"/api/demo/run/{s['key']}").json()
        assert out["steps"], s["key"]
