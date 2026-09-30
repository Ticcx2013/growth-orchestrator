"""Narrated CLI demo: runs the scenarios end to end and prints every audit stage.

  uv run python demo/run_demo.py                 # all scenarios
  uv run python demo/run_demo.py crm_failure_retry
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from demo.scenarios import SCENARIOS, run_scenario  # noqa: E402
from growth_orchestrator.runtime import build_runtime  # noqa: E402

STAGE_ICON = {
    "received": "IN ", "duplicate": "DUP", "state_loaded": "ST ", "ordering": "ORD", "stale_event": "OLD", "state_updated": "ST+",
    "eligibility": "ELG", "compliance": "LAW", "ai_interpretation": "AI ", "ai_validation": "CHK", "decision": "DEC",
    "freshness_check": "FRS", "action_enqueued": "OUT", "action_dispatched": "ACT", "action_uncertain": "???",
    "action_reconciled": "RCN", "action_retry_scheduled": "RTY", "action_dead": "DLQ", "review_queued": "HUM", "completed": "END", "failed": "ERR",
}


def main(keys: list[str]) -> None:
    rt = build_runtime(db_path=":memory:")
    print(f"Growth Orchestrator demo | AI mode: {'OFFLINE (recorded responses)' if rt.settings.offline else 'LIVE ' + rt.settings.model}\n")
    for key in keys:
        out = run_scenario(rt, key)
        print("=" * 100)
        print(f"{out['title']}  --  {out['summary']}")
        print("=" * 100)
        for step in out["steps"]:
            print(f"\n> {step['title']}")
            if step.get("note"):
                print(f"  {step['note']}")
            if step.get("event"):
                p = step["event"]["payload"]
                if "text" in p:
                    print(f"  reply: “{p['text']}”")
            for t in step["trace"]:
                print(f"  [{STAGE_ICON.get(t['stage'], '   ')}] {t['stage']:<22} {t['message']}")
            r = step.get("result") or {}
            if r:
                print(f"  => {r}")
            if step.get("crm"):
                print(f"  CRM: {step['crm']['records']}  faults fired: {step['crm']['faults_fired']}")
        print(f"\nCRM at end: {out['crm']['records']} | open review items: {len(out['review_queue'])}\n")


if __name__ == "__main__":
    main(sys.argv[1:] or list(SCENARIOS))
