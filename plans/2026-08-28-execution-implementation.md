# Implementation Plan — Application Execution Superwave

## Starting State

- UE-Xchanges-OS v0.6 + post-deadline execution checkpoint on `main`.
- 34 canonical opportunities.
- 13 application nodes after Step Into Paralympics dossier creation.
- 13+ organisation nodes.
- 12 private Evidence Nodes.
- 4 structured historical outcomes.
- 0 TOY-qualifying references.
- 11+ organisation-facing messages sent; replies pending at wave start.

## Phase 0 — State Convergence — COMPLETE

- GitHub/Drive/Todoist post-deadline state aligned.
- Triglav receipt ambiguity preserved.
- Thrive and Step original infopacks parsed.
- Sensitive-target conflict encoded rather than guessed.
- PR #9 merged after exact-head CI.

## Phase 1 — Execution Control Plane — IMPLEMENTED IN THIS PR

Deliverables:

- deterministic outbound-message SLA routing;
- deterministic submission/receipt state resolution;
- deterministic next-action gate for applications;
- execution-event JSON schema;
- regression coverage for silence != rejection and missing receipt != non-submission;
- canonical Execution Superwave protocol.

Exit criterion: exact-head CI succeeds on Python 3.11 and 3.12.

## Phase 2 — Reply Ingestion — ACTIVE

For Ticket2Europe/ORAMA, YUPI, Papaya, BreGal, Thrive coordinator, Step coordinator, Digi-Hack, AREAAA, Euroaccion, 585m2 and Murcia Youth Service:

1. read complete thread;
2. store raw message ID/thread ID privately;
3. extract explicit source claims only;
4. resolve conflicts;
5. update Organisation/Application/Opportunity nodes;
6. choose one mandatory next action;
7. label thread `UEX/Reply Ingested` after processing.

Exit criterion: every reply is reflected in CRM and no reply remains only in Gmail.

## Phase 3 — P0/P1 Submission Factory — ACTIVE

### Step Into Paralympics

Deadline: 29 Aug. Resolve target profile + route + policy. Submit only if private gates pass.

### Building With Our Hands

Deadline signal: 31 Aug. Production pack exists. Await YUPI/policy confirmation; then human-owned CV/letter/video -> review -> send -> receipt.

### Future Careers & AI

Form/infopack/date captured. Await host/sending-route/policy clarification. Resolve private residence and availability. Human answer worksheet -> review -> form -> receipt.

### Thrive and Shine

Original infopack captured. Await exact cutoff/form/policy. Map exact questions -> human review -> submit.

### O-live T.R.E.E.S.

Recover Spanish form/slots and AI policy; exploit direct OliVideos contribution without treating media as eligibility.

### Game of Nature

Wait for Papaya answer on current profile criterion; no false current youth-work claim.

Exit criterion: every node becomes `SUBMITTED_CONFIRMED`, `BLOCKED`, `CLOSED`, or a precisely named external/private gate.

## Phase 4 — Credential Acquisition — ACTIVE

1. ingest responses from Murcia youth organisations/services;
2. agree a real host, audience, date and safeguarding conditions;
3. tailor Workshop V1;
4. deliver;
5. capture L2 evidence pack;
6. request organiser feedback/reference;
7. re-evaluate current youth-work context;
8. pursue co-facilitation and qualifying international trainer responsibility later.

Exit criterion: one delivered activity plus independent organiser evidence.

## Phase 5 — Outcome & Portfolio Loop

- capture receipts and results;
- preserve waitlist rank semantics;
- resolve mutually exclusive accepted opportunities before commitment;
- update organisation relationship/response priors;
- no probability model until sufficient independent outcomes exist.

## Checkpoints

- C1: exact-head CI green for Execution Control Plane.
- C2: first two submission receipts stored.
- C3: five replies ingested.
- C4: first youth-facing collaboration confirmed.
- C5: first L2 evidence pack complete.
- C6: score/route review using real outcomes, not intuition.
