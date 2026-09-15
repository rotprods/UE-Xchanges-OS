# UE-Xchanges-OS — Agent Context Pack

Current semantic-durability seal: `2026-09-15`
Baseline main before this seal: `c5fd939617cb28f8af90d5ac39907564804ee925`

This directory is a **derived zero-context recovery projection**. It exists so a new agent can recover the system without this chat. It never overrides current official/provider evidence, private Drive canonical state, current GitHub contracts, or current unexpired leases.

## Mandatory bootstrap

Machine-readable contract: [`bootstrap_manifest.json`](bootstrap_manifest.json).

Stable semantic memory: [`../MEMORY.md`](../MEMORY.md).

Semantic-brain durability/restore contract: [`../docs/SEMANTIC_BRAIN_DURABILITY.md`](../docs/SEMANTIC_BRAIN_DURABILITY.md).

Current zero-context continuation: [`NEXT.md`](NEXT.md).

Current semantic durability checkpoint: [`../checkpoints/2026-09-15-semantic-brain-durability-seal.md`](../checkpoints/2026-09-15-semantic-brain-durability-seal.md).

Previous scheduler/context seal: [`../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md`](../checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md).

Every writer still follows the bootstrap manifest and current `AGENTS.md`; this pack does not bypass WriterAuthorization or leases. A WriterAuthorization receipt is coordination evidence only; it is not domain authority or external capability.

## Current navigation

- `context.md` — public/non-sensitive snapshot and authority map.
- `progress.md` — completed reliability milestones, blockers and promotion ladder.
- `checkpoints.md` — checkpoint/release/event index.
- `session.md` — known canary/repair lifecycle snapshot.
- `runtimegraph.md` — RG2.2 scheduler/runtime topology and limits.
- `knowledge.md` — known/unknown facts and inference boundaries, including semantic-brain durability.
- `recovery.md` — zero-context recovery algorithm, including restore-before-regenerate law.
- `CGEV2_COS.md` — responsibility/authority split between CGEV2, COS and RuntimeGraph.
- `REGRESSION.md` — scheduler/runtime incident regression history and falsified hypotheses.
- `LEARNINGS.md` — durable engineering lessons and required regression tests.
- `CONSCIOUSNESS_ACT.md` — operational awareness: knowns, unknowns, stop-lines and dominant risk.
- `NEXT.md` — exact next-agent directive and DoD.

## Semantic brain durability

A running Qdrant/Ollama daemon is **not** the persistence boundary. The semantic brain survives agent/sandbox death through validated external artifacts, manifests/checksums, public recovery contracts and private recovery packages.

Cold agents must:

1. read `docs/SEMANTIC_BRAIN_DURABILITY.md` (the bootstrap manifest now requires it);
2. restore and checksum validated artifacts before regenerating embeddings;
3. classify historical partitions by their source SHA instead of pretending they are current;
4. preserve private live-evidence overlays outside public GitHub;
5. keep every semantic result `mutation_authority=false`.

Current known recovery assurance records a validated historical **676-point / 397-path** Qwen3 1024D index, Qdrant v1.19.0, COS-20D topology, isolated snapshot restoration and external private backup. Exact model/runtime binaries are not yet all independently replicated in that external backup, so an air-gapped bit-for-bit restore remains a future hardening gate.

## Current critical coordination state

- Baseline main before this seal: `c5fd939617cb28f8af90d5ac39907564804ee925`.
- RuntimeGraph read on 2026-09-15 was materially stale versus the canonical EventBus/source evidence; projection existence must not be confused with freshness.
- Exact current domain/frontier state still requires fresh Drive/provider reconstruction.
- Semantic retrieval/COS/fuzzy similarity never authorises a state transition.

## Fast cold start

```text
CURRENT_GITHUB_MAIN_SHA
→ goal.md
→ AGENTS.md
→ MEMORY.md
→ agent_context/bootstrap_manifest.json
→ docs/SEMANTIC_BRAIN_DURABILITY.md
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
→ restore/validate semantic artifacts if semantic retrieval is needed
→ NEW session
→ SESSION_STARTED
→ BOOTSTRAP_CONTEXT_LOADED
→ bounded current-writer health
→ WriterAuthorization(ALLOWED)
→ WRITER_AUTHORIZATION_GRANTED(receipt)
→ canonical receipt
→ immediate narrow lease
→ bounded work
→ exact readback
→ release
→ terminal session
```

## Authority rule

If any snapshot in this directory conflicts with fresher authoritative evidence, **the snapshot loses**. Never “repair” authority to match this documentation.
