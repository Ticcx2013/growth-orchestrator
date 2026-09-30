"""HTTP surface: the webhook, a small JSON API for the console, and the console pages themselves.

Webhook contract: respond fast (202), do the work after. Duplicates are answered 200 and never re-processed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from .config import ROOT
from .db import iso
from .models import Action, InboundEvent
from .policy import Policy
from .runtime import Runtime, build_runtime
from .seed import seed

sys.path.insert(0, str(ROOT))
from demo.scenarios import SCENARIOS, run_scenario  # noqa: E402

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def create_app(rt: Runtime | None = None) -> FastAPI:
    rt = rt or build_runtime()
    app = FastAPI(title="Growth Orchestrator", version="0.1.0",
                  description="event -> state -> decision -> AI/rules -> action -> audit")
    app.state.rt = rt

    # Seed on first boot so the console has something to show.
    if rt.db.one("SELECT COUNT(*) AS n FROM accounts")["n"] == 0:
        seed(rt.db, rt.crm, now=rt.clock())

    # ------------------------------------------------------------------------------
    # 1. Trigger: the webhook
    # ------------------------------------------------------------------------------
    @app.post("/events", status_code=202)
    async def receive_event(request: Request, background: BackgroundTasks, sync: bool = False):
        body = await request.body()
        if rt.settings.webhook_secret:
            sig = request.headers.get("X-Signature", "")
            expected = hmac.new(rt.settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                raise HTTPException(401, "invalid signature")
        try:
            event = InboundEvent.model_validate_json(body)
        except ValidationError as e:
            raise HTTPException(422, e.errors())

        with rt.lock:
            ing = rt.orchestrator.ingest(event)
        if ing["status"] == "duplicate":
            return JSONResponse({"status": "duplicate", "event_id": event.event_id}, status_code=200)
        if sync:
            with rt.lock:
                result = rt.orchestrator.process(event.event_id)
                result["trace"] = rt.db.trace(event.event_id)
            return JSONResponse(result, status_code=200)
        background.add_task(_process_locked, rt, event.event_id)
        return {"status": "accepted", "event_id": event.event_id}

    # ------------------------------------------------------------------------------
    # 2. Read API for the console
    # ------------------------------------------------------------------------------
    @app.get("/api/events")
    def list_events(limit: int = 50):
        return rt.db.all("SELECT * FROM events ORDER BY received_at DESC LIMIT ?", (limit,))

    @app.get("/api/events/{event_id}/trace")
    def event_trace(event_id: str):
        return rt.db.trace(event_id)

    @app.get("/api/state")
    def state():
        return {"accounts": rt.db.all("SELECT * FROM accounts ORDER BY name"),
                "contacts": rt.db.all("SELECT * FROM contacts ORDER BY account_id, name"),
                "suppressions": rt.db.all("SELECT * FROM suppressions ORDER BY id")}

    @app.get("/api/decisions")
    def decisions(limit: int = 50):
        rows = rt.db.all("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,))
        for r in rows:
            r["trace"] = json.loads(r.pop("trace_json"))
            r["payload"] = json.loads(r.pop("payload_json"))
        return rows

    @app.get("/api/actions")
    def actions(limit: int = 50):
        rows = rt.db.all("SELECT * FROM actions ORDER BY created_at DESC LIMIT ?", (limit,))
        for r in rows:
            r["payload"] = json.loads(r.pop("payload_json"))
        return rows

    @app.get("/api/audit")
    def audit(limit: int = 200):
        rows = rt.db.all("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
        for r in rows:
            r["data"] = json.loads(r.pop("data_json")) if r.get("data_json") else None
        return rows

    @app.get("/api/ai_calls")
    def ai_calls(limit: int = 50):
        rows = rt.db.all("SELECT * FROM ai_calls ORDER BY id DESC LIMIT ?", (limit,))
        for r in rows:
            r["parsed"] = json.loads(r.pop("parsed_json")) if r.get("parsed_json") else None
            r["validation_errors"] = json.loads(r.pop("validation_errors_json") or "[]")
        return rows

    @app.get("/api/crm")
    def crm():
        return {"records": list(rt.crm.records.values()), "accounts": list(rt.crm.accounts.values()), "calls": rt.crm.calls[-50:],
                "faults_fired": rt.crm.faults.fired}

    # ------------------------------------------------------------------------------
    # 3. Human review queue
    # ------------------------------------------------------------------------------
    @app.get("/api/review")
    def review(status: str = "open"):
        rows = rt.db.all(
            "SELECT r.*, d.action AS decision_action, d.reason AS decision_reason, d.payload_json, d.contact_id, d.account_id,"
            " e.payload_json AS event_payload, a.parsed_json AS ai_parsed"
            " FROM review_queue r JOIN decisions d ON d.id = r.decision_id JOIN events e ON e.event_id = r.event_id"
            " LEFT JOIN ai_calls a ON a.id = d.ai_call_id"
            " WHERE (? = 'all' OR r.status = ?) ORDER BY r.id DESC", (status, status))
        for r in rows:
            r["payload"] = json.loads(r.pop("payload_json"))
            r["event_payload"] = json.loads(r.pop("event_payload"))
            parsed = r.pop("ai_parsed")
            r["ai"] = json.loads(parsed) if parsed else None
        return rows

    @app.post("/api/review/{item_id}/approve")
    def approve(item_id: int, body: dict[str, Any] | None = None):
        item = rt.db.one("SELECT r.*, d.payload_json FROM review_queue r JOIN decisions d ON d.id = r.decision_id WHERE r.id = ?", (item_id,))
        if not item or item["status"] != "open":
            raise HTTPException(404, "review item not open")
        proposed = (body or {}).get("action") or item["proposed_action"]
        executed = None
        with rt.lock:
            if proposed and proposed not in ("no_action", "escalate_to_human"):
                action = Action(proposed)
                payload = json.loads(item["payload_json"])
                row = rt.orchestrator.outbox.enqueue(decision_id=item["decision_id"], event_id=item["event_id"], action=action, payload=payload)
                executed = rt.orchestrator.outbox.dispatch(row["idempotency_key"])
                rt.db.audit(item["event_id"], "human_decision", f"reviewer approved {action.value}", {"review_id": item_id, "by": (body or {}).get("by", "console")})
            else:
                rt.db.audit(item["event_id"], "human_decision", "reviewer closed the item with no action", {"review_id": item_id})
            rt.db.exec("UPDATE review_queue SET status='approved', resolved_by=?, resolution_note=?, resolved_at=? WHERE id=?",
                       ((body or {}).get("by", "console"), (body or {}).get("note"), iso(rt.clock()), item_id))
        return {"status": "approved", "executed": executed}

    @app.post("/api/review/{item_id}/reject")
    def reject(item_id: int, body: dict[str, Any] | None = None):
        item = rt.db.one("SELECT * FROM review_queue WHERE id = ?", (item_id,))
        if not item or item["status"] != "open":
            raise HTTPException(404, "review item not open")
        rt.db.exec("UPDATE review_queue SET status='rejected', resolved_by=?, resolution_note=?, resolved_at=? WHERE id=?",
                   ((body or {}).get("by", "console"), (body or {}).get("note"), iso(rt.clock()), item_id))
        rt.db.audit(item["event_id"], "human_decision", "reviewer rejected the proposed action", {"review_id": item_id})
        return {"status": "rejected"}

    # ------------------------------------------------------------------------------
    # 4. Policy (the "change an assumption live" surface)
    # ------------------------------------------------------------------------------
    @app.get("/api/policy")
    def get_policy():
        return rt.policies.load().model_dump(mode="json")

    @app.put("/api/policy")
    def put_policy(body: dict[str, Any]):
        try:
            current = rt.policies.load()
            body["version"] = current.version
            policy = Policy.model_validate(body)
        except ValidationError as e:
            raise HTTPException(422, e.errors())
        saved = rt.policies.save(policy)
        rt.db.audit(None, "policy_changed", f"policy saved as version {saved.version}", {"automation": saved.model_dump(mode='json')["automation"]})
        return saved.model_dump(mode="json")

    # ------------------------------------------------------------------------------
    # 5. Demo and operations helpers
    # ------------------------------------------------------------------------------
    @app.get("/api/demo/scenarios")
    def scenarios():
        return [{"key": k, "title": v["title"], "summary": v["summary"], "kind": v["kind"]} for k, v in SCENARIOS.items()]

    @app.post("/api/demo/run/{key}")
    def run_demo(key: str, reset: bool = True):
        if key not in SCENARIOS:
            raise HTTPException(404, "unknown scenario")
        return run_scenario(rt, key, reset=reset)

    @app.post("/api/demo/reset")
    def reset():
        with rt.lock:
            rt.clock.reset()
            seed(rt.db, rt.crm, now=rt.clock())
        return {"status": "reset"}

    @app.post("/api/outbox/tick")
    def outbox_tick(advance_seconds: float = 0):
        with rt.lock:
            if advance_seconds:
                rt.clock.advance(advance_seconds)
            return {"processed": rt.orchestrator.outbox.process_due(), "clock": iso(rt.clock())}

    @app.get("/api/eval/results")
    def eval_results():
        d = ROOT / "evals" / "results"
        latest = d / "latest.json"
        reports = sorted([p.name for p in d.glob("*.md")]) if d.exists() else []
        return {"latest": json.loads(latest.read_text(encoding="utf-8")) if latest.exists() else None, "reports": reports}

    @app.get("/api/health")
    def health():
        return {"ok": True, "ai_mode": "offline" if rt.settings.offline else "live", "model": rt.settings.model,
                "policy_version": rt.policies.load().version, "clock": iso(rt.clock())}

    # ------------------------------------------------------------------------------
    # 6. Console pages
    # ------------------------------------------------------------------------------
    def page(request: Request, name: str, **ctx):
        base = {"request": request, "page": name, "ai_mode": "offline" if rt.settings.offline else "live", "model": rt.settings.model}
        return TEMPLATES.TemplateResponse(request, f"{name}.html", {**base, **ctx})

    @app.get("/", response_class=HTMLResponse)
    def ui_index(request: Request):
        return page(request, "index", scenarios=scenarios())

    @app.get("/policy", response_class=HTMLResponse)
    def ui_policy(request: Request):
        return page(request, "policy", actions=[a.value for a in Action if a not in (Action.NO_ACTION,)])

    @app.get("/operations", response_class=HTMLResponse)
    def ui_operations(request: Request):
        return page(request, "operations")

    @app.get("/about", response_class=HTMLResponse)
    def ui_about(request: Request):
        docs = {}
        for name in ("DECISIONS.md", "EXPERIMENT.md", "WHAT_IF.md"):
            p = ROOT / "docs" / name
            docs[name] = p.read_text(encoding="utf-8") if p.exists() else ""
        return page(request, "about", docs=docs)

    return app


def _process_locked(rt: Runtime, event_id: str) -> None:
    with rt.lock:
        rt.orchestrator.process(event_id)


app = create_app()
