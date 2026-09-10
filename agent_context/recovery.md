# UE-Xchanges-OS — Zero-Context Recovery Procedure

Current seal: `2026-09-10T14:46:00+02:00`

Use this when a new agent starts with no trusted chat memory.

## 1. Establish current Git authority

Read current `main` first. Historical baseline for this seal is `349f63f2109e40ab6cba960c7311456a5d7ae906`; a later main supersedes it.

Then read:

1. `../goal.md`
2. `../AGENTS.md`
3. `../MEMORY.md`
4. `bootstrap_manifest.json`
5. `../LIVE-STATE-OVERRIDE.json`
6. `../STATE.md`
7. `../HANDOFF.md`
8. `../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md`
9. this directory's current navigation files, ending with `NEXT.md`
10. current writer-authorization/bootstrap/runbook files required by the manifest and by the intended operation.

## 2. Reconstruct private control plane

Read:

- `Context_Registry`;
- exact/new `Agent_Sessions`;
- currently **UNEXPIRED** `Work_Leases` only for live fencing;
- `Agent_Event_Bus` after the live watermark;
- RuntimeGraph `Command_Center`, `Human_Now`, `Agent_Next`, `Source_Cursors`, `Dead_Letters`.

Seal lower-bound EventBus watermark: `EVT-20260910T132147-CPR14-008`.

Do not assume this is the current tail. Read every later event.

## 3. Reconcile scheduler/canary lifecycle

At seal:

- `UEX Runtime Dispatcher` disabled;
- simple tool-free scheduler probe succeeded;
- control-plane canary V3 completed exact receipt/lease/release lifecycle;
- no full production-path PASS;
- PCV3, staged-A and PCV4 are terminal FAILED after CPR13/14 and are never reusable.

Verify whether CPR14 has a later `SESSION_COMPLETED` EventBus event. If its session row and event chain disagree, create a finding/RPL; do not invent event history.

## 4. Reconstruct domain state fresh

This seal intentionally does not assert current opportunities, applications, Human Frontier, receipts, deadlines or source cursors.

Read canonical Drive and fresh provider evidence before any domain/frontier claim.

## 5. Normal writer authorization

Use current PR69 architecture when still present on main:

```text
exact new current session rows
+ exact BootstrapGuard evidence
+ currently-unexpired leases
+ exact live lease owners/bootstrap evidence
→ bounded writer health
→ WriterAuthorization
→ canonical receipt
→ immediate exact lease acquisition
```

`historical_hygiene_evaluated=false` means exactly that. Do not pretend it is a global-green report.

## 6. Execute only one RG2.2 micro-batch

For scheduled canary/initial production:

- one adapter slice;
- <=5 new/late-unique candidates;
- <=2 exact application/opportunity subgraphs;
- no second adapter in the same activation;
- preserve continuation boundary;
- never advance cursor beyond unprocessed evidence.

Exact-ID explicit adapter facts only.

## 7. Preserve authority boundaries

- Gmail cannot directly become receipt.
- COS/fuzzy/title/embedding similarity cannot authorize mutation.
- RuntimeGraph cannot self-heal canonical domain state.
- RG2.2 cannot execute Agent_Next.
- Todoist mutation requires exact persisted binding.
- payments/auth/credentials/OTP/cookies/external PREFILL/Submit remain outside generic execution.

## 8. Closure is mandatory

Reserve activation budget for:

- exact read-back;
- release all own leases by stable ID;
- verify `RELEASED`;
- close session terminally;
- emit terminal event evidence;
- persist changed STATE/HANDOFF/NEXT/checkpoint only when state materially changed.

## 9. Promotion sequence

```text
SCHEDULER_PRODUCTION_CANARY_PASS #1
→ independent PASS #2
→ enable bounded hourly dispatcher
→ 3 consecutive clean recurrent cycles
→ RG2.2_SCHEDULED_PRODUCTION_STABLE
→ safe self-heal subset
→ RG2.3 reversible execution
→ provider Form Gateway certification
→ receipt-backed application throughput
```

## 10. End every session durably

Before exit, persist exact main SHA, private watermark, own session/lease lifecycle, tests/read-backs, blockers, next transition and handoff. Chat text is never the sole continuity layer.
