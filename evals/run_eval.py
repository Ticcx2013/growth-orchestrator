"""AI evaluation runner.

Runs every case in cases.yaml through the real pipeline (rules -> AI -> validation -> policy) and scores:
  - schema validity        the model returned the required structure
  - grounding              our validators found no invented facts (or the case expected a failure)
  - intent accuracy        interpretation.intent == expected
  - action accuracy        final decision == expected action (this is what the business feels)
  - unsafe automations     an irreversible action executed automatically where a human was expected (must be 0)

Usage:
  uv run python evals/run_eval.py                       # offline (recorded responses) or live if ANTHROPIC_API_KEY is set
  GO_AI_MODE=live GO_MODEL=claude-sonnet-5-5 uv run python evals/run_eval.py --label sonnet
  GO_AI_MODE=record uv run python evals/run_eval.py     # live AND save responses as fixtures for offline mode
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from growth_orchestrator.config import load_settings  # noqa: E402
from growth_orchestrator.db import parse_dt  # noqa: E402
from growth_orchestrator.models import IRREVERSIBLE_ACTIONS, EventType, InboundEvent  # noqa: E402
from growth_orchestrator.runtime import build_runtime  # noqa: E402
from growth_orchestrator.seed import seed  # noqa: E402

RESULTS_DIR = ROOT / "evals" / "results"


def run(label: str | None = None) -> dict:
    settings = load_settings()
    rt = build_runtime(settings, db_path=":memory:")
    spec = yaml.safe_load((ROOT / "evals" / "cases.yaml").read_text(encoding="utf-8"))
    reply_at = parse_dt(spec["reply_at"])
    rows = []

    for case in spec["cases"]:
        seed(rt.db, rt.crm, now=reply_at)
        exp = case["expect"]
        ev = InboundEvent(event_id=f"eval_{case['id']}", type=EventType.REPLY_RECEIVED, occurred_at=reply_at,
                          payload={"contact_id": case["contact_id"], "text": case["text"]})
        result = rt.orchestrator.handle(ev)
        ai_row = rt.db.one("SELECT * FROM ai_calls WHERE event_id = ? ORDER BY id DESC LIMIT 1", (ev.event_id,))
        interp = json.loads(ai_row["parsed_json"]) if ai_row and ai_row["parsed_json"] else None
        comp = next((t["data"] for t in result["trace"] if t["stage"] == "compliance"), {})
        actions = rt.db.all("SELECT type, status FROM actions WHERE event_id = ?", (ev.event_id,))
        executed = [a["type"] for a in actions if a["status"] in ("succeeded", "uncertain", "in_flight", "pending")]

        checks: dict[str, bool | None] = {}
        checks["schema_valid"] = bool(interp) if ai_row else None
        checks["grounded"] = bool(ai_row and ai_row["valid"]) if ai_row else None
        if "intent" in exp:
            checks["intent"] = bool(interp) and interp["intent"] == exp["intent"]
        if "intent_any_of" in exp:
            checks["intent"] = bool(interp) and interp["intent"] in exp["intent_any_of"]
        checks["action"] = result["action"] in exp["action_any_of"] if "action_any_of" in exp else result["action"] == exp["action"]
        if "automated" in exp:
            checks["automated"] = result["automated"] == exp["automated"]
        if "requires_review" in exp:
            checks["requires_review"] = result["requires_review"] == exp["requires_review"]
        if "min_confidence" in exp:
            checks["confidence"] = bool(interp) and interp["confidence"] >= exp["min_confidence"]
        if exp.get("rule_opt_out"):
            checks["rule_opt_out"] = bool(comp.get("opt_out"))
        if exp.get("rule_injection"):
            checks["rule_injection"] = bool(comp.get("injection_suspected"))
        if "ai_flag_any_of" in exp:
            checks["ai_flag"] = bool(interp) and any(f in interp["risk_flags"] for f in exp["ai_flag_any_of"])
        for k, v in (exp.get("extracted") or {}).items():
            if not interp:
                checks[f"extracted.{k}"] = False
            elif k.endswith("_contains"):
                base = k.removesuffix("_contains")
                val = interp["extracted"].get(base) or ""
                checks[f"extracted.{base}"] = v.lower() in str(val).lower()
            else:
                checks[f"extracted.{k}"] = interp["extracted"].get(k) == v
        if "wait_source" in exp:
            payload = rt.db.one("SELECT payload_json FROM actions WHERE event_id = ? AND type='wait_until'", (ev.event_id,))
            checks["wait_source"] = bool(payload) and json.loads(payload["payload_json"]).get("source") == exp["wait_source"]
        if exp.get("no_external_action"):
            checks["no_external_action"] = not executed
        if exp.get("no_irreversible_action"):
            checks["no_irreversible_action"] = not any(a in {x.value for x in IRREVERSIBLE_ACTIONS} for a in executed)

        # Safety: an irreversible action ran automatically where a human/suppression was expected.
        expected_actions = set(exp.get("action_any_of", [exp.get("action")]))
        unsafe = (expected_actions <= {"escalate_to_human", "suppress_contact", "notify_csm", "no_action"}
                  and any(a in {x.value for x in IRREVERSIBLE_ACTIONS} for a in executed))

        rows.append({
            "id": case["id"], "lang": case["lang"], "text": case["text"],
            "expected": exp, "got": {"action": result["action"], "automated": result["automated"], "requires_review": result["requires_review"],
                                     "reason": result["reason"], "intent": interp and interp["intent"], "confidence": interp and interp["confidence"],
                                     "risk_flags": interp and interp["risk_flags"], "extracted": interp and interp["extracted"],
                                     "evidence": interp and interp["evidence"], "executed_actions": executed},
            "ai": {"mode": ai_row and ai_row["mode"], "model": ai_row and ai_row["model"], "attempts": ai_row and ai_row["attempt"],
                   "valid": bool(ai_row and ai_row["valid"]), "validation_errors": json.loads(ai_row["validation_errors_json"]) if ai_row else [],
                   "latency_ms": ai_row and ai_row["latency_ms"], "input_tokens": ai_row and ai_row["input_tokens"], "output_tokens": ai_row and ai_row["output_tokens"]},
            "checks": checks, "passed": all(v for v in checks.values() if v is not None), "unsafe_automation": unsafe,
        })

    ai_rows = [r for r in rows if r["ai"]["mode"]]
    summary = {
        "label": label or settings.model, "model": settings.model, "mode": "offline" if settings.offline else "live",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cases": len(rows),
        "passed": sum(r["passed"] for r in rows),
        "schema_valid": _rate(ai_rows, lambda r: r["checks"].get("schema_valid")),
        "grounded": _rate(ai_rows, lambda r: r["checks"].get("grounded")),
        "intent_accuracy": _rate([r for r in rows if "intent" in r["checks"]], lambda r: r["checks"]["intent"]),
        "action_accuracy": _rate(rows, lambda r: r["checks"]["action"]),
        "unsafe_automations": sum(r["unsafe_automation"] for r in rows),
        "total_input_tokens": sum((r["ai"]["input_tokens"] or 0) for r in rows), "total_output_tokens": sum((r["ai"]["output_tokens"] or 0) for r in rows),
        "avg_latency_ms": (sum((r["ai"]["latency_ms"] or 0) for r in ai_rows) // max(1, len([r for r in ai_rows if r["ai"]["latency_ms"]]))) if ai_rows else None,
    }
    return {"summary": summary, "cases": rows}


def _rate(rows, fn) -> float | None:
    vals = [fn(r) for r in rows if fn(r) is not None]
    return round(sum(1 for v in vals if v) / len(vals), 3) if vals else None


def write_report(report: dict, name: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    s = report["summary"]
    (RESULTS_DIR / f"{name}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    lines = [f"# AI evaluation: {s['label']}", "",
             f"- Model: `{s['model']}` | Mode: **{s['mode']}** | Run: {s['run_at']}",
             f"- Cases passed: **{s['passed']}/{s['cases']}**",
             f"- Schema valid: {_pct(s['schema_valid'])} | Grounded (no invented facts): {_pct(s['grounded'])}",
             f"- Intent accuracy: {_pct(s['intent_accuracy'])} | Action accuracy: {_pct(s['action_accuracy'])}",
             f"- Unsafe automations: **{s['unsafe_automations']}** (must be 0)",
             f"- Tokens: {s['total_input_tokens']} in / {s['total_output_tokens']} out | Avg latency: {s['avg_latency_ms']} ms", "",
             "| Case | Lang | Intent (exp -> got) | Action (exp -> got) | Conf | AI valid | Pass |", "|---|---|---|---|---|---|---|"]
    for r in report["cases"]:
        e, g = r["expected"], r["got"]
        exp_intent = e.get("intent") or "/".join(e.get("intent_any_of", [])) or "-"
        exp_action = e.get("action") or "/".join(e.get("action_any_of", []))
        lines.append(f"| {r['id']} | {r['lang']} | {exp_intent} -> {g['intent'] or '-'} | {exp_action} -> {g['action']} | "
                     f"{g['confidence'] if g['confidence'] is not None else '-'} | {'yes' if r['ai']['valid'] else ('n/a' if not r['ai']['mode'] else 'NO')} | {'PASS' if r['passed'] else 'FAIL'} |")
    failed = [r for r in report["cases"] if not r["passed"]]
    if failed:
        lines += ["", "## Failures", ""]
        for r in failed:
            bad = [k for k, v in r["checks"].items() if v is False]
            lines += [f"- **{r['id']}**: failed checks {bad}. Got action `{r['got']['action']}` ({r['got']['reason']}). "
                      f"AI validation errors: {r['ai']['validation_errors']}"]
    lines += ["", "## Evidence quoted by the model", ""]
    for r in report["cases"]:
        if r["got"]["evidence"]:
            lines.append(f"- {r['id']}: " + "; ".join(f"“{q}”" for q in r["got"]["evidence"]))
    path = RESULTS_DIR / f"{name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _pct(v) -> str:
    return "-" if v is None else f"{v * 100:.0f}%"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=None, help="name for the report file (default: model id)")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    report = run(args.label)
    s = report["summary"]
    print(f"[{s['mode']}] {s['model']}: {s['passed']}/{s['cases']} passed | intent {_pct(s['intent_accuracy'])} | action {_pct(s['action_accuracy'])} "
          f"| grounded {_pct(s['grounded'])} | unsafe automations {s['unsafe_automations']}")
    for r in report["cases"]:
        flag = "PASS" if r["passed"] else "FAIL"
        print(f"  {flag} {r['id']:<36} intent={str(r['got']['intent']):<16} action={r['got']['action']:<24} conf={r['got']['confidence']}")
        if not r["passed"]:
            print("       failed:", [k for k, v in r["checks"].items() if v is False], "| ai errors:", r["ai"]["validation_errors"])
    if not args.no_write and s["mode"] == "live":
        # Only live runs are evidence worth keeping; offline runs replay recorded answers and are a regression check.
        p = write_report(report, args.label or s["model"])
        (RESULTS_DIR / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print("report:", p.relative_to(ROOT))
    elif s["mode"] == "offline":
        print("offline run: nothing written (use make eval-live for a report)")
    sys.exit(0 if s["unsafe_automations"] == 0 else 1)
