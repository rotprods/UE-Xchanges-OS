# UE-Xchanges-OS — Agent Context Snapshot

Seal: `2026-09-10T14:46:00+02:00`
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`
Baseline main: `349f63f2109e40ab6cba960c7311456a5d7ae906`
Observed EventBus lower-bound watermark: `EVT-20260910T132147-CPR14-008`

> DERIVED RECOVERY PROJECTION. Fresh official/provider evidence, private Drive canonical state, current GitHub main/contracts and current unexpired leases override this file.

## Mission

Operate `APPLY EVERYTHING VIABLE` as an evidence-first global mobility / paid-role / trainer pipeline. The goal is receipt-backed outcomes, not activity metrics or infrastructure for its own sake.

## Current system situation

The active engineering problem is RG2.2 scheduled-production reliability.

Current evidence:

- PR67 hardened WriterAuthorization receipts/integrity.
- PR68 made stale `ACTIVE_READ_ONLY` sessions observable without granting writer authority.
- CPR12 reconciled the orphaned lease class that broke live fencing semantics.
- PR69 added bounded normal-writer health over the exact current session and actually-unexpired lease set.
- Tiny native Scheduled Tasks probe completed successfully.
- Control-plane canary V3 completed a receipt/lease/release lifecycle.
- No full production-path canary PASS is proven.
- `UEX Runtime Dispatcher` remains disabled.

## Terminal canary debt already reconciled

- `SES-UEX-AUTO-20260910T010530-RG22-PCV3-001` → FAILED via CPR13.
- `SES-UEX-AUTO-20260910T113308-RG22-SCA-001` → FAILED via CPR13 after unconsumed staged-bootstrap handoff expiry.
- `SES-UEX-AUTO-20260910T115630-RG22-PCV4-001` → FAILED via CPR14; no own lease/source/RuntimeGraph/provider mutation.

Never reuse these Session IDs.

## Current uncertainty

This seal intentionally did not refresh the full opportunity/application domain, Human Frontier, source cursors, Dead Letters or Gmail/official sources. Historical counts from 2026-09-02 must not be treated as current.

A successor must read Drive and RuntimeGraph before making any domain/frontier claim.

## Current authority topology

```text
Official/provider/receipt evidence
            ↓
Private Drive canonical CRM + Agent_Event_Bus
            ↓
CGEV2 control/provenance layer
       ↙                 ↘
RuntimeGraph exact-ID      COS semantic/20D retrieval
execution projection       navigation/topology only
       ↘                 ↙
Human / Agent / System frontier
```

COS similarity never authorises a state-changing route.

## Canonical resources

- Private CRM: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`
- RuntimeGraph V2 Command Center: `1OtSLFI4VHW6aSne1YjtRykRsN4j4G4OcEGSCXVDLwbM`
- GitHub: `rotprods/UE-Xchanges-OS`
- Current runbook: `RUNBOOKS/RG22_SCHEDULED_CANARY.md`
- Current checkpoint: `checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md`
- Continuation directive: `agent_context/NEXT.md`

## Immediate target

`SCHEDULER_PRODUCTION_CANARY_PASS #1` on current main, using bounded writer health and one source micro-batch.

Then a second independent clean canary. Only then may recurring RG2.2 be considered for re-enable.
