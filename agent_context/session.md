# UE-Xchanges-OS — Session / Lease Snapshot

Snapshot: 2026-09-02 00:22 Europe/Madrid

## Current session

```text
Session ID:  SES-UEX-CHATGPT-20260902T002200-31
Agent ID:    AGT-AGENT-CONTEXT-SURVIVAL-SEALER
Context ID:  CTX-UEX-GLOBAL-EXPANSION-INCOME-V1
Wave:        CGEV2_AGENT_CONTEXT_SURVIVAL
Node:        AGENT_CONTEXT_PACK_BUILD
Lease:       LSE-UEX-AGENT-CONTEXT-20260902T002200-31
Scope:       github:agent_context/**
Authority:   DERIVED CONTINUITY ONLY
```

This session must not mutate domain applications, payments, submissions, RuntimeGraph adapter projections, or root continuity files currently leased by another writer.

## Active concurrent sessions

### RG2.2 source adapters / self-heal
- Session: `SES-UEX-CHATGPT-20260902T001630-27`
- Agent: `AGT-RUNTIMEGRAPH-SOURCE-ADAPTERS-SELFHEAL`
- Lease: `LSE-UEX-RUNTIMEGRAPH-ADAPTERS-20260902T001630-27`
- Status: ACTIVE at snapshot.
- Owns `runtime_v2/adapters/**`, projection health/repair code and derived Command Center projection tabs.
- Canonical application truth remains read-only.

### Root continuity handoff sealer
- Session: `SES-UEX-CHATGPT-20260902T002030-30`
- Agent: `AGT-CONTINUITY-HANDOFF-SEALER`
- Lease: `LSE-UEX-HANDOFF-20260902T002030-30`
- Status: ACTIVE at snapshot.
- Owns root `STATE.md`, `HANDOFF.md`, `CHANGELOG.md`, checkpoint/recovery-pack refresh.
- Current target includes CONVIVIAL FOODSCAPES continuity; no domain gate promotion.

## Recently completed sessions

### Browser Stack Supervisor
- Session: `SES-UEX-CHATGPT-20260902T000500-29`
- Node: `BROWSER_STACK_SUPERVISOR_V1_RELEASED`
- PR #49 merged.
- Main: `d1d82b0dbb8d5712888cef7d247b2487f9fd7514`.
- CI: `33565691506`, `33565691512` SUCCESS.

Coordination caveat: owning session is COMPLETED but its lease row was last observed ACTIVE. Treat as stale coordination debt; do not assume new overlapping Browser Stack write authority until reconciled.

### Browser Relay MCP
- Session: `SES-UEX-CHATGPT-20260901T234518-28`
- COMPLETED / lease RELEASED.

### Browser Worker
- Session: `SES-UEX-CHATGPT-20260901T232100-27`
- COMPLETED / lease RELEASED.

### RuntimeGraph dispatcher live cycle
- Session: `SES-UEX-AUTO-20260901T233539-28`
- COMPLETED / lease RELEASED.
- Human Frontier after cycle: STEP, COMPASS, CIVIS LAB, SABER.

## Multi-agent write protocol

Before any canonical write:

1. Register a unique `Agent_Sessions` row.
2. Read active, unexpired `Work_Leases`.
3. Acquire smallest non-overlapping lease.
4. Emit idempotent Event Bus events.
5. Verify output/read-back.
6. Recompute projections only after authority changes.
7. Release lease with explicit handoff.

Unregistered sessions are read-only.

## Session resumption rule

A successor must never reuse this session ID for writing. It creates a fresh session, references this session as parent/input, reads events after this snapshot watermark, and acquires a new lease.