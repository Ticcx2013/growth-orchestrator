# Growth Orchestrator — rules for Claude Code sessions

Read `README.md`, `docs/DECISIONS.md` and `docs/SPEC.md` before changing anything.

## Non-negotiables
- The model interprets; it never decides an action. Actions come from `policy.yaml` through `decision.py`.
- Compliance (opt-out, injection) is rules in `compliance.py` and runs before the model. Never make it depend on the model.
- Every external side effect goes through `outbox.py` with an idempotency key. No direct CRM calls from handlers.
- Every stage writes to the audit log with a reason. If you add a stage, add its audit line and its pipeline mapping in `templates/index.html`.
- Secrets only from environment (`.env` is git-ignored). Never log or commit keys.
- `make test` must pass and `make eval` must report 0 unsafe automations before a commit.

## Conventions
- Python 3.12, `uv`, FastAPI, SQLite, Pydantic v2, pytest. No new dependencies without a reason in DECISIONS.md.
- Repo, code comments, docs and commits in English.
- Keep the console thin: server-rendered templates, Tailwind and Alpine from CDN, no build step.
- New reply texts used in demos or evals need a recorded fixture: run `make record` with an API key.
- Scope is the vertical slice in `docs/SPEC.md`. Do not add channels, UI for SDRs, real sending or calendar integration.
