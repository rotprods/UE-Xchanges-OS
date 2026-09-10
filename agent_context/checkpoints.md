# UE-Xchanges-OS — Checkpoint Index

> Derived navigation only. Current GitHub main, private Drive/EventBus and fresh provider evidence override every snapshot here.

## Current seal

- Timestamp: `2026-09-10T14:46:00+02:00`
- Baseline main: `349f63f2109e40ab6cba960c7311456a5d7ae906`
- Private EventBus lower-bound observed: `EVT-20260910T132147-CPR14-008`
- Checkpoint: [`../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md`](../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md)
- Continuation: [`NEXT.md`](NEXT.md)

## Reliability milestones represented by the current seal

- CGEV2 zero-context continuity exists; chat is not the continuity system.
- PR67: strict WriterAuthorization receipt/integrity boundary.
- PR68: stale `ACTIVE_READ_ONLY` visibility without writer promotion.
- CPR12: orphaned-owner lease class reconciled; live fencing semantics restored.
- Scheduler control-plane canary V3: receipt/lease ACTIVE/release lifecycle proven without source/domain mutation.
- PR69: bounded normal-writer health over exact current writer + currently-unexpired leases/live owners.
- CPR13: production-canary V3 + staged-A reconciled `FAILED`.
- CPR14: production-canary V4 reconciled `FAILED`; repair fence released.
- Full scheduled RG2.2 production-path PASS remains unproven.
- `UEX Runtime Dispatcher` remains disabled.

## Current next checkpoint trigger

Create a new checkpoint only after a material transition:

1. `SCHEDULER_PRODUCTION_CANARY_PASS #1`;
2. independent production-canary PASS #2;
3. recurring RG2.2 enabled;
4. 3 consecutive clean recurrent cycles / `RG2.2_SCHEDULED_PRODUCTION_STABLE`;
5. material Human Frontier, strong-receipt or P0/P1 gate change.

Do not create a success checkpoint merely because a scheduled task started or a simple scheduler probe passed.

## Historical checkpoint pointers

- `2026-09-01-cgev2-zero-context-survival.md` — original CGEV2 zero-context survival boundary.
- `2026-09-02-runtimegraph-v2-1-dispatch-cycle-close.md` — older RuntimeGraph dispatch recovery baseline; domain/frontier counts inside are historical.
- `2026-09-10-cgev2-cos-runtimegraph-context-seal.md` — current reliability/continuity seal.
