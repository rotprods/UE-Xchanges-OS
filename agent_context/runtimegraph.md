# UE-Xchanges-OS — RuntimeGraph Recovery Map

Seal: `2026-09-21T21:59:00+02:00`  
Baseline main: `c0c31fed602a1ad774a7c6416a4abd7e09d26dde`

> RuntimeGraph is a derived read model, never canonical domain truth.

## Current status

`STALE_VS_EVENTBUS`.

The global RuntimeGraph still carries historical source revision/watermark data older than current provider/CRM/EventBus evidence. Targeted overlays do not make the global projection current.

## Required rebuild order

```text
fresh provider/Gmail/form evidence
→ canonical Applications/EventBus exact-ID reconciliation
→ deterministic RuntimeGraph full rebuild
→ Command_Center watermark/readback
→ Human_Now/Agent_Next/Source_Cursors/Dead_Letters validation
```

Do not patch canonical CRM to match RuntimeGraph and do not add another targeted overlay as a substitute for a full rebuild.

## Validation conditions for CURRENT

- Command_Center watermark is at or after the canonical reconciliation event set used as input;
- Human_Now contains no expired deadline instructions or superseded provider actions;
- Agent_Next contains no terminal/closed action as READY;
- receipt counts include only strong exact-identity evidence;
- Source_Cursors represent current adapter progress;
- Dead_Letters are reviewed.

## Execution boundary

RuntimeGraph may navigate exact-ID work only after freshness validation. It does not grant provider/email/form Submit/auth/payment capability. Semantic similarity never authorises mutations.

## Next milestone

The next RuntimeGraph milestone is **FULL_DETERMINISTIC_REBUILD_AFTER_CANONICAL_P0_RECONCILIATION**, not a historical scheduler-canary milestone.
