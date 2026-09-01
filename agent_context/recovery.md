# UE-Xchanges-OS — Zero-Context Recovery Procedure

Use this when an agent starts with no trusted chat memory.

## 1. Establish authority

Read in this order:

1. `../goal.md`
2. `../LIVE-STATE-OVERRIDE.json`
3. newest root `STATE.md`
4. `../AGENTS.md`
5. `../ARCHITECTURE.md`
6. newest root `HANDOFF.md`
7. newest root checkpoint under `../checkpoints/`
8. this `agent_context/` pack as a derived navigation aid
9. private Drive `Context_Registry`, `Agent_Sessions`, `Work_Leases`, tail of `Agent_Event_Bus`
10. fresh Gmail/official sources since the latest event watermark

If these disagree, higher/newer authoritative evidence wins.

## 2. Verify live code state

Read current `main` rather than trusting a checkpoint SHA.
At this snapshot baseline:

```text
main = d1d82b0dbb8d5712888cef7d247b2487f9fd7514
PR #49 = merged
main test = 33565691506 SUCCESS
main browser-stack = 33565691512 SUCCESS
```

A later main supersedes these values.

## 3. Verify concurrency

Before any write:

- list ACTIVE sessions;
- list unexpired ACTIVE leases;
- inspect their resource IDs/scopes;
- acquire a new narrow lease only if disjoint or after explicit takeover/release event.

At this snapshot, RG2.2 adapters and a root continuity sealer are active. Do not overwrite their paths.

## 4. Reconstruct domain state

Read Drive opportunity/application rows and Event Bus; do not use Dashboard counts blindly.
At snapshot:

- latest canonical opportunity count signal: 176;
- Mass Apply/application nodes: 164;
- receipts: 0;
- Human Frontier: STEP, COMPASS, CIVIS LAB, SABER.

Dashboard was stale at 175 opportunities.

## 5. Reconstruct RuntimeGraph

- load current source cursors / dead letters;
- apply events after cursor;
- recompute derived state/frontiers;
- do not mutate canonical truth from a derived projection.

If RG2.2 is still ACTIVE, respect its lease and read its latest handoff before projection writes.

## 6. Reconstruct Form Execution capability

Current baseline stack:

```text
MCP Host
→ Browser Stack Supervisor
→ Browser Relay MCP
→ loopback Browser Worker
→ dedicated Chromium
```

Baseline capability ceiling:

```text
local inspect        YES
local validate       YES
local prefill        HMAC-gated
external inspect     NO
external prefill     NO
submit               NO
upload/payment       NO
cookie/storage leak  NO
```

Do not add Submit as part of recovery.

## 7. Search fresh external evidence

At each cycle:

- search Gmail for organiser replies after checkpoint;
- read full threads;
- check deadline-critical official forms/pages;
- reconcile reply → opportunity/application;
- persist truth in Drive;
- recompute RuntimeGraph;
- notify only genuinely new human-critical action.

## 8. Resume highest-value work

Default order unless new evidence changes it:

1. deadline/receipt-critical Human Frontier;
2. reversible Agent Frontier with deadline impact;
3. source adapters/cursor health;
4. paid trainer/facilitator/professional lanes;
5. provider certification for Form Gateway;
6. lower-priority source backlog.

## 9. End every session durably

Before exit:

- update session heartbeat/status;
- emit final idempotent events;
- verify read-back;
- release all owned leases;
- leave concise handoff with exact main SHA/event watermark/next action;
- never rely on chat text as sole state.