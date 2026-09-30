"""HTTP contract: fast 2xx, duplicates answered 200, signature enforced when configured, review approvals execute."""

import hashlib
import hmac
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

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


def test_approving_a_low_confidence_escalation_rebuilds_the_payload(client, rt):
    policy = rt.policies.load().model_copy(deep=True)
    policy.ai.min_confidence_auto = 0.99  # force the interested reply to escalate with a proposed handoff
    rt.policies.replace(policy)
    r = client.post("/events?sync=true", json={**EVENT, "event_id": "evt_low"}).json()
    assert r["action"] == Action.ESCALATE_TO_HUMAN.value
    item = client.get("/api/review").json()[0]
    assert item["proposed_action"] == Action.HANDOFF_TO_AE.value and item["payload"] == {}
    out = client.post(f"/api/review/{item['id']}/approve", json={"by": "test"}).json()
    assert out["executed"]["status"] == "succeeded"
    assert len(rt.crm.records_of("deal")) == 1 and rt.crm.records_of("deal")[0]["owner_ae_id"] == "ae_sofia"
    assert rt.db.one("SELECT status FROM contacts WHERE id='c_lucia'")["status"] == "handed_off"


def test_approving_out_of_icp_pricing_escalation_works(client, rt):
    from .conftest import PRICING_ES
    r = client.post("/events?sync=true", json={**EVENT, "event_id": "evt_price", "payload": {"contact_id": "c_mateo", "text": PRICING_ES}}).json()
    assert r["action"] == Action.ESCALATE_TO_HUMAN.value
    item = client.get("/api/review").json()[0]
    out = client.post(f"/api/review/{item['id']}/approve", json={"by": "test"}).json()
    assert out["executed"]["status"] == "succeeded" and len(rt.crm.records_of("deal")) == 1


def test_approve_rejects_unknown_actions(client, rt):
    from .conftest import UNCLEAR
    client.post("/events?sync=true", json={**EVENT, "event_id": "evt_unclear", "payload": {"contact_id": "c_ana", "text": UNCLEAR}})
    item = client.get("/api/review").json()[0]
    assert client.post(f"/api/review/{item['id']}/approve", json={"action": "send_gift"}).status_code == 422
    assert client.get("/api/review").json()[0]["status"] == "open"


def test_webhook_does_not_block_on_a_slow_model():
    """Two events in flight: the second webhook must be acknowledged while the first is still with the model."""
    import threading, time
    from .conftest import NOW, ROOT
    import shutil
    from growth_orchestrator.config import Settings
    from growth_orchestrator.runtime import build_runtime
    from growth_orchestrator.seed import seed
    import tempfile
    tmp = Path(tempfile.mkdtemp()); shutil.copy(ROOT / "policy.yaml", tmp / "policy.yaml")
    settings = Settings(db_path=Path(":memory:"), policy_path=tmp / "policy.yaml", model="m", anthropic_api_key=None, webhook_secret=None, ai_mode="offline")
    rt = build_runtime(settings, db_path=":memory:"); rt.clock.offset = NOW - datetime.now(timezone.utc); seed(rt.db, rt.crm, now=rt.clock())
    real = rt.interpreter.interpret
    calls = []
    def slow_interpret(*a, **kw):
        calls.append(1)
        if len(calls) == 1:  # only the first event's model call is slow; the second must not wait for it
            time.sleep(1.5)
        return real(*a, **kw)
    rt.interpreter.interpret = slow_interpret
    app = create_app(rt)
    timings = {}
    def post(name, event_id, sync):
        t0 = time.perf_counter()
        with TestClient(app) as c:
            c.post(f"/events?sync={'true' if sync else 'false'}", json={**EVENT, "event_id": event_id})
        timings[name] = time.perf_counter() - t0
    first = threading.Thread(target=post, args=("slow", "evt_slow", True)); first.start(); time.sleep(0.3)
    post("second", "evt_fast", False)
    first.join()
    assert timings["slow"] >= 1.5
    assert timings["second"] < 1.0, timings
