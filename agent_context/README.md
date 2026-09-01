# UE-Xchanges-OS — Agent Context Pack

This directory is a **derived zero-context recovery projection**. It exists so a new agent can orient quickly without using chat memory.

It never overrides canonical authorities.

## Files

- `context.md` — current non-sensitive project snapshot and authority map.
- `progress.md` — completed milestones, active work, debt and next milestones.
- `goals.md` — concise goal projection; canonical authority remains `../goal.md`.
- `checkpoints.md` — checkpoint/event/release index.
- `session.md` — current and concurrent agent sessions/leases.
- `runtimegraph.md` — RuntimeGraph + Form Gateway execution topology.
- `knowledge.md` — known facts, unknowns and forbidden inference rules.
- `recovery.md` — cold-start algorithm.

## Authority rule

If this pack conflicts with a newer official source, organiser/receipt, Drive Event Bus, active lease, root checkpoint, or current GitHub main, **this pack loses**.

## Snapshot watermark

```text
2026-09-02 00:22 Europe/Madrid
session: SES-UEX-CHATGPT-20260902T002200-31
baseline main: d1d82b0dbb8d5712888cef7d247b2487f9fd7514
observed event watermark: EVT-20260902T002200-HOFF-002
```

## Fast cold start

```text
goal.md
→ LIVE-STATE-OVERRIDE.json
→ newest STATE/HANDOFF/checkpoint
→ AGENTS.md
→ Drive sessions + leases + Event Bus tail
→ fresh Gmail / official sources
→ agent_context/context.md + progress.md + runtimegraph.md as navigation
→ acquire fresh lease
→ execute
```

Never reuse the snapshot session ID for writes.