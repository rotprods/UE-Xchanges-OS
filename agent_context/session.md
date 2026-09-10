# UE-Xchanges-OS — Session / Lease Snapshot

Seal: `2026-09-10T14:46:00+02:00`
Baseline main: `349f63f2109e40ab6cba960c7311456a5d7ae906`

> Derived snapshot. Never reuse any Session ID below for writes. Re-read current `Agent_Sessions`, currently-unexpired `Work_Leases` and EventBus before mutation.

## Current known terminal reliability sessions

### Scheduler control-plane canary V3
- Session: `SES-UEX-AUTO-20260909T134553-CANV3-001`
- Status: `COMPLETED`.
- Lease: `LSE-UEX-SCHEDULER-CANARY-V3-20260909T140041-001` → `RELEASED`.
- Meaning: proves scheduler control-plane receipt/lease/release lifecycle only.
- Source/RuntimeGraph/Todoist/domain mutation: none.

### Production canary V3
- Session: `SES-UEX-AUTO-20260910T010530-RG22-PCV3-001`
- Status: `FAILED` after CPR13 reconciliation.
- Own RG2.2 lease: none observed.
- Production PASS: no.

### Staged production canary A
- Session: `SES-UEX-AUTO-20260910T113308-RG22-SCA-001`
- Status: `FAILED` after CPR13 reconciliation.
- Stage A did reach `STAGED_BOOTSTRAP_READY`, but its handoff expired unconsumed.
- WriterAuthorization/lease: none.

### Production canary V4
- Session: `SES-UEX-AUTO-20260910T115630-RG22-PCV4-001`
- Status: `FAILED` after CPR14/RPL `RPL-d21dbdcfd1227f0e`.
- It referenced superseded main `801a3c7c...` and made no later progress.
- Own RG2.2 lease/source/RuntimeGraph/provider mutation: none.

## Repair sessions

### CPR12
- Session: `SES-UEX-CHATGPT-20260909T175507-CPR12`.
- Status: `COMPLETED`.
- 31 own repair leases recorded `RELEASED`.
- Material outcome: orphaned-owner stale lease class reconciled and live fencing integrity restored.

### CPR13
- Session: `SES-UEX-CHATGPT-20260910T124209-CPR13`.
- Status: `COMPLETED`.
- Reconciled PCV3 and staged-A; repair fences released.

### CPR14
- Session: `SES-UEX-CHATGPT-20260910T131121-CPR14`.
- `Agent_Sessions` status observed: `COMPLETED`, heartbeat `2026-09-10T13:23:16+02:00`.
- Repair lease: `LSE-UEX-CPR-20260910T131920-PCV4` → `RELEASED`.
- EventBus lower-bound observed through `EVT-20260910T132147-CPR14-008` (`LEASE_RELEASED`).
- Verify whether a later `SESSION_COMPLETED` event exists; if absent, preserve as event/session divergence.

## Current scheduler

`UEX Runtime Dispatcher` is disabled at seal.

Do not infer writer concurrency from scheduler enabled/disabled state. Only current unexpired leases are write fences.

## Recent lease observation

The current-day exact repair/merge rows inspected for this seal were `RELEASED`. No actually-unexpired overlapping writer was observed in the recent scan. This is not durable permission; a successor must scan again immediately before authorization/mutation.

## Session law for successor

```text
NEW unique session ID
→ SESSION_STARTED
→ mandatory bootstrap
→ BOOTSTRAP_CONTEXT_LOADED
→ refresh current main/EventBus/unexpired leases
→ bounded current-writer health
→ real WriterAuthorization
→ canonical receipt
→ exact narrow lease
→ bounded work
→ exact readback
→ release
→ terminal session
```

Historical canary/repair Session IDs are evidence only, never resumable write identities.
