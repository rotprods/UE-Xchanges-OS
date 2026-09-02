# UE-Xchanges-OS — HANDOFF

Checkpoint: 2026-09-02 00:30 Europe/Madrid

Purpose: allow a zero-context agent to recover current execution without relying on chat memory.

> **Bootstrap overlay:** this file is a watermarked handoff snapshot. The mandatory cross-session bootstrap contract is `AGENTS.md` + `agent_context/bootstrap_manifest.json`; durable semantic memory is `MEMORY.md`. Newer Drive/Event Bus/official evidence and later checkpoints override snapshot details below.

## Cold start — mandatory order

1. Read current GitHub `main` and record its SHA.
2. Read `goal.md`.
3. Read `AGENTS.md`.
4. Read `MEMORY.md`.
5. Read `agent_context/bootstrap_manifest.json` and follow its required public/private read sets.
6. Read active `LIVE-STATE-OVERRIDE.json`.
7. Read current `STATE.md` and this `HANDOFF.md`.
8. Read `agent_context/README.md`, `context.md`, `progress.md`, `checkpoints.md`, `session.md`, `runtimegraph.md`, `knowledge.md` and `recovery.md` as watermarked navigation.
9. Read `docs/MULTI_AGENT_CONTROL_PLANE.md` and `docs/AGENT_BOOTSTRAP_PROTOCOL.md`.
10. Read current RuntimeGraph/Form Gateway docs and the newest relevant checkpoint.
11. Read private Drive CRM `Context_Registry`, `Agent_Sessions`, **currently unexpired** `Work_Leases`, and the tail of `Agent_Event_Bus`; never reuse an old session ID.
12. Read RuntimeGraph V2 Command Center tabs `Command_Center`, `Human_Now`, `Agent_Next`, `Receipt_Inbox`, `Dispatcher_State`, `Source_Cursors` and `Dead_Letters`.
13. Read only source deltas after stored cursors; late unique events may still be processed idempotently.
14. Register a fresh Session ID and emit `SESSION_STARTED`.
15. Emit `BOOTSTRAP_CONTEXT_LOADED` with manifest version, observed main SHA, context ID, read-set refs/hash, private event watermark and lease-scan timestamp.
16. Refresh unexpired leases + Event Bus tail immediately before mutation.
17. Only after the bootstrap acknowledgement may the session acquire a fresh narrow lease; runtime-action mutation requires the exact action lease/fencing token.
18. Persist external evidence/gate changes to canonical Drive evidence first, then apply/recompute only the affected application subgraph and downstream projections.

A registered session without `BOOTSTRAP_CONTEXT_LOADED` is read-only. `BOOTSTRAP_CONTEXT_LOADED` must precede `LEASE_ACQUIRED` for compliant writers.

## Canonical resources

- Drive CRM: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`
- Drive handoff folder: `1T8EW70y2Clfhnug3vRqRhtTtqDqvQPid`
- RuntimeGraph V2 Command Center: `1OtSLFI4VHW6aSne1YjtRykRsN4j4G4OcEGSCXVDLwbM`
- Legacy RuntimeGraph v1 read model: `16QcHOWoBD1ixstPkhivftuyqmQdhtZj6`
- Legacy machine snapshot: `1iVyNAZWmURTdK8wZyYjYxyYDh9Djik3P`
- Private recovery pack: `19tM23N37cqweaWPSoVMxEECZhfOSrEJPGj_nRJB71q4`
- Todoist project: `6hCjVwH7R6hq49G3`
- Todoist W9 control: `6hPPRQrhG6cmhh3V`
- GitHub repo: `rotprods/UE-Xchanges-OS`

## Snapshot semantics

All counts, frontiers, cursors and concurrent-lease statements below are historical values captured at the checkpoint time. **Never treat them as current without refreshing Drive/Event Bus/current main.**

## Aggregate state at checkpoint

- Canonical opportunities: **176**.
- Mass Apply / application nodes: **164**.
- Organisations: **30**.
- Current-wave authoritatively confirmed receipts: **0**.
- Telegram unique unresolved: **60** / source-access blocked.

`non_salto-convivial-foodscapes-2026` was the 176th canonical opportunity at this checkpoint. It is P1, deadline `2026-09-15`, state `POLICY_GATE_PENDING`, and intentionally remained outside `Mass_Apply_Queue` while `AI_POLICY_UNKNOWN` and `FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED` were unresolved. Read newer Event Bus/opportunity state before acting.

## RuntimeGraph V2.1 — checkpoint runtime

Dispatcher release SHA: `6c23c9b6a70f33a7cb1eb780c54e49ebf5cf0d16`.

Completed material cycle:

- session: `SES-UEX-AUTO-20260901T233539-28`
- completion event: `EVT-20260901T234155-DSPC-008`
- Human Frontier: **3 → 4**
- confirmed receipts: **0**
- dead letters: **0**
- Gmail new relevant observations: **0**
- safe Form Gateway observations: **0**
- official-source material observations: **1**
- projection repair: `EVT-20260901T233800-DSPC-004`, immediate column-offset correction, no domain/payment/submission/receipt state change.

Delivery contract:

`AT_LEAST_ONCE + DETERMINISTIC_IDEMPOTENCY + MONOTONIC_CURSORS + MAX_3_SAME_STRATEGY_RETRIES + DEAD_LETTER_ISOLATION`.

Never claim exactly-once semantics.

### Source cursors at cycle close

| Source | State | Last item | Last observed | Revision |
|---|---|---|---|---|
| `gmail:organiser-replies` | ACTIVE | `1a05eb5b1861284d` | `2026-09-01T22:42:26+02:00` | `1` |
| `receipt:reconciler` | BOOTSTRAP | `none` | `2026-09-01T22:30:00+02:00` | `0` |
| `form:gateway` | BOOTSTRAP | `none` | `2026-09-01T22:30:00+02:00` | `0` |
| `source:official` | ACTIVE | `step-form-live-20260901` | `2026-09-01T23:35:39+02:00` | `1` |

Cursors are ingestion high-watermarks, not source authority. Do not move them backwards; late unique events may still apply if their deterministic idempotency key has not been processed.

## Human Frontier — checkpoint projected READY set

1. `app-step-paralympics-v1` — **Step Into Paralympics**: complete private/applicant-owned fields/text personally, submit personally, capture confirmation/receipt. Form reverified live at `2026-09-01T23:35:39+02:00` on organiser-confirmed extension date `2026-09-01`; exact close time unknown. Stale deadline and `2025` transport-date text remained in form. Application action was READY; travel booking remained blocked pending written 2026 transport-date clarification. No submission/receipt existed at checkpoint.
2. `app-compass-bregal-2026-v1` — **COMPASS**: decide/execute human €30 payment, capture receipt, then complete Tally. Not confirmed at checkpoint.
3. `app-salto-listing-2026-08-31-civis-lab-v1` — **CIVIS LAB**: human approve/decline; if approved, €50 payment and proof. Travel sequence separately gated.
4. `app-non_salto-saber-2026-v1` — **SABER — Soilpunk Youth Exchange**: human login, review private fields, irreversible submit, capture receipt under host-authorised late route.

Human-only: authentication/MFA/CAPTCHA, identity/sensitive values, payment, applicant-owned final wording where required, personal video and irreversible submit unless a later versioned capability contract explicitly changes a specific boundary.

## Agent Frontier — checkpoint reversible/evidence work

1. Step Into Paralympics — ingest organiser transport-date reply when received; this reply was non-blocking for the application but blocks travel purchase.
2. I-PLAY — ingest Ticket2Europe route/details reply when received.
3. Game of Nature — ingest group-leader follow-up; do not contaminate the proven participant route with unproven GL status.
4. Building With Our Hands — verify authoritative receipt or authorised late route after deadline.
5. Receipt sweep — after human actions, bind candidate confirmations to exact `application_id` and submission identity before any submitted/receipt transition.
6. CONVIVIAL FOODSCAPES — resolve AI-policy evidence and full-November availability before any application preparation/queue promotion.

## Runtime action protocol

```text
READ CURRENT MAIN / BOOTSTRAP CONTRACT / CONTROL-PLANE WATERMARK
→ READ UNEXPIRED LEASES
→ READ COMMAND CENTER + SOURCE CURSORS + DEAD LETTERS
→ READ ONLY NEW SOURCE DELTAS
→ NORMALIZE EXPLICIT FACTS WITH EXACT IDS
→ DEDUPE BY DETERMINISTIC IDEMPOTENCY KEY
→ REGISTER NEW SESSION
→ BOOTSTRAP_CONTEXT_LOADED
→ ACQUIRE NARROW LEASE
→ APPLY ONLY AFFECTED SUBGRAPH/SCOPE
→ VERIFY EVIDENCE / READ BACK
→ APPEND EVENTBUS EVIDENCE
→ ADVANCE CURSOR MONOTONICALLY
→ RECOMPUTE HUMAN/AGENT FRONTIERS
→ RELEASE LEASE
```

Retry the same transient strategy at most 3 times; then dead-letter. Notify Roberto only if Human Frontier changes, a receipt becomes authoritatively confirmed, a P0/P1 status/blocker changes materially, or a dead letter needs human attention.

## Hard evidence rules

- Raw prose is not a state transition.
- Normalize state-changing evidence only with exact `application_id` or exact `opportunity_id` mapping.
- `ROUTE_QUERY_SENT != APPLICATION_SUBMITTED`.
- `ELIGIBLE != SELECTED`.
- `INVITED_TO_APPLY != ACCEPTED`.
- `PAYMENT_REQUIRED_FOR_PLACE != CONFIRMED`.
- `CLICK_SUBMIT != SUBMITTED_CONFIRMED`.
- `SubmissionAttempt != SubmissionReceipt`.
- No `APPLICATION_SUBMITTED` or receipt state without authoritative confirmation bound to the exact application/submission identity.
- Latest authoritative organiser/official-source evidence overrides older summaries.
- Todoist/Notion/HubSpot/RuntimeGraph are projections, never receipt authority.

## Form / browser boundary

RuntimeGraph decides what action is ready. Form Gateway represents typed fields/ownership/auth/attempts/receipts. Browser Worker/Relay/Stack are local execution infrastructure only.

Capability state is versioned and must be read from current code/recovery artifacts. Authentication never implies PREFILL; PREFILL never implies Submit.

At this checkpoint the hard ceiling remained:

- no payment;
- no credential/cookie/storage export;
- no external provider PREFILL certification;
- no irreversible Submit by agent;
- no inference of sensitive/private applicant values.

A later versioned contract may promote a bounded capability only after its own gate/CI/evidence; this historical handoff does not grant it.

## CONVIVIAL FOODSCAPES P1 at checkpoint

- ID: `non_salto-convivial-foodscapes-2026`
- role: visual artist
- host/location: Quinta das Relvas x CONVIVIUM, Branca, Portugal
- residency: `2026-11-01` → `2026-11-30`
- deadline: `2026-09-15`
- Spain gate: PASS
- hard gates at capture: `AI_POLICY_UNKNOWN`, `FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED`
- next gate: `VERIFY_AI_POLICY_AND_NOVEMBER_AVAILABILITY_THEN_PREPARE`
- Mass Apply at capture: not enqueued
- official source: `https://quintadasrelvas.pt/convivialfoodscapes/`

Do not infer these gates are still unresolved; refresh current evidence first.

## Concurrent work at this seal

At `2026-09-02 00:30 Europe/Madrid` two disjoint leases were observed active. This is historical concurrency context only.

Every successor must re-read `Work_Leases` and use **currently unexpired** overlapping leases as the write fence.

## Projection status

- Drive CRM + Event Bus: canonical operational truth/provenance.
- RuntimeGraph V2 Command Center: derived execution frontier.
- Notion: reconstructible projection.
- Todoist: human/control action projection only; never receipt evidence.
- HubSpot: organisation/contact/paid-relationship graph only; participant mobility applications are never Deals.
- TickTick: daily-focus mirror only.
- `MEMORY.md`: slow-changing semantic memory only.
- `agent_context/**`: watermarked recovery/navigation only.

## Next safe continuation

1. Follow `agent_context/bootstrap_manifest.json`.
2. Reconstruct current main, EventBus watermark, unexpired leases, Command Center, cursors and DLQ.
3. Reconcile any later RuntimeGraph/source-adapter/executor releases before touching projections.
4. Process only new source deltas after cursors plus late unique items idempotently.
5. Prioritise authoritative receipt reconciliation after human actions.
6. Surface only materially changed Human Frontier/P0-P1/DLQ states.
7. Select current work from live frontiers rather than this historical list.
8. Keep every state transition evidence-backed and receipt-disciplined.

## Whole-project state

This handoff made the RuntimeGraph V2.1 material cycle recoverable without chat. It is **not** the final project state. Current truth must be rebuilt from current main + bootstrap contract + Drive/Event Bus + official evidence.
