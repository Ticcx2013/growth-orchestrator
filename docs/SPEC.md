# SPEC: Growth Orchestration System (vertical slice)

Source: Clara's "Business Case Invitation" for the AI Growth Automation Engineer role. This file is the build contract the repository was written against; each milestone lists its acceptance criteria and where they are verified.

## Scope

One end-to-end flow: **a prospect replies → the reply is interpreted → the next best action is decided → executed safely → audited.** Supporting events: `prospect.identified` (rules only), `crm.account_updated` (state and ordering), `contact.unsubscribed` (compliance).

Out of scope on purpose: AI personalization, multichannel, real sending, calendar, SDR inbox, auth, deployment infrastructure.

## Milestones and acceptance criteria

### M1 Core without AI
- `POST /events` returns 202 in under 100 ms and processes in the background; duplicate `event_id` returns 200 and does nothing. → `tests/test_api.py`, `tests/test_idempotency.py`
- Persistent accounts, contacts, suppressions, events, decisions, actions, review queue, audit log in SQLite. → `db.py`
- Eight eligibility rules, all deterministic. → `tests/test_eligibility.py`
- Opt-out and injection rules in ES/PT/EN with no false positives on "not interested". → `tests/test_compliance.py`
- Policy from `policy.yaml`: automation mode per action, thresholds, intent → action map. → `tests/test_policy_engine.py`
- Outbox with idempotency key per action and a mock CRM that honours keys. → `tests/test_idempotency.py`

### M2 AI layer
- Structured output enforced by the API, validated by our own grounding checks, one repair round, then human. → `ai/interpreter.py`, `tests/test_ai_validation.py`
- Offline mode replays recorded real responses; tests and demo run without a key. → `ai/fixtures.json`
- Evaluation suite of 12–15 cases across ES/PT/EN with per-case checks and a zero-unsafe-automation gate. → `evals/`
- Live results committed for at least two models. → `evals/results/`

### M3 Reliability
- Timeout after commit → `uncertain` → reconcile by key → exactly one record. → `tests/test_outbox_retry.py`
- 429 → backoff with persisted `next_attempt_at`; permanent error → dead letter + review item. → same
- Stale CRM updates ignored; replies evaluated against current state. → `tests/test_ordering_and_freshness.py`
- Freshness check before irreversible actions, tolerant to a rate-limited CRM. → same

### M4 Console
- Control room runs the scenarios and shows all six stages with reasons.
- Policy screen edits `policy.yaml` with presets; a saved change alters the next decision without restart. → `tests/test_api.py::test_policy_roundtrip_bumps_version_and_changes_behaviour`
- Operations: review queue with approve/reject that executes the proposed action; outbox; audit; AI calls; state; CRM. → `tests/test_api.py::test_review_approval_executes_the_proposed_action`
- How-it-works: diagram, AI boundaries, latest eval, docs rendered.

### M5 Documents
- README with architecture, requirement map, AI boundaries, reliability, eval summary, production path.
- `docs/DECISIONS.md` (four required points), `docs/EXPERIMENT.md`, `docs/WHAT_IF.md`, `docs/AI_EVALUATION.md`.
- One architecture diagram (Mermaid in README and console).

## Demo checklist (presentation)
1. Successful flow → deal + task in CRM.
2. Duplicate event → one deal.
3. Failure and retry → uncertain, reconcile, 429 backoff, one deal one task.
4. Unsafe AI (injection) → zero actions, human.
5. Ambiguous AI (mixed) → rule suppresses, human gets the rest.
6. Out-of-order → stale ignored, reply judged on current state.
7. Stale local state → freshness check re-decides.
8. Live policy change → same scenario, different outcome.
