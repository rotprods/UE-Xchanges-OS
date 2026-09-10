# UE-Xchanges-OS — CGEV2 + COS + RuntimeGraph context seal

Checkpoint: `2026-09-10T14:46:00+02:00`
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`
Baseline main observed before this handoff branch: `349f63f2109e40ab6cba960c7311456a5d7ae906`
Observed private EventBus lower-bound watermark: `EVT-20260910T132147-CPR14-008`

> Zero-context recovery checkpoint. It is a public, non-sensitive summary. Current official/provider evidence and private Drive authority always win. Volatile domain counts are intentionally not reasserted here.

## Why this seal exists

The current conversation is approaching practical context limits after a multi-day RuntimeGraph/scheduler reliability recovery. This checkpoint prevents loss of the reasoning, regression history and next safe transition.

The objective is not to preserve chat prose. It is to preserve **operationally necessary facts, falsified hypotheses, surviving invariants, current code lineage and next gates**.

## North Star

`discover → verify → prepare → execute reversible work → surface only true human/irreversible gates → submit through authorised route → bind strong receipt → learn/reconcile → continue`, while keeping exact authority/provenance and zero fabricated state.

## Current code state

Observed `main` at seal: `349f63f2109e40ab6cba960c7311456a5d7ae906`.

Reliability lineage relevant to the next agent:

- **PR67** — strict WriterAuthorizationReceipt payload/integrity boundary, content-addressed receipt ID, duplicate-key rejection, decision/timestamp binding and fail-closed verification/audit.
- **PR68** — detect stale `ACTIVE_READ_ONLY` lifecycle debt while preserving it as non-writer.
- **PR69** — bounded normal-writer health: exact current session + BootstrapGuard + currently-unexpired leases/live owners; historical hygiene is a separate watchdog/reconciliation concern.

Current runbook: `RUNBOOKS/RG22_SCHEDULED_CANARY.md`.

## Scheduler state

- `UEX Runtime Dispatcher`: **DISABLED** at seal.
- Native Scheduled Tasks dispatch capability: **PROVEN for a tiny tool-free probe**.
- Control-plane scheduler canary V3: **COMPLETED/PASS for receipt→lease ACTIVE→release→session lifecycle only**; it did not exercise source/RuntimeGraph/domain work.
- Full production-path canary PASS: **NOT PROVEN**.

Do not enable recurring production from this checkpoint alone.

## Reconciled canary history

### Production Canary V3

Session: `SES-UEX-AUTO-20260910T010530-RG22-PCV3-001`.

Outcome: later reconciled `FAILED` under CPR13. It had no own lease and did not prove source/projection execution.

### Staged Canary A

Session: `SES-UEX-AUTO-20260910T113308-RG22-SCA-001`.

Stage A completed bootstrap and emitted a time-bounded `SCHEDULER_BOOTSTRAP_READY` handoff. Stage B did not consume it before expiry. CPR13 reconciled the session `FAILED`. No WriterAuthorization receipt or lease had been acquired.

### Production Canary V4

Session: `SES-UEX-AUTO-20260910T115630-RG22-PCV4-001`.

The session registered against superseded main `801a3c7ca9a8e517de56b0bb402acf59f9299bd5`, then made no material progress and acquired no own lease. CPR14 applied `RPL-d21dbdcfd1227f0e`, closed it `FAILED`, re-evaluated its stale finding and released repair lease `LSE-UEX-CPR-20260910T131920-PCV4`.

Observed CPR14 EventBus chain:

- `EVT-20260910T131221-CPR14-001` SESSION_STARTED
- `EVT-20260910T131222-CPR14-002` bootstrap ACK
- `EVT-20260910T131728-CPR14-003` corrected canonical bootstrap ACK
- `EVT-20260910T131947-CPR14-004` WRITER_AUTHORIZATION_GRANTED
- `EVT-20260910T131948-CPR14-005` LEASE_ACQUIRED
- `EVT-20260910T132051-CPR14-006` repair applied: target ACTIVE→FAILED
- `EVT-20260910T132147-CPR14-007` health finding cleared
- `EVT-20260910T132147-CPR14-008` repair lease RELEASED

`Agent_Sessions` showed CPR14 itself `COMPLETED` with heartbeat `2026-09-10T13:23:16+02:00`. The EventBus search performed during this seal did not expose a later CPR14 SESSION_COMPLETED event. A successor must search after `...CPR14-008`; if missing, preserve this as coordination/event projection divergence and use an RPL rather than inventing history.

## Historical lease-hygiene recovery

CPR12 reconciled the class of stale/orphaned `ACTIVE` lease rows that broke live fencing semantics. The important result was **restored live `lease_fencing_integrity`**, not cosmetic removal of every historical stale row.

Subsequent CPR13/CPR14 repair leases observed in current-day rows are `RELEASED`.

At the seal, recent Work_Lease scans did not reveal a currently-unexpired overlapping writer. This is **not** permission for a successor to skip the mandatory fresh lease scan.

## CGEV2 state

CGEV2 remains the continuity/control/provenance layer:

- unique session identities;
- leases as scope fencing;
- append-only events;
- exact causal/evidence refs;
- state/handoff/checkpoints;
- reconciliation instead of overwrite;
- zero-context recovery;
- tool/provider projections kept subordinate to authority.

CGEV2 is the reason this handoff must exist outside chat.

## COS state

The repository contains a local semantic/COS-20D layer under `src/uexchanges/semantic/**` with `graphify` / `cos-graph-engine` tooling.

COS is **retrieval/topology**, not mutation authority. Semantic similarity may surface candidate relations or duplicates, but exact IDs + authoritative evidence are required before any state-changing RuntimeGraph/domain transition.

## RuntimeGraph state

RuntimeGraph remains derived.

The currently preferred production-canary architecture after PR69 is:

```text
fresh unique session
→ full manifest bootstrap
→ exact current-session lookup
→ currently-unexpired lease inventory + exact live owners
→ bounded normal-writer health
→ real WriterAuthorization
→ canonical content-addressed receipt
→ WRITER_AUTHORIZATION_GRANTED
→ immediate exact lease acquisition
→ exact-ID ACTIVE readback
→ ONE source adapter micro-batch
→ <=5 candidates
→ <=2 exact application/opportunity subgraphs
→ deterministic projection reconciliation
→ readback
→ exact lease RELEASED
→ terminal session
→ SESSION_COMPLETED
→ SCHEDULER_PRODUCTION_CANARY_PASS
```

No second adapter in a canary activation. No backlog drain.

## Deliberately NOT asserted in this seal

The seal does not assert current values for:

- number of live opportunities/applications;
- Human Frontier members;
- strong receipt count;
- current Source_Cursors;
- current Dead_Letters;
- latest Gmail organiser replies;
- current official deadlines/forms;
- Todoist binding completeness.

All of those must be reconstructed from Drive/RuntimeGraph/provider authority by the next agent.

## Absolute boundaries

- no Agent_Next execution from RG2.2;
- no fuzzy/title/embedding mutation authority;
- no Gmail message directly becoming a receipt;
- no cursor rewind;
- no blind retry after ambiguous write;
- no payment;
- no authentication/MFA/CAPTCHA handling by generic agent;
- no credentials/OTP/cookies export/use;
- no external PREFILL certification by inference;
- no irreversible Submit;
- no historical `COMPLETED` invented for cleanliness.

## Next milestone

**`SCHEDULER_PRODUCTION_CANARY_PASS #1` on current main.**

Then:

1. second independent clean production-path canary;
2. enable bounded hourly dispatcher only after two PASSes;
3. observe at least 3 clean recurrent cycles;
4. declare `RG2.2_SCHEDULED_PRODUCTION_STABLE` only with read-back evidence;
5. continue historical hygiene separately;
6. resume RG2.3 reversible execution;
7. provider-specific Form Gateway certification;
8. strong receipt engine and application throughput.

See `agent_context/NEXT.md` for the copy/paste continuation directive.
