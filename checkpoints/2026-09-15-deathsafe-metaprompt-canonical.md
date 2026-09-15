# UE-Xchanges-OS — Death-Safe Master Metaprompt Canonicalization

Date: `2026-09-15`  
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`  
Baseline main before this wave: `844640c008a0cdf161925b55687cdaa159ec40a0`

## Purpose

Make the deep cold-start handoff a machine-discoverable, versioned contract rather than something that survives only because a user copies a chat message.

## Material change

- Added `agent_context/NEXT_DEATHSAFE.md` as the canonical deep continuation/metaprompt.
- Converted `agent_context/NEXT.md` into a small stable router instead of a stale task-specific monolith.
- Added `agent_context/NEXT_DEATHSAFE.md` to the bootstrap manifest required public reads without changing manifest version `1.1.0`.
- Updated `agent_context/README.md` to make the contract obvious to zero-context agents.
- Public contract remains sanitised; private live evidence stays in Drive/provider systems.
- A reusable copy is published into `rotprods/rot.knowledge` on a separate current-main branch/PR.
- A private full handoff copy is persisted in Drive.

## Why

The architecture already made semantic artifacts death-safe, but the deepest handoff still existed first as chat prose. This wave applies the same law to the instructions themselves:

```text
agent memory -> versioned recoverable contract
```

A future agent should discover the continuation contract from bootstrap rather than requiring Roberto to remember which chat contains it.

## Contract laws preserved

```text
chat memory != continuity
service liveness != persistence
restore before regenerate
semantic similarity != mutation authority
projection existence != projection freshness
historical frontier != current frontier
```

`NEXT_DEATHSAFE.md` is never live domain truth. Every agent must reconcile it against current GitHub, Drive/EventBus, current unexpired leases, RuntimeGraph freshness and provider evidence before execution.

## Writer evidence

Session: `SES-UEX-CHATGPT-20260915T121430-META01`  
Agent: `AGT-UEX-DEATHSAFE-METAPROMPT-PUBLISHER`  
WriterAuthorizationReceipt: `WAZ-be313e1ecfd0fb0c0c927fae`  
Lease: `LSE-UEX-DEATHSAFE-METAPROMPT-20260915T121602-META01`

Scope is versioned handoff/public knowledge/private Drive documentation only. No canonical opportunity/application state, RuntimeGraph execution projection, provider operation, payment, authentication or submit is authorised by this checkpoint.

## Current external-state observation before publication

The latest private recovery wave observed before this write completed its own Telegram-domain reconciliation and released its leases. It also created a **targeted RuntimeGraph overlay while explicitly preserving the globally stale RuntimeGraph watermark**. Future agents must preserve this distinction and read the later EventBus tail.

## Next

Use `agent_context/NEXT_DEATHSAFE.md` for a cold start. Its first required deliverable is a `RECOVERY READBACK`; only after that should an agent choose the current P0 frontier.
