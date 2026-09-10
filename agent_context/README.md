# UE-Xchanges-OS — Agent Context Pack

Current seal: `2026-09-10T14:46:00+02:00`
Baseline main at seal: `349f63f2109e40ab6cba960c7311456a5d7ae906`

This directory is a **derived zero-context recovery projection**. It exists so a new agent can recover the system without this chat. It never overrides current official/provider evidence, private Drive canonical state, current GitHub contracts, or current unexpired leases.

## Mandatory bootstrap

Machine-readable contract: [`bootstrap_manifest.json`](bootstrap_manifest.json).

Stable semantic memory: [`../MEMORY.md`](../MEMORY.md).

Current zero-context continuation: [`NEXT.md`](NEXT.md).

Current context seal: [`../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md`](../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md).

Every writer still follows the bootstrap manifest and current `AGENTS.md`; this pack does not bypass WriterAuthorization or leases.

## Current navigation

- `context.md` — current public/non-sensitive snapshot and authority map.
- `progress.md` — completed reliability milestones, current blockers and promotion ladder.
- `checkpoints.md` — checkpoint/release/event index.
- `session.md` — current known canary/repair lifecycle snapshot.
- `runtimegraph.md` — current RG2.2 scheduler/runtime topology and limits.
- `knowledge.md` — known/unknown facts and inference boundaries.
- `recovery.md` — zero-context recovery algorithm.
- `CGEV2_COS.md` — explicit responsibility/authority split between CGEV2, COS and RuntimeGraph.
- `REGRESSION.md` — scheduler/runtime incident regression history and falsified hypotheses.
- `LEARNINGS.md` — durable engineering lessons and required regression tests.
- `CONSCIOUSNESS_ACT.md` — operational awareness: knowns, unknowns, stop-lines and dominant risk.
- `NEXT.md` — exact next-agent directive and DoD.

## Current critical state

- `UEX Runtime Dispatcher` is disabled.
- Simple Scheduled Tasks dispatch is proven by a tool-free probe; that does not certify RG2.2.
- Control-plane canary V3 proved receipt→lease→release lifecycle only.
- Full production-path canary PASS has **not** been proven.
- PCV3, staged-A and PCV4 stale sessions were reconciled `FAILED` by CPR13/CPR14; never reuse them.
- PR69 on the baseline main introduced bounded normal-writer health based on exact current session + BootstrapGuard + currently-unexpired leases/live owners.
- Historical hygiene remains a separate `CONTROL_PLANE_REPAIR`/watchdog concern.

## Fast cold start

```text
CURRENT_GITHUB_MAIN_SHA
→ goal.md
→ AGENTS.md
→ MEMORY.md
→ agent_context/bootstrap_manifest.json
→ LIVE-STATE-OVERRIDE.json
→ STATE.md
→ HANDOFF.md
→ newest checkpoint
→ this pack, especially NEXT.md + CONSCIOUSNESS_ACT.md + REGRESSION.md
→ Drive Context_Registry
→ exact current/new Agent_Sessions
→ currently UNEXPIRED Work_Leases only
→ Agent_Event_Bus after live watermark
→ RuntimeGraph Command_Center/Human_Now/Agent_Next/Source_Cursors/Dead_Letters
→ fresh provider evidence when action depends on it
→ NEW session
→ SESSION_STARTED
→ BOOTSTRAP_CONTEXT_LOADED
→ bounded current-writer health
→ real WriterAuthorization
→ canonical receipt
→ immediate narrow lease
→ bounded work
→ exact readback
→ release
→ terminal session
```

## Authority rule

If any snapshot in this directory conflicts with fresher authoritative evidence, **the snapshot loses**. Never “repair” authority to match this documentation.
