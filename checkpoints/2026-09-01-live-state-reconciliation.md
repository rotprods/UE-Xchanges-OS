# UE-Xchanges-OS — 2026-09-01 Live State Reconciliation

Checkpoint: 2026-09-01 15:39 Europe/Madrid

## Purpose

Publish a bounded, evidence-safe runtime checkpoint because `goal-state.json` on `main` is a 31 August release snapshot and is materially behind the private Drive CRM.

This checkpoint does **not** redesign architecture, submit external forms, execute payments, invent receipts, or copy private applicant/payment data into GitHub.

## Authority

Current precedence remains:

1. official source / authorised form / organiser confirmation / submission receipt;
2. active `LIVE-STATE-OVERRIDE.json`;
3. private Drive CRM + Agent Event Bus;
4. `goal-state.json` release snapshot;
5. Todoist / Notion / HubSpot projections.

Private CRM: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`

Session: `SES-UEX-CHATGPT-20260901T144200-11`

State-sync lease: `LSE-UEX-PUBLIC-STATE-20260901T153900-11`

Event watermark at override generation: `EVT-20260901T153900-STATE-009`

## Reconciled runtime

- Opportunities: **170** canonical IDs.
- Application nodes: **159**.
- Mass-apply queue: **159**.
- Organisations: **26**.
- Outcome history rows: **6**.
- Event-bus events at state-sync start: **128**.
- Submission receipts: **0**.
- Historical applications proven by later organiser outcome: **1** (`COMPASS`; original submitted timestamp/receipt still unreconstructed).
- Verified TOY-qualifying trainer references: **0**.
- Open paid trainer/facilitator calls crossing the alert threshold: **0**.
- Telegram unique unresolved corpus: **60**.

## Projection reconciliation

### Notion

W9.35 is complete.

- Opportunities projection: `170/170` unique canonical IDs.
- Applications projection: `159/159` unique application IDs.
- Organisations projection: `26/26` materialised.
- Drive remains canonical; Notion write-back remains prohibited.

### HubSpot

Relationship graph remains write-gated.

- Company / Contact / Deal read: AVAILABLE.
- Company / Contact / Deal write: REQUIRES_REAUTHORIZATION.
- Exact-name dedupe of ten hot organisations returned zero existing Company records.
- Deal remains reserved for genuine paid trainer/facilitator/consulting engagements, never participant mobility applications.

### Todoist

- W9.35 full backfill: completed.
- W10 HubSpot write-lane gate: open.
- Human P0 gates remain explicit tasks; Todoist is not submission evidence.

## P0 frontier

### COMPASS

Project: `2025-3-PT02-KA152-YOU-000370370`

State: `SELECTED_EMAIL_ACCEPTED_PAYMENT_TALLY_PENDING`.

BreGal selected the applicant after a withdrawal from first position on the waiting list. The place was explicitly accepted by email on 1 September. BreGal still requires the human contribution/payment receipt and final Tally before it considers the candidature accepted/finalised.

Do not mark `CONFIRMED` before payment + Tally evidence.

### Step Into Paralympics

State: participant eligibility PASS; correct Spain direct-form route confirmed; deadline extended to 1 September; exact cutoff not supplied.

Organiser confirms mixed disabled/non-disabled participants and no youth-work requirement for normal participants. AI is not prohibited, but genuine personal answers are preferred.

A cutoff/form-validity follow-up was sent. No receipt exists.

### CIVIS LAB

State: eligibility PASS / human payment gate.

EUROACTIVA-T confirms no separate Spanish application form. After the human EUR 50 payment and proof, the applicant is included in the participant list. Force-majeure refund and the travel-authorisation-before-ticket sequence are confirmed.

No payment was executed by the agent.

### SABER / Soilpunk

State: host-authorised late application after cancellation in the Spanish group.

The form remains the route and the host explicitly permits AI if useful. Human form submission + receipt remains mandatory.

### Game of Nature

State: participant route supported by organiser; group-leader lane pending exact duties/minimum experience/current slots/AI policy.

Follow-up resent 1 September. Do not claim official group-leader experience.

### I-PLAY

State: Ticket2Europe directly confirms places available; public listing is Braga, 27 October–5 November 2026, 7 participants + 1 group leader.

Follow-up sent for current role slots, route, effective deadline, funding and AI policy. No submission yet.

### Oriel 53967

The official 1 September 15:00 deadline crossed. No connector-visible receipt exists. State is `DEADLINE_PASSED_SUBMISSION_UNVERIFIED`, not a fabricated `NOT_SUBMITTED`; human receipt evidence can still prove a pre-cutoff manual submission.

## Paid trainer/facilitator watch

SALTO Calls for Trainers was rescanned on 1 September at 15:35 Europe/Madrid.

No new open trajectory-changing paid call was found.

The existing Inspirational Event call still states that separate calls are planned in September 2026 for:

- 2 plenary facilitators;
- 5 co-creation-lab facilitators.

These are **not yet open calls** and must not be treated as applyable employment.

## Ticket2Europe Italy watch

Ana del Valle stated that another late-September Italy project would be published on 1 September. A follow-up asks for the link. The public site also exposes an older-looking `LEAD RIGHT!` listing in Alatri (24 September–2 October), but current evidence does not prove it is the newly promised project. Do not silently merge the identities.

## Safety / evidence invariants

- `ROUTE_QUERY_SENT != APPLICATION_SUBMITTED`.
- `ELIGIBLE != SELECTED`.
- `INVITED_TO_APPLY != ACCEPTED`.
- `PAYMENT_REQUIRED_FOR_PLACE != CONFIRMED`.
- A later selection email can prove a historical application existed, but it does not reconstruct the original submit timestamp or receipt.
- No sensitive profile attribute may be inferred.
- No private payment coordinates are stored in this public checkpoint.

## Exit criteria

This override/checkpoint may be retired only when:

1. the same evidence-backed runtime is integrated into `goal-state.json`;
2. exact-head CI succeeds;
3. the state is merged to `main`;
4. Drive Dashboard/public state references are reconciled to the resulting main SHA;
5. no projection-divergence gate remains open.
