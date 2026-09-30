# If you change an assumption

Six changes a panel might propose live, with what moves in the code and what does not.

## 1. "Replies also come in on WhatsApp and LinkedIn, not only email."

- **Unchanged:** the whole pipeline. Events already carry `channel` in the payload; eligibility, compliance, interpretation, policy and outbox are channel-agnostic.
- **Changes:** one adapter per channel that normalises the provider's webhook into `reply.received` with a stable `event_id`. Opt-out regex gets channel-specific phrasings ("STOP", "baja" as a single word). Policy gains per-channel cooldowns since WhatsApp tolerates less frequency.
- **Watch out for:** WhatsApp consent rules (opt-in required in MX/BR/CO) become an eligibility rule, not a model task.

## 2. "Scale is 500k companies a month, not 50k."

- **Unchanged:** the logic and the schema.
- **Changes:** SQLite → Postgres; a queue between `/events` and processing; N workers with a per-account lock; batch the model calls where latency allows (the Messages Batch API is half price). At 2,500 replies/day the model bill is still under $50/day at Opus prices, and Sonnet would halve it.
- **The real constraint** moves to CRM API quotas and sending domains. The outbox's backoff already respects 429s; add per-integration concurrency limits.

## 3. "The CRM is the only source of truth; you may not keep local state."

- **Unchanged:** the decision logic and the audit log.
- **Changes:** `eligibility.evaluate` reads account facts from the CRM adapter with a short cache instead of `accounts`. The freshness check becomes redundant (every read is fresh) and the ordering guard moves to the CRM's own `updated_at`. Latency per event rises by one CRM read; the outbox and idempotency keys stay exactly as they are because the CRM still cannot deduplicate our writes for us.
- **Risk introduced:** a CRM outage stalls decisions. Mitigation: degrade to "escalate everything", which the system already does when the model is unavailable.

## 4. "We want the AI to write the reply, not just read it."

- **Unchanged:** interpretation and policy. Drafting is a *new* action type, `draft_reply`, that starts in `assisted` mode by definition.
- **Changes:** a second model call with grounded inputs (the reply, the interpretation, approved snippets), a validator that rejects any factual claim not present in the inputs, and a review step where the SDR edits before sending. Add drafting quality to the evaluation suite with human grading.
- **Non-negotiable:** the draft never sends itself until the experiment in EXPERIMENT.md shows it does not hurt acceptance or complaint rates.

## 5. "No humans in the loop. Everything automated from day one."

- **What the policy file allows:** set every action to `auto` (the "Fully autonomous" preset) and lower the confidence gates. The system will run.
- **What I would say:** ambiguous, contradictory and injected replies still have to go somewhere. Without a queue they either get a default action (unsafe) or get dropped (lost pipeline). The honest version of "no humans" is a much narrower automated scope and a *later*, not earlier, shadow-mode gate. I would keep `escalate_to_human` as the fallback for the small residual and measure how small it is; on the evaluation set it is ~25% under conservative thresholds and would fall with data.

## 6. "The model gets it wrong on Brazilian Portuguese slang."

- **Unchanged:** architecture. This is exactly what the gates are for.
- **Changes:** add the failing replies to `evals/cases.yaml`, run `make eval-live` per model, and pick the one that passes. If none does, raise `min_confidence_auto` for `language == pt` only (a one-line policy change) so PT replies route to humans while the prompt or model is improved. The audit log's `language` field shows the routing split per language for free.
