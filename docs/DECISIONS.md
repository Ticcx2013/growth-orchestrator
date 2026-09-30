# Decision log

## Something I deliberately did not build

**AI-written personalization of the first outbound email**, plus multichannel sequencing, a real calendar integration and an SDR-facing inbox.

Personalization is the most visible use of an LLM in outbound and the least defensible one in this case. It multiplies the number of things that can go wrong in front of a prospect (hallucinated facts about their company, tone drift across three languages, compliance wording) while the business question is not "can we write more emails" but "can we qualify without adding SDRs". The reply-triage flow is where the SDR hours actually go, so that is where the depth went. Personalization is a candidate for a *later* experiment, gated by the same evaluation discipline.

The console is deliberately thin: it exists so a non-technical operator can change policy and clear the review queue, which is the real user of this system. It is not an SDR workspace.

## Somewhere I deliberately did not use AI

**Eligibility, suppression and opt-out, deduplication, ordering, and the mapping from intent to action.**

Each of these is a question about state or policy, not about language. A rule is cheaper, faster, testable, explainable to a regulator, and editable by RevOps without a prompt change. Opt-out detection in particular runs *before* the model and wins any disagreement: LFPDPPP (Mexico), LGPD (Brazil) and Ley 1581 (Colombia) do not accept "the model missed it". The model still flags `unsubscribe_request` as a second opinion; when it catches something the regex did not, the contact is suppressed and a human is notified so the regex can be improved.

There is also one place where the model *could* have decided and does not: the model never chooses the action. It names an intent; a table names the action. This is less "intelligent" and much more predictable.

## The most important tradeoff

**Precision over coverage.** On the evaluation set, 5 of 15 replies go to a human under the default policy (mixed, unclear, injection, pricing outside ICP, the assisted referral); the set over-represents hard cases on purpose, so on real traffic the expectation is 15–25%, to be measured in shadow mode. A more aggressive design would automate more and be wrong more often, and a wrong handoff or a missed opt-out costs far more than a reviewed item.

The corollary is that the model's output is treated as a claim, not a fact: evidence must be verbatim, extracted emails and numbers must appear in the text, dates must be in the future, and one repair round is allowed before a human takes over. This costs a few lines of validation and buys the right to say "the system never invented a referral".

Related tradeoff: the policy is a YAML file rather than code. It loses type-checked flexibility and gains the ability for RevOps to change what is automated during a meeting. The `version` is stored on every decision so any past decision can be explained against the policy that produced it.

## The production risk I would address first

**Acting on stale state: contacting an account that is now a customer, or has an AE in an active deal, because our copy of the CRM lagged.**

The prototype mitigates it three ways: a versioned state that never rolls back, a re-read of the CRM before any irreversible action, and a rule that customers and AE-owned accounts are blocked regardless of what the reply says. In production the first thing I would do is make the CRM the single source of truth for those three fields (customer, open opportunity, owner) with a short cache TTL, add a per-account lock so two events on the same account cannot interleave, and put a metric with an alert on "contacts to existing customers", which must read zero every day.

## Smaller decisions worth recording

- **Idempotency key per action, not per event.** An event can legitimately produce two actions in the future; `event_id:action_type` keeps each one exactly-once.
- **Timeout after commit is modelled explicitly.** Most retry code treats a timeout as "failed, try again", which duplicates writes. Here it is `uncertain`, and reconciliation by key runs before any re-send.
- **Offline mode with recorded real responses.** Tests and the demo run without a key or network, and what they replay is what the model actually said, not hand-written stand-ins.
- **Structured outputs on the API side plus our own validators.** The schema guarantee removes a whole class of parsing errors; the semantic checks remove the class the schema cannot see (invented facts).
- **Effort set to `medium` on the interpreter.** The task is classification with extraction; more reasoning was not needed in the evaluation and would only add latency.
- **Freshness check tolerates a rate-limited CRM.** A 429 during the check logs and proceeds with local state rather than blocking; the alternative was to stall every handoff during a CRM incident.
- **`assisted` is the default for anything unknown.** An action missing from the policy file is treated as needing a human. Unknown means not automated.
