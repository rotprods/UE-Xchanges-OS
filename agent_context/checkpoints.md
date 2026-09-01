# UE-Xchanges-OS — Checkpoint Index

> Derived index. Newer official evidence / Drive Event Bus / root checkpoint overrides this file.

## Current recovery watermark

- Snapshot time: **2026-09-02 00:22 Europe/Madrid**
- GitHub `main`: **`d1d82b0dbb8d5712888cef7d247b2487f9fd7514`**
- Current agent-context session: `SES-UEX-CHATGPT-20260902T002200-31`
- Lease: `LSE-UEX-AGENT-CONTEXT-20260902T002200-31`
- Latest domain continuity event observed: `EVT-20260902T002200-HOFF-002`

## Recent durable checkpoints

### CGEV2 survival — 2026-09-01
Established root `STATE.md`, `HANDOFF.md`, `CHANGELOG.md`, checkpoint and Drive recovery pack; chat no longer required for cold start.

### RuntimeGraph V2 closed loop
Event: `EVT-20260901T223000-RG2-007`
Released incremental reducer, evidence→claim registry, Form bridge, receipt reconciler and Human Command Center.

### RuntimeGraph V2.1 dispatcher
Event: `EVT-20260902T001630-DSP-006`
Released normalized ingress, source cursors, idempotent routing, retries/dead-letter semantics and frontier-change projection.

### First live dispatcher cycle
Event: `EVT-20260901T234155-DSPC-008`
Human Frontier became: Step Into Paralympics, COMPASS, CIVIS LAB, SABER. Receipts remained 0.

### Browser Worker v1
Event: `EVT-20260901T234322-BW-004`
PR #47 → `ba79fe5c…`. Persistent loopback Chromium; INSPECT→PREFILL_LOCAL→VALIDATE_LOCAL on same DOM; Submit absent.

### Browser Relay MCP v1
Event: `EVT-20260902T000251-RELAY-003`
PR #48 → `c10c7a44…`. Exactly four MCP tools; local PREFILL requires HMAC capability; worker remains loopback-only.

### Browser Stack Supervisor v1
Owning session: `SES-UEX-CHATGPT-20260902T000500-29`
PR #49 → `d1d82b0d…`.
Main CI: `33565691506` SUCCESS and `33565691512` SUCCESS.
One stdio MCP command supervises Relay + ephemeral-token Worker. External targets and Submit remain absent.

### CONVIVIAL FOODSCAPES continuity
Event: `EVT-20260902T002200-HOFF-002`
Canonical opportunity row already exists; P1; deadline 2026-09-15; `AI_UNKNOWN`; full-November availability unresolved; not Mass-Apply-enqueued. Canonical opportunity count becomes 176.

## Active snapshot writers

- RG2.2 adapters/self-heal: `SES-UEX-CHATGPT-20260902T001630-27` / `LSE-UEX-RUNTIMEGRAPH-ADAPTERS-20260902T001630-27`.
- Root continuity sealer: `SES-UEX-CHATGPT-20260902T002030-30` / `LSE-UEX-HANDOFF-20260902T002030-30`.
- Agent-context pack: `SES-UEX-CHATGPT-20260902T002200-31` / `LSE-UEX-AGENT-CONTEXT-20260902T002200-31`.

## Known stale/contradictory checkpoint signals

- Dashboard still says 175 opportunities and old GitHub main; latest event says 176 and current main is `d1d82b0d…`.
- Root `STATE.md/HANDOFF.md` were last observed at 18:11 and do not yet contain Browser Worker/Relay/Stack V1; an active sealer owns their refresh.
- Browser Stack session is COMPLETED but its Work_Lease row was last observed ACTIVE. Reconcile before overlapping Browser Stack writes.

## Cold-start checkpoint rule

Read the newest root checkpoint and Drive tail **after** this index. This file is a map, not the final authority.