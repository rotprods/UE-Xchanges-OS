# UE-Xchanges-OS — RuntimeGraph V2.1 Dispatch Cycle Close

Checkpoint: `2026-09-02 00:30 Europe/Madrid`

Purpose: make the completed RuntimeGraph V2.1 dispatcher cycle and its current executable frontier recoverable without this chat.

## 1. Authority and captured base

Authority order remains:

`official source / organiser confirmation / authoritative receipt > private Drive CRM + Agent_Event_Bus > active LIVE-STATE-OVERRIDE.json > GitHub versioned contracts/checkpoints > RuntimeGraph/Notion/Todoist/HubSpot projections > chat memory`.

Captured GitHub base before this recovery seal: `d72369366396e97cf532f9c7a462df3cfdc9b79e`.

Canonical private CRM: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`.

RuntimeGraph V2 Command Center: `1OtSLFI4VHW6aSne1YjtRykRsN4j4G4OcEGSCXVDLwbM`.

RuntimeGraph V2.1 dispatcher release: `6c23c9b6a70f33a7cb1eb780c54e49ebf5cf0d16`.

The immediately preceding continuity seal raised canonical opportunity count to **176** and preserved `Mass_Apply_Queue` at **164**; this checkpoint does not roll that state back.

## 2. Mandatory reconstruction performed before mutation

Before writing this checkpoint the closer reconstructed:

- current GitHub `main`;
- latest available `Agent_Event_Bus` tail;
- current `Work_Leases`;
- RuntimeGraph V2 `Command_Center`;
- `Human_Now`;
- `Agent_Next`;
- `Receipt_Inbox`;
- `Dispatcher_State`;
- `Source_Cursors`;
- `Dead_Letters`.

The earlier `continuity_recovery` lease `LSE-UEX-HANDOFF-20260902T002030-30` was observed **RELEASED** before this recovery-file lease was acquired.

A fresh bounded lease was then acquired:

- session: `SES-UEX-CHATGPT-20260902T002900-32`
- agent: `AGT-RUNTIMEGRAPH-HANDOFF-SEALER`
- lease: `LSE-UEX-RG21-REPO-HANDOFF-20260902T002900-32`
- start event: `EVT-20260902T002900-RGHS-001`
- lease event: `EVT-20260902T002900-RGHS-002`
- scope: only `STATE.md`, `HANDOFF.md`, `LIVE-STATE-OVERRIDE.json`, `CHANGELOG.md` and this checkpoint.

It explicitly yields RuntimeGraph V2.2 adapter/projection paths and `agent_context/**`.

## 3. Completed RG2.1 dispatcher cycle

Cycle session: `SES-UEX-AUTO-20260901T233539-28`.

Causal events:

- `EVT-20260901T233539-DSPC-001` — session started.
- `EVT-20260901T233539-DSPC-002` — bounded dispatch lease acquired.
- `EVT-20260901T233539-DSPC-003` — explicit Step Into Paralympics normalized official-source observation applied to exact `application_id=app-step-paralympics-v1`.
- `EVT-20260901T233800-DSPC-004` — Applications projection column-offset incident corrected immediately; no payment/submission/receipt state changed.
- `EVT-20260901T234155-DSPC-005` — Human Frontier changed `3 → 4`, Step added.
- `EVT-20260901T234155-DSPC-006` — dispatch cycle completed.
- `EVT-20260901T234155-DSPC-007` — dispatch lease released.
- `EVT-20260901T234155-DSPC-008` — session completed/handoff.

Cycle result:

```text
gmail_new_relevant = 0
receipt_confirmed = 0
form_gateway_safe_events = 0
official_material_events = 1
human_frontier_before = 3
human_frontier_after = 4
dead_letters = 0
projection_fix_applied = true
```

No payment, authentication, credential/OTP/cookie entry, external PREFILL certification, external submit or irreversible application submission occurred.

## 4. Step Into Paralympics — explicit facts only

Exact mapping:

- application ID: `app-step-paralympics-v1`
- opportunity ID: `doc1-step-paralympics`

Normalized facts applied by the cycle:

- official Google Form was live when reverified at `2026-09-01T23:35:39+02:00`;
- organiser had explicitly extended the deadline date to `2026-09-01`;
- exact closing time was **not known**;
- the live form still contained stale `18/08/2026` deadline text;
- the live form still contained stale `2025` transport dates;
- written organiser clarification of correct 2026 transport dates had **not** arrived;
- receipt = `false`;
- submission = `false`.

Deterministic dispatcher ingress key: `rg21ing_914e768c0e217afd914a7294658c2f50659e118eda04d1be2e2efa2b1bf887f3`.

State effect:

- human application action became READY/urgent;
- waiting for transport-date clarification became **non-blocking for the application**;
- travel purchase remains **blocked** until written 2026 transport-date clarification.

No eligibility, submission or receipt status was inferred from raw prose.

## 5. Human Frontier at cycle close

### 1 — Step Into Paralympics

`app-step-paralympics-v1`

Human-only action: complete private/applicant-owned fields/text, personally submit, capture confirmation/receipt. Travel booking remains blocked separately.

### 2 — COMPASS

`app-compass-bregal-2026-v1`

Human-only action: decide/execute €30 payment, capture receipt, then Tally. Selection/acceptance email is not payment receipt and does not mean `CONFIRMED`.

### 3 — CIVIS LAB

`app-salto-listing-2026-08-31-civis-lab-v1`

Human-only action: approve/decline; if approved, €50 payment and proof. Travel remains separately gated.

### 4 — SABER — Soilpunk Youth Exchange

`app-non_salto-saber-2026-v1`

Human-only action: login, private-field review, irreversible submit and receipt capture under the host-authorised late route.

## 6. Agent Frontier snapshot

Top safe reversible/evidence actions in `Agent_Next` after the completed cycle:

1. Step Into Paralympics — ingest organiser transport-date reply when received; non-blocking for application.
2. I-PLAY — ingest Ticket2Europe reply when received.
3. Game of Nature — ingest group-leader follow-up while preserving participant-route separation.
4. Building With Our Hands — verify receipt or authorised late route after deadline.
5. Receipt sweep — after human actions, bind candidate evidence to exact application/submission identity.

CONVIVIAL FOODSCAPES remains a separate P1 hard-gate lane: verify AI policy and full-November availability before Mass Apply enqueue or preparation.

## 7. Source cursors

Captured from RuntimeGraph V2 `Source_Cursors` after the cycle:

| Source ID | State | High watermark | Last item | Last observed | Revision | Meaning |
|---|---|---:|---|---|---:|---|
| `gmail:organiser-replies` | ACTIVE | `0` | `1a05eb5b1861284d` | `2026-09-01T22:42:26+02:00` | `1` | CIVIS evidence already normalized; late unique Gmail events remain processable. |
| `receipt:reconciler` | BOOTSTRAP | `0` | `none` | `2026-09-01T22:30:00+02:00` | `0` | Confirmed current-wave receipts = 0. |
| `form:gateway` | BOOTSTRAP | `0` | `none` | `2026-09-01T22:30:00+02:00` | `0` | External PREFILL/Submit not certified. |
| `source:official` | ACTIVE | `0` | `step-form-live-20260901` | `2026-09-01T23:35:39+02:00` | `1` | Step form-live observation already applied. |

Cursors are ingestion high-watermarks, not authority. They must move monotonically; late unique events may still be processed idempotently.

## 8. Receipt Inbox and Dead Letters

`Receipt_Inbox`:

- confirmed current-wave receipts: **0**;
- COMPASS: `PENDING_HUMAN_PAYMENT_RECEIPT`;
- CIVIS LAB: `PENDING_HUMAN_PAYMENT_PROOF`.

`Dead_Letters`:

- current count: **0**.

A future poison/unroutable normalized event receives at most three attempts of the same transient strategy, then moves to Dead Letters without raw prose/secrets. Human notification is required only when that dead letter needs attention.

## 9. Dispatcher invariants

- `AT_LEAST_ONCE_PLUS_IDEMPOTENCY`; never claim exactly-once.
- deterministic ingress/idempotency keys.
- normalize state-changing observations only with exact application/opportunity mapping.
- raw prose does not establish eligibility, submission, receipt or confirmation.
- process only source changes after stored cursors, while accepting late unique idempotent events.
- apply only the affected application subgraph.
- append safe EventBus evidence.
- advance cursors monotonically.
- recompute Human/Agent frontiers after state-changing evidence.
- retry same transient strategy at most 3 times before dead-lettering.
- `SubmissionAttempt != SubmissionReceipt`.
- no `APPLICATION_SUBMITTED` without authoritative confirmation bound to exact application/submission identity.

## 10. Irreversible-action boundary

Agents must never:

- pay;
- authenticate or complete MFA/CAPTCHA;
- enter credentials, OTPs or cookies;
- export credentials/cookies/storage;
- certify an external provider PREFILL target from untrusted evidence;
- perform irreversible Submit;
- infer private/sensitive applicant values.

Those boundaries remain true even though local Browser Worker/Relay/Stack infrastructure exists.

## 11. Concurrent leases observed at repository-seal start

Captured at approximately `2026-09-02 00:30 Europe/Madrid`:

- `LSE-UEX-RUNTIMEGRAPH-ADAPTERS-20260902T001630-27` — ACTIVE at capture; owns RuntimeGraph V2.2 adapter/projection implementation paths and Command Center projection tabs. This recovery seal does not touch them.
- `LSE-UEX-AGENT-CONTEXT-20260902T002200-31` — ACTIVE at capture; owns only `github:agent_context/**`. This recovery seal does not touch it.

A future agent must re-read `Work_Leases`; do not treat this captured snapshot as current truth after time advances.

## 12. Recovery sequence for the next zero-context agent

1. Read current GitHub `main` and record the exact SHA.
2. Read `goal.md`, `LIVE-STATE-OVERRIDE.json`, `STATE.md`, `AGENTS.md`, `HANDOFF.md`.
3. Read `docs/MULTI_AGENT_CONTROL_PLANE.md`, `docs/RUNTIMEGRAPH_V2_CLOSED_LOOP.md`, `docs/RUNTIMEGRAPH_V2_1_EVENT_DISPATCHER.md`, `docs/RUNTIMEGRAPH_FORM_GATEWAY.md`, `RUNBOOKS/RUNTIMEGRAPH_RECOVERY.md`.
4. Read this checkpoint and the CONVIVIAL checkpoint.
5. Read private CRM `Agent_Sessions`, active `Work_Leases` and EventBus after the public checkpoint watermark.
6. Read RuntimeGraph V2 Command Center, `Source_Cursors`, `Receipt_Inbox` and `Dead_Letters`.
7. Reconcile any newer V2.2 source-adapter/self-heal release before writing projection tabs.
8. Read only new Gmail organiser/receipt, Form Gateway safe events and authoritative official-source changes after cursors.
9. Normalize only explicit exact-ID facts; never infer eligibility/submission/receipt from prose.
10. Dispatch idempotently, update only affected subgraphs, append evidence, advance cursors and recompute frontiers.
11. Notify the human only on material Human Frontier, authoritative receipt, P0/P1 blocker/status or human-attention dead-letter deltas.

## 13. Chat closure condition

This chat is no longer required once this checkpoint and the associated recovery-file updates are merged to `main`, the resulting main SHA is recorded in `Agent_Event_Bus`, and `LSE-UEX-RG21-REPO-HANDOFF-20260902T002900-32` is released.
