# UE-Xchanges-OS — STATE

Updated: `2026-09-10T14:46:00+02:00`
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`
Baseline GitHub main observed: `349f63f2109e40ab6cba960c7311456a5d7ae906`
Private EventBus lower-bound observed: `EVT-20260910T132147-CPR14-008`

> Current public recovery projection. It intentionally avoids asserting volatile opportunity/application/frontier counts that were not re-read during this seal. Current official/provider evidence and private Drive canonical state always win.

## North Star

Operate `APPLY EVERYTHING VIABLE` as an evidence-first system that converts legitimate Spain-compatible opportunities into verified, receipt-backed outcomes while keeping irreversible/sensitive actions human-gated and making all agent work recoverable without chat.

## Authority

`official/organiser/receipt → private Drive CRM + EventBus → current GitHub policy/code/recovery → RuntimeGraph derived state → COS/task/UI projections → chat`.

COS/semantic similarity is never mutation authority.

## Current reliability release

Current baseline main: `349f63f2109e40ab6cba960c7311456a5d7ae906`.

Relevant lineage:

- PR67 — strict WriterAuthorizationReceipt shape/integrity, content address, duplicate-key rejection, decision/timestamp binding and fail-closed gate/audit.
- PR68 — stale `ACTIVE_READ_ONLY` lifecycle visibility without granting writer authority.
- CPR12 — reconciled orphaned-owner stale lease class and restored live fencing semantics.
- PR69 — bounded normal-writer health over the exact current session + BootstrapGuard + currently-unexpired leases/live owners. Historical hygiene remains separate.

Current runbook: `RUNBOOKS/RG22_SCHEDULED_CANARY.md`.

## Scheduler / RG2.2 promotion state

```text
Native Scheduled Tasks dispatch probe       PASS
Control-plane receipt/lease canary V3       PASS
Full scheduled RG2.2 production path        NOT YET PASS
UEX Runtime Dispatcher recurring             DISABLED
```

The simple probe proves only native task dispatch. The control-plane canary proves only coordination lifecycle. Neither certifies source-dispatch/projection production.

## Failed production canaries already reconciled

- `SES-UEX-AUTO-20260910T010530-RG22-PCV3-001` → `FAILED` under CPR13. No own RG2.2 lease/source-path success claimed.
- `SES-UEX-AUTO-20260910T113308-RG22-SCA-001` → `FAILED` under CPR13 after Stage-A bootstrap handoff expired unconsumed. No WriterAuthorization/lease had been acquired.
- `SES-UEX-AUTO-20260910T115630-RG22-PCV4-001` → `FAILED` under CPR14 / `RPL-d21dbdcfd1227f0e`; no own lease/source/RuntimeGraph/provider mutation; no production PASS inferred.

These Session IDs are historical evidence and must never be reused for writes.

## Recent control-plane repair state

### CPR12
`SES-UEX-CHATGPT-20260909T175507-CPR12` → `COMPLETED`.

Material outcome: the orphaned-owner `ACTIVE` lease class that broke live fencing semantics was reconciled in narrow RPL waves. Its own repair leases were observed `RELEASED`.

### CPR13
`SES-UEX-CHATGPT-20260910T124209-CPR13` → `COMPLETED`; PCV3 + Stage-A repaired to `FAILED`, exact repair fences released.

### CPR14
`SES-UEX-CHATGPT-20260910T131121-CPR14` was observed `COMPLETED` in `Agent_Sessions` with heartbeat `2026-09-10T13:23:16+02:00`.

Observed EventBus chain through:
- `EVT-20260910T132051-CPR14-006` repair target ACTIVE→FAILED;
- `EVT-20260910T132147-CPR14-007` target health finding cleared;
- `EVT-20260910T132147-CPR14-008` repair lease ACTIVE→RELEASED.

The EventBus search used for this seal did not expose a later CPR14 `SESSION_COMPLETED` event. Successor must search later events; if absent, treat as coordination/event divergence rather than inventing history.

## Current concurrency statement

Current-day repair/merge rows inspected during this seal were `RELEASED`. No actually-unexpired overlapping writer was observed in the recent scan.

This is a snapshot, not durable permission. Before any write, re-read **all currently-unexpired** leases relevant to the proposed scope.

## RuntimeGraph operating law

Normal `DERIVED_PROJECTION` writer authorization now uses the PR69 bounded health path:

```text
exact new current session
+ exact BootstrapGuard evidence
+ currently-unexpired leases only
+ exact live owners/bootstrap evidence
→ bounded ControlPlaneHealthReport
→ WriterAuthorization
→ canonical WriterAuthorizationReceipt
→ immediate exact lease acquisition
```

`historical_hygiene_evaluated=false` is not a global-green claim.

Scheduled canary/initial production micro-budget:

- exactly one adapter slice maximum;
- at most 5 new/late-unique candidates;
- at most 2 exact application/opportunity subgraphs;
- no second adapter in the same activation;
- monotonic cursor with continuation boundary;
- at-least-once + deterministic idempotency;
- same transient strategy max 3;
- poison/unroutable normalized events → Dead_Letters.

## Self-heal boundary

RG2.2 may repair actual deterministic mismatches only on derived RuntimeGraph surfaces allowed by current runbook/policy. It must never use projection repair to rewrite canonical Opportunities, Applications, Mass_Apply_Queue, Execution_Log, Agent_Event_Bus, Agent_Sessions, Work_Leases, Autofill_Profile or Human_Gates.

Control-plane lifecycle changes require their own coordination operation or separate evidence-backed `CONTROL_PLANE_REPAIR` RPL.

## External/sensitive boundary

- RG2.2 never executes `Agent_Next`.
- Gmail raw prose/absence cannot directly establish receipt.
- A strong receipt must bind to exact submission identity.
- No fuzzy/title/embedding route may cause a state mutation.
- No payment.
- No authentication/MFA/CAPTCHA handling by generic agent.
- No credentials/OTP/cookies export/use.
- No external PREFILL certification by inference.
- No irreversible Submit.

## Volatile domain state

Not refreshed in this seal. Do **not** treat 2026-09-02 counts/frontiers/deadlines as current.

A successor must reconstruct:

- canonical opportunity/application state;
- Human Frontier;
- strong receipt count;
- Source_Cursors;
- Dead_Letters;
- organiser replies;
- authoritative official deadlines/forms;
- Todoist exact bindings;

from private Drive/RuntimeGraph/provider evidence.

## Immediate next milestone

`SCHEDULER_PRODUCTION_CANARY_PASS #1` on current main using `RUNBOOKS/RG22_SCHEDULED_CANARY.md`.

Promotion ladder:

`PASS #1 → independent PASS #2 → enable bounded hourly RG2.2 → 3 clean recurrent cycles → RG2.2_SCHEDULED_PRODUCTION_STABLE → safe self-heal subset → RG2.3 → provider certification → receipt-backed throughput`.

## Recovery pointers

- `HANDOFF.md`
- `agent_context/NEXT.md`
- `agent_context/CONSCIOUSNESS_ACT.md`
- `agent_context/REGRESSION.md`
- `agent_context/LEARNINGS.md`
- `agent_context/CGEV2_COS.md`
- `checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md`
