# UE-Xchanges-OS — Agent Context Pack

This directory is a **derived zero-context recovery projection**. It exists so a new agent can orient quickly without using chat memory.

It never overrides canonical authorities.

## Mandatory bootstrap

Machine-readable contract: `bootstrap_manifest.json`.

Slow-changing semantic memory: [`../MEMORY.md`](../MEMORY.md).

Every compliant writer must:

1. follow `bootstrap_manifest.json`;
2. read the required public/private context;
3. create a fresh Session ID;
4. emit `SESSION_STARTED`;
5. emit `BOOTSTRAP_CONTEXT_LOADED` with the manifest version, observed main SHA and private watermark;
6. refresh current main, currently unexpired leases, Event Bus tail and control-plane health;
7. evaluate generic `WriterAuthorization` for the exact proposed lease/scope/intent;
8. only after a positive decision, emit `WRITER_AUTHORIZATION_GRANTED` carrying one `UEX_WRITER_AUTHORIZATION_RECEIPT@1.0.0` bound to that exact lease;
9. only then acquire the write lease, referencing the receipt ID + authorization decision digest;
10. execute within the lease and release it durably.

A Writer Authorization Receipt is coordination evidence only. It is **not** domain authority, browser/provider capability, payment permission, authentication authority or Submit permission.

The pack is navigation. `MEMORY.md` is semantic memory. Neither is live domain authority.

## Files

- `bootstrap_manifest.json` — mandatory machine-readable read/handshake/authorization/write order.
- `context.md` — watermarked non-sensitive project snapshot and authority map.
- `progress.md` — completed milestones, active work, debt and next milestones.
- `goals.md` — concise goal projection; canonical authority remains `../goal.md`.
- `checkpoints.md` — checkpoint/event/release index.
- `session.md` — snapshot of agent sessions/leases.
- `runtimegraph.md` — RuntimeGraph + Form Gateway execution topology.
- `knowledge.md` — known facts, unknowns and forbidden inference rules.
- `recovery.md` — cold-start algorithm.

Additional mandatory coordination contracts are declared by the manifest, including:

- `../docs/WRITER_AUTHORIZATION_AND_RELIABILITY_WATCHDOG.md`
- `../docs/WRITER_AUTHORIZATION_RECEIPT.md`

## Authority rule

If this pack conflicts with a newer official source, organiser/receipt, Drive Event Bus, current unexpired lease, root checkpoint, or current GitHub main, **this pack loses**.

## Snapshot watermark

The Markdown files in this directory are snapshots and may age independently of the manifest/bootstrap contract.

Always read their own watermark and then refresh live authorities.

The original survival-pack snapshot was:

```text
2026-09-02 00:22 Europe/Madrid
session: SES-UEX-CHATGPT-20260902T002200-31
baseline main: d1d82b0dbb8d5712888cef7d247b2487f9fd7514
observed event watermark: EVT-20260902T002200-HOFF-002
```

Do not treat that watermark as current state.

## Fast cold start

```text
CURRENT_GITHUB_MAIN_SHA
→ goal.md
→ AGENTS.md
→ MEMORY.md
→ agent_context/bootstrap_manifest.json
→ required writer-authorization contracts
→ LIVE-STATE-OVERRIDE.json
→ newest STATE.md / HANDOFF.md / checkpoint
→ agent_context watermarked navigation files
→ Drive Context_Registry / Agent_Sessions / unexpired Work_Leases / Event Bus tail
→ RuntimeGraph Command Center + cursors + dead letters
→ fresh Gmail / official sources when relevant
→ NEW session
→ SESSION_STARTED
→ BOOTSTRAP_CONTEXT_LOADED
→ refresh main + leases + events + health
→ WriterAuthorization(ALLOWED)
→ WRITER_AUTHORIZATION_GRANTED(receipt)
→ acquire fresh narrow lease referencing receipt
→ execute
```

Never reuse the snapshot session ID for writes. Never reuse one authorization receipt for a different lease or changed scope.
