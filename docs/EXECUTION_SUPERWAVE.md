# Execution Superwave v1

## Mission

Convert the existing opportunity/evidence graph into verified submissions, organisation relationships and current youth-work evidence. Engineering is frozen unless execution reveals a new state-machine or safety requirement.

## North Star

`accepted_high_value_funded_opportunities / human_application_hours`

## Superwave Definition of Done

- at least 2 applications submitted with stored receipts;
- at least 5 organisation replies ingested as evidence events;
- 0 known eligibility false-passes;
- 0 duplicate submissions;
- 0 fabricated claims;
- 0 known AI-policy violations;
- 1 genuine youth-facing collaboration confirmed;
- 1 real activity date agreed for Workshop V1 or equivalent;
- GitHub, Drive CRM, Todoist and git.local converge on the same state.

## Mandatory Execution Graph

```text
CANDIDATE
 -> SOURCE_VERIFIED
 -> ELIGIBILITY_PASS
 -> PRIVATE_GATES_RESOLVED
 -> FORM_CAPTURED
 -> AI_POLICY_RESOLVED
 -> ASSETS_READY
 -> HUMAN_REVIEW
 -> SUBMITTED
 -> RECEIPT_CAPTURED
 -> OUTCOME
 -> LEARNING_EVENT
```

Alternate routes:

```text
MESSAGE_SENT -> REPLY_INGESTED -> GATES_REEVALUATED
MESSAGE_SENT -> FOLLOW_UP_DUE -> ONE_FOLLOW_UP
MESSAGE_SENT -> DEADLINE_CRITICAL -> LEGITIMATE_DIRECT_ROUTE
DEADLINE_PASSED + NO RECEIPT -> RECEIPT_UNKNOWN (never guessed)
SENSITIVE_TARGET_CONFLICT -> DIRECT_CLARIFICATION (never inferred)
```

## Active Workstreams

### W8A — Reply Ingestion

Twice daily, search the active organisation threads. A reply becomes:

`raw email -> source evidence -> extracted claims -> provenance -> fact conflict resolution -> CRM update -> next mandatory action`.

Never treat silence as rejection. Never send duplicate follow-ups inside the SLA.

### W8B — Deadline Applications

1. Step Into Paralympics — 29 Aug; resolve target-profile conflict, Spanish route and policy.
2. Building With Our Hands — 31 Aug; confirm call/policy, then produce human-owned CV/letter/video and submit.
3. Future Careers & AI — form captured; resolve policy/private gates and submit while places remain.
4. Thrive and Shine — infopack captured; resolve exact cutoff/form/policy and submit.
5. O-live T.R.E.E.S. — recover Spanish route/slots/policy.
6. Game of Nature — resolve current-profile criterion with Papaya.

### W8C — Submission Evidence

Every submission must create:

- submission timestamp;
- canonical form/portal URL;
- receipt/email/screenshot/reference;
- exact role;
- human minutes;
- portfolio conflict edges;
- follow-up date.

No receipt plus a crossed deadline becomes `DEADLINE_PASSED_RECEIPT_UNKNOWN`, not `CLOSED_NOT_SUBMITTED`.

### W8D — Credential Acquisition

`outreach -> collaboration confirmed -> activity designed -> delivered -> evidence pack -> organiser feedback/reference -> current-context re-evaluation`.

The first target is L2/L3 evidence. It does not become a TOY reference unless official criteria are independently satisfied.

### W8E — Outcome Learning

Use causal-strength policies only. Waitlists, high-competition rejection, no-response and specific feedback remain different outcomes.

## Human Gates

Only the applicant can finally confirm:

- legal/current residence where requested;
- real-world availability and travel commitment;
- sensitive attributes voluntarily disclosed where relevant;
- truth of subjective motivation;
- authenticated portal/form submission;
- final wording where AI is prohibited or unknown;
- receipt/status not visible through connected sources.

## Agent Responsibilities

- Scout: new/changed opportunities only.
- Verifier: original sources, deadlines, forms and policy.
- Reply Ingestor: organisation messages -> provenance events.
- Eligibility Engine: deterministic hard gates.
- Application Strategist: criterion -> evidence -> contribution.
- Human-Gate Guard: private/subjective confirmations.
- Submission Auditor: receipts, duplicates and timestamps.
- Credential Builder: real youth-facing delivery path.
- Outcome Analyst: causal-strength learning.

## Cadence

- 09:00 Europe/Madrid — opportunity/deadline sweep.
- 09:30 — organisation reply ingestion.
- 18:00 — second reply sweep and next-day deadline review.
- T-72h / T-24h / T-6h — deadline re-verification from original source.
- After every submission — receipt capture immediately.

## Engineering Freeze Rule

Create code only when real execution exposes a missing state, invariant or deterministic decision. Do not add infrastructure for hypothetical scale.
