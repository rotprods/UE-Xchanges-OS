# UE-Xchanges-OS v0.7 — Execution Orchestrator Implementation Plan

## 1. Objective

Move the system from researched/verified opportunity intelligence to a controlled execution campaign that produces real, human-reviewed applications, submission receipts, organisation replies and current youth-work evidence.

The release does not add infrastructure for its own sake. It introduces one deterministic next-operation router, one campaign contract and one reply-to-decision protocol.

## 2. Definition of success

The campaign checkpoint closes only when all of the following are true:

- at least 2 applications are `SUBMITTED_WITH_RECEIPT`;
- at least 5 external organisation replies are ingested as sourced evidence;
- at least 1 genuine youth-facing collaboration is confirmed;
- at least 1 real delivery date is confirmed for Workshop V1 or an equivalent youth activity;
- GitHub, Drive CRM, dossiers, Todoist and git.local have zero known state divergence;
- all hard SLOs remain at zero.

## 3. Release boundary

### Included

- deterministic `next_execution_decision()`;
- deadline/receipt integrity;
- source/fact/external-response/public/private/policy/review precedence;
- execution-campaign configuration;
- reply-ingestion protocol;
- canonical integration of the temporary live-state override;
- Todoist W8 execution graph;
- Command Center in Drive;
- tests, CI and portable git.local handoff.

### Explicitly deferred

- probabilistic acceptance forecasting;
- browser automation for authenticated form submission;
- a new graph database/vector database;
- generic workflow-orchestration infrastructure;
- autonomous sending of final application answers;
- treating silence as consent or non-response as rejection.

## 4. Mandatory execution graph

```text
DISCOVERED
  -> SOURCE_VERIFIED
  -> FACT_CONFLICT_RESOLVED
  -> DEADLINE_VERIFIED
  -> EXTERNAL_CLARIFICATION_RESOLVED?
  -> PUBLIC_ELIGIBILITY_PASS
  -> PRIVATE_GATES_PASS
  -> FORM_CAPTURED
  -> AI_POLICY_RESOLVED
  -> HUMAN_WRITE_OR_REVIEW
  -> SUBMITTED
  -> RECEIPT_STORED
  -> OUTCOME_INGESTED
  -> LEARNING_POLICY_APPLIED
```

Alternate terminal states:

```text
BLOCKED_INELIGIBLE
BLOCKED_PRIVATE_GATES
HUMAN_WRITE_REQUIRED
DEADLINE_CROSSED_RECEIPT_UNKNOWN
CLOSED_NOT_SUBMITTED
WITHDRAWN
EXPIRED
```

No agent may skip a predecessor because an opportunity has a high Fit Score or urgent deadline.

## 5. Workstreams

### W0 — State reconciliation

- integrate `LIVE-STATE-OVERRIDE.json` into canonical `goal-state.json`;
- preserve Triglav as `DEADLINE_CROSSED_RECEIPT_UNKNOWN` until human evidence resolves it;
- reconcile current P0/P1 states across CRM, dossiers and Todoist;
- record sent communications and waiting-response states;
- delete the temporary override only after canonical integration.

**Checkpoint:** one canonical operational state.

### W1 — Reply-to-decision engine

For every tracked reply:

1. read the complete thread;
2. create a source/evidence event;
3. extract only explicit facts;
4. compare against current canonical facts;
5. resolve or preserve conflicts;
6. recompute eligibility/private/policy gates;
7. choose exactly one next operation;
8. update Drive CRM, dossier and Todoist;
9. persist material routing changes in GitHub.

**Checkpoint:** 5 replies ingested without unsupported inference.

### W2 — Application batch

Priority lanes:

1. Future Careers & AI;
2. Step Into Paralympics;
3. Building With Our Hands;
4. Thrive and Shine;
5. O-live T.R.E.E.S.;
6. Game of Nature.

For every lane:

- resolve source/deadline/profile/policy debt;
- verify private residence and real availability;
- capture exact questions and mandatory documents;
- map each criterion to private evidence;
- require human-owned final wording when policy is unknown or prohibits AI;
- human review;
- submit through the legitimate route;
- store receipt, timestamp and canonical form/source.

**Checkpoint:** 2 applications submitted with receipts.

### W3 — Credential acquisition

```text
OUTREACH_SENT
 -> REPLY_INGESTED
 -> DISCOVERY_CALL
 -> COLLABORATION_CONFIRMED
 -> ACTIVITY_ADAPTED
 -> DATE_CONFIRMED
 -> ACTIVITY_DELIVERED
 -> EVIDENCE_PACK_CAPTURED
 -> ORGANISER_FEEDBACK
 -> CURRENT_YOUTH_WORK_CONTEXT_REEVALUATED
```

Candidate routes: Euroaccion, 585m² Espacio Joven and Murcia Youth Service / Informajoven.

A proposal, session plan or booked conversation does not count as delivered youth-work evidence.

**Checkpoint:** 1 host and delivery date confirmed; L2 evidence only after real delivery.

### W4 — Outcome and learning integrity

- classify every outcome with causal strength;
- never learn negative application-quality heuristics from an unranked waitlist, high-competition rejection without feedback or no-response;
- retain organisation relationship and response-behaviour priors separately;
- postpone calibrated probability models until enough independent outcomes exist.

## 6. Agent responsibilities

| Agent | Output | Prohibited decision |
|---|---|---|
| Scout | new/changed source candidate | eligibility declaration |
| Verifier | sourced facts and conflicts | silent conflict resolution |
| Execution Router | one mandatory next action | free-form route choice |
| Eligibility Engine | PASS/FAIL/UNKNOWN | desirability ranking |
| Evidence Retriever | verified private proof | invented evidence |
| Application Strategist | criterion-to-proof map | final text when policy blocks it |
| Policy Guard | AI/submission mode | assuming absence of restriction = allowed |
| Receipt Guard | receipt/submission state | missing receipt = non-submission |
| Credential Builder | real activity path | credential self-declaration |
| Outcome Analyst | causal-strength update | invented rejection cause |

## 7. Daily operating loop

```text
09:00 discovery + deadline sweep
10:00 tracked-thread reply ingestion
12:00 active-lane source/form verification
15:00 human-gate and submission window
20:00 receipt/outcome integrity sweep
```

This schedule is an operational default, not an excuse to wait when a material deadline is closer.

## 8. QA / adversarial tests

The release must prove:

- crossed deadline plus missing receipt routes to receipt verification;
- explicit non-submission can close the node;
- public/private FAIL blocks regardless of score;
- organiser clarification precedes guessing eligibility;
- form capture precedes final-answer work;
- `AI_UNKNOWN` blocks final prose;
- `AI_FINAL_TEXT_PROHIBITED` routes to human writing;
- human review precedes submission;
- submitted-without-receipt is not complete;
- timezone-naive deadlines are rejected.

## 9. Human boundary

The human owner remains responsible for:

- confirming sensitive/private facts;
- confirming genuine availability and commitment;
- authenticating to portals/forms;
- reviewing or writing final application answers;
- clicking submit;
- supplying the submission receipt when connectors cannot observe it.

The OS prepares, verifies, routes and records. It does not impersonate the applicant or bypass access controls.
