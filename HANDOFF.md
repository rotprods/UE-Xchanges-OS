# UE-Xchanges-OS — HANDOFF

Checkpoint: `2026-09-10T14:46:00+02:00`
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`
Baseline main observed before this handoff branch: `349f63f2109e40ab6cba960c7311456a5d7ae906`
Private EventBus lower-bound observed: `EVT-20260910T132147-CPR14-008`

Purpose: allow a fresh agent to recover the current UE-Xchanges-OS operating state without relying on this chat.

> This is a watermarked public recovery projection. Fresh official/provider evidence, private Drive canonical state, current GitHub main/contracts and current unexpired leases override it.

## Mandatory cold start

1. Read current GitHub `main` and record SHA.
2. Read `goal.md`.
3. Read `AGENTS.md`.
4. Read `MEMORY.md`.
5. Read `agent_context/bootstrap_manifest.json` and obey its required public/private read sets.
6. Read `LIVE-STATE-OVERRIDE.json`, `STATE.md`, this file and the newest checkpoint.
7. Read `agent_context/README.md`, `context.md`, `progress.md`, `checkpoints.md`, `session.md`, `runtimegraph.md`, `knowledge.md`, `recovery.md`, `CGEV2_COS.md`, `REGRESSION.md`, `LEARNINGS.md`, `CONSCIOUSNESS_ACT.md`, and finally `NEXT.md`.
8. Read private Drive `Context_Registry`, exact/new `Agent_Sessions`, currently **UNEXPIRED** `Work_Leases`, and `Agent_Event_Bus` after the current watermark.
9. Read RuntimeGraph V2 Command Center `Command_Center`, `Human_Now`, `Agent_Next`, `Source_Cursors` and `Dead_Letters`.
10. Read fresh Gmail/official/Form/receipt evidence only when the next operation depends on it.
11. Register a **new** Session ID. Never reuse any historical Session ID below for writes.
12. Emit `SESSION_STARTED`, then `BOOTSTRAP_CONTEXT_LOADED`.
13. Refresh current main + current EventBus + currently-unexpired leases immediately before WriterAuthorization.
14. Acquire only the smallest exact lease after a real positive authorization and canonical receipt.

## Reliability lineage now in code

### PR67 — WriterAuthorization receipt integrity

Established strict canonical receipt payload validation, duplicate JSON-key rejection, content-addressed `receipt_id`, exact decision/session/context/main/lease/scope/health/prelease binding, authorization-timestamp integrity, and fail-closed audit/gate behavior.

### PR68 — stale `ACTIVE_READ_ONLY` visibility

Made stale nonterminal read-only sessions visible to health/reconciliation while preserving `ACTIVE_READ_ONLY` as non-writer.

### CPR12 — live fencing recovery

Reconciled the orphaned-owner stale lease class under narrow evidence-backed RPLs. Material result: live `lease_fencing_integrity` was restored. Historical hygiene was deliberately not treated as a normal-writer critical-path blocker.

### PR69 — bounded normal-writer health

Current baseline main includes `uexchanges.bounded_writer_health.evaluate_bounded_writer_authorization_health` and `RUNBOOKS/RG22_SCHEDULED_CANARY.md`.

Normal `DERIVED_PROJECTION` authorization must evaluate:

- exact stable-ID matches for the current new session;
- the real BootstrapGuard for this current writer;
- currently-unexpired leases only;
- exact owner/bootstrap evidence for every actually-live lease.

The resulting report explicitly does **not** claim historical hygiene was evaluated globally.

## Scheduler state at this checkpoint

```text
Native Scheduled Tasks tool-free dispatch probe   PASS
Control-plane canary V3 receipt/lease lifecycle   PASS
Full RG2.2 scheduled production path              NOT YET PASS
UEX Runtime Dispatcher recurring                   DISABLED
```

A scheduler probe does not certify RuntimeGraph. A control-plane canary does not certify source dispatch.

## Reconciled failed canaries

### Production canary V3

`SES-UEX-AUTO-20260910T010530-RG22-PCV3-001` → `FAILED` through CPR13. No own RG2.2 lease/source-path success claimed.

### Staged canary A

`SES-UEX-AUTO-20260910T113308-RG22-SCA-001` completed cold bootstrap and created a bounded handoff, but Stage B did not consume it before expiry. CPR13 reconciled the session `FAILED`. No WriterAuthorization receipt/lease existed.

### Production canary V4

`SES-UEX-AUTO-20260910T115630-RG22-PCV4-001` registered against superseded main `801a3c7ca9a8e517de56b0bb402acf59f9299bd5`, acquired no own lease, made no source/RuntimeGraph/provider mutation, and was reconciled `FAILED` by CPR14 using `RPL-d21dbdcfd1227f0e`.

Never reuse these Session IDs.

## CPR14 terminal-evidence caveat

`Agent_Sessions` showed `SES-UEX-CHATGPT-20260910T131121-CPR14` as `COMPLETED` with heartbeat `2026-09-10T13:23:16+02:00`.

The EventBus search performed while sealing this handoff observed CPR14 through:

- `EVT-20260910T132051-CPR14-006` — target repair ACTIVE→FAILED;
- `EVT-20260910T132147-CPR14-007` — target finding cleared;
- `EVT-20260910T132147-CPR14-008` — repair lease ACTIVE→RELEASED.

It did not expose a later CPR14 `SESSION_COMPLETED` event in that search. A successor must read the EventBus tail after `...CPR14-008`; if terminal event evidence is still absent, preserve this as coordination/event divergence and use the reconciliation planner rather than fabricating history.

## RuntimeGraph production-canary contract

The immediate milestone is **`SCHEDULER_PRODUCTION_CANARY_PASS #1`**.

Use the current scheduled-canary runbook and keep one activation deliberately small:

```text
NEW SESSION
→ full manifest bootstrap
→ exact current-session lookup
→ current main/EventBus/unexpired leases refresh
→ bounded writer health
→ real WriterAuthorization
→ canonical content-addressed receipt
→ persist WRITER_AUTHORIZATION_GRANTED
→ immediate exact lease acquisition
→ exact-ID ACTIVE readback
→ ONE adapter slice
→ <=5 source candidates
→ <=2 exact application/opportunity subgraphs
→ deterministic derived reconciliation only
→ exact readback
→ exact lease RELEASED
→ terminal session
→ SESSION_COMPLETED
→ SCHEDULER_PRODUCTION_CANARY_PASS
```

No second adapter and no backlog drain in the canary.

## Source / receipt rules

- explicit adapter-contract facts only;
- exact `application_id` / `opportunity_id` for state-changing routing;
- fuzzy title matching, similarity and COS/embeddings never authorise mutation;
- Gmail raw prose or absence is never receipt authority;
- strong receipt requires canonical evidence bound to exact submission identity;
- at-least-once delivery + deterministic idempotency + monotonic cursors;
- same transient strategy max 3;
- poison/unroutable normalized events → `Dead_Letters`;
- preserve continuation boundary; never advance cursor past unprocessed evidence.

## Derived self-heal boundary

RG2.2 may repair only actual deterministic mismatches on its current derived allowlist. It must never use projection repair to rewrite canonical `Opportunities`, `Applications`, `Mass_Apply_Queue`, `Execution_Log`, `Agent_Event_Bus`, `Agent_Sessions`, `Work_Leases`, `Autofill_Profile` or `Human_Gates`.

Control-plane lifecycle repair requires its own evidence-backed `CONTROL_PLANE_REPAIR` RPL.

## Absolute boundaries

- RG2.2 never executes `Agent_Next`;
- no payment;
- no generic-agent login/MFA/CAPTCHA handling;
- no credentials/OTP/cookies export or use;
- no inferred external PREFILL certification;
- no irreversible Submit;
- no historical `COMPLETED` invented for dashboard cleanliness.

## CGEV2 / COS split

- **CGEV2** = continuity, provenance, exact identity, sessions, leases, EventBus, checkpoints, reconciliation and zero-context recovery.
- **COS** = semantic retrieval, 20D topology, graph navigation and candidate relation discovery.
- **RuntimeGraph** = exact-ID deterministic execution/read projection.
- **Provider/Drive authority** = truth.

COS may suggest what to inspect. It may never decide what state to mutate.

## Deliberately not asserted here

This seal did not refresh the whole domain. Do not reuse old 2026-09-02 counts/frontiers/deadlines as current.

The next agent must reconstruct live:

- opportunities/applications;
- Human Frontier;
- strong receipts;
- Source_Cursors;
- Dead_Letters;
- organiser replies;
- official deadlines/forms;
- Todoist exact bindings.

## Promotion ladder

1. `SCHEDULER_PRODUCTION_CANARY_PASS #1`.
2. Independent clean PASS #2.
3. Enable bounded hourly `UEX Runtime Dispatcher` only after two PASSes.
4. Observe at least 3 consecutive clean recurrent cycles.
5. Declare `RG2.2_SCHEDULED_PRODUCTION_STABLE` only with read-back evidence.
6. Continue historical hygiene separately through watchdog/RPL queue.
7. Resume RG2.3 reversible execution.
8. Provider-specific Form Gateway certification.
9. Receipt-backed application throughput.

## Fast continuation

Read [`agent_context/NEXT.md`](agent_context/NEXT.md) and execute exactly one next promotion wave. It contains the copy/paste `/next` directive.
