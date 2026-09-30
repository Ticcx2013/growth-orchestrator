# Measurement plan: does the orchestrator create incremental qualified pipeline?

The objective is not more messages or more replies. It is more **AE-accepted opportunities per eligible account**, at equal or lower SDR cost, without hurting deliverability or compliance.

## Funnel

```
target accounts → eligible → contacted → replied → positive reply → meeting held → AE-accepted opportunity (SQO) → won
```

The orchestrator acts between *replied* and *AE-accepted*. It can also move *eligible → contacted* (faster, cleaner enrolment) and reduce leakage (replies that sit in an inbox for two days). It must not move *target → eligible*: that is a policy decision, and gaming it (loosening ICP) would inflate volume without pipeline.

## Design

**Randomized controlled experiment at the account level.** Randomizing contacts would contaminate: two people at the same company would be handled by different processes, and word travels. Stratify by country (MX/BR/CO), segment and company-size band so the arms are balanced where the base rates differ.

- **Arm A (control):** current process. SDRs read and triage replies, hand off manually.
- **Arm B (treatment):** orchestrator handles replies; SDRs only work the human-review queue.

Same sequences, same copy, same sending infrastructure, same AEs. The only difference is who triages and how fast.

**Primary metric:** share of eligible accounts with an **AE-accepted opportunity within 45 days** of first contact. AE acceptance (not "meeting booked") is the point where the pipeline is real and the AE, not the system, judges quality.

**Sample size.** Assume a 1.5% base rate and a target of a 20% relative lift (to 1.8%). Two-proportion test, α = 0.05 two-sided, 80% power: about **28,000 accounts per arm**. At ~50,000 target companies per month that is roughly 5–6 weeks of enrolment plus 45 days of maturation, so the read-out comes about three months after start. A larger true effect shortens this; a smaller one is probably not worth the operational change.

**Secondary metrics**
- Pipeline value ($) of accepted opportunities, winsorized at the 99th percentile (heavy tail).
- Speed to lead: minutes from reply to handoff or human touch (expected to collapse from hours to minutes).
- Meetings held per 100 replies.
- Cost per SQO, including model cost and SDR hours.
- SDR hours per 100 replies, measured from review-queue time.

**Guardrails (any breach pauses the treatment arm)**
- Spam complaint rate < 0.1%; bounce rate < 2%.
- Unsubscribe rate not above control by more than 20% relative.
- Rate of handoffs rejected by AEs not above control.
- Meeting no-show rate not above control.
- Contacts to existing customers or AE-owned accounts: **0**.
- Error rate in the 5% human sample of automated decisions < 3%.

## Reading the result

Report the absolute and relative lift with confidence intervals, per stratum, and the guardrail table. A lift on replies without a lift on AE acceptance means the system is moving the wrong things and should not ship. A flat primary metric with a large drop in SDR hours is still a positive result, but a different one (cost, not growth) and should be labelled as such.

## Rollout

1. **Shadow.** The orchestrator decides but does nothing; decisions are compared with what SDRs did. Target ≥ 95% agreement on 500+ replies before any automation.
2. **Assisted.** Every action is proposed in the review queue; humans click. Measures reviewer time and catches systematic errors.
3. **Autonomous by action class.** Low-risk first (`wait_until`, `nurture`), then `handoff_to_ae`, then `suppress` (already rule-driven), with `create_referral_contact` last. The policy file's `auto / assisted / off` switch is the rollout mechanism; no deploy is needed to move a class.

Run the experiment in step 3, once the system behaves in shadow and assisted modes. Randomizing earlier would measure a system we already know is not ready.
