# UE-Xchanges-OS — Agent Bootstrap Protocol v1

## Purpose

Make zero-context recovery **mandatory and auditable** for every agent that can write to UE-Xchanges-OS.

The existence of recovery documents is not enough. A compliant writer must prove that it loaded current context before acquiring write authority.

Machine-readable contract: `agent_context/bootstrap_manifest.json`.

## Authority model

This protocol does not create a new source of domain truth.

```text
Official source / organiser / contract / receipt
  > private Drive CRM + evidence + Event Bus
  > current GitHub policy/code/recovery state
  > RuntimeGraph derived state
  > agent_context/** navigation
  > MEMORY.md semantic memory
  > UI/task projections
  > chat memory
```

`MEMORY.md` contains durable lessons only. `agent_context/**` is a derived recovery projection. Both lose to fresher authoritative evidence.

## Mandatory cold start

Every writer must execute the bootstrap manifest before any write lease is acquired.

### Phase A — public/versioned context

1. Record current GitHub `main` SHA.
2. Read `goal.md`.
3. Read `AGENTS.md`.
4. Read `MEMORY.md`.
5. Read `LIVE-STATE-OVERRIDE.json`.
6. Read current `STATE.md` and `HANDOFF.md`.
7. Read `agent_context/README.md` and the required files declared in `bootstrap_manifest.json`.
8. Read the newest relevant checkpoint.

Do not assume counts embedded in old documents are live.

### Phase B — private/live context

Read:

- `Context_Registry`;
- `Agent_Sessions`;
- currently unexpired `Work_Leases`;
- `Agent_Event_Bus` after the stored cursor/watermark;
- relevant RuntimeGraph V2 Command Center projections/cursors/dead letters;
- fresh Gmail/official-source deltas when the intended action depends on external state.

### Phase C — session handshake

Create a **new** Session ID. Never reuse a historical Session ID for writing.

Append:

1. `SESSION_STARTED`;
2. `BOOTSTRAP_CONTEXT_LOADED`.

`BOOTSTRAP_CONTEXT_LOADED` must include or reference:

- bootstrap manifest version;
- observed current main SHA;
- context ID;
- public read-set refs/hash;
- private Event Bus watermark;
- lease scan timestamp;
- agent ID;
- session ID.

Only after that event may the session acquire a write lease.

## Lease acquisition law

Immediately before lease acquisition:

1. refresh current GitHub main if code/docs are in scope;
2. refresh currently unexpired leases;
3. refresh Event Bus tail;
4. verify no overlapping active lease;
5. acquire the smallest safe scope.

A stale historical row containing the word `ACTIVE` is not enough to block forever. Status, expiry, heartbeat and later release/takeover events must be reconciled.

## Write law

For every material transition:

```text
READ CURRENT AUTHORITY
→ CLAIM NARROW LEASE
→ EXECUTE BOUNDED OPERATION
→ READ BACK EXACT TARGET
→ EMIT IDEMPOTENT EVENT
→ RECOMPUTE ONLY AFFECTED DERIVED PROJECTIONS
→ RELEASE
```

A writer may not silently widen its scope. Scope expansion requires an Event Bus record before touching the additional resource.

## Memory law

Use `MEMORY.md` only for:

- durable architecture laws;
- durable mission/policy decisions;
- recurring failure patterns;
- long-lived evidence-handling rules;
- safe cross-session lessons.

Do not store:

- current opportunity/application counts;
- current Human/Agent Frontier membership;
- deadline-sensitive statuses;
- current lease ownership;
- applicant PII/private answers;
- receipt IDs/private evidence;
- secrets/cookies/tokens.

Volatile state belongs in Drive, `STATE.md`, `HANDOFF.md`, checkpoints and watermarked `agent_context/**` snapshots.

## Existing-session rule

An already-running session does not magically learn a repository update.

Before each material mutation, it must refresh Event Bus + leases. If `AGENTS.md`, `MEMORY.md` or the bootstrap manifest materially changes during a long-running session, the session must refresh those contracts before continuing significant work.

A future dispatcher may emit `BOOTSTRAP_CONTRACT_UPDATED` to make this refresh explicit, but absence of that event does not remove the read-before-write duty.

## Handoff law

Before session close:

- refresh main/events/leases;
- persist material knowledge in the appropriate authority;
- update derived recovery artifacts only if within lease;
- record exact PR/commit/CI evidence actually observed;
- release every lease;
- emit `SESSION_COMPLETED`.

Do not dump volatile state into `MEMORY.md` as a shortcut.

## Compliance

`tests/test_agent_bootstrap_contract.py` enforces repository-level invariants:

- mandatory files exist;
- manifest is strict and declares `BOOTSTRAP_CONTEXT_LOADED`;
- AGENTS and HANDOFF reference the manifest/MEMORY/context pack;
- MEMORY declares itself non-authoritative and forbids volatile counts;
- required cold-start ordering markers remain present.

CI cannot prove a remote agent actually read a file. The Event Bus handshake supplies the operational audit trail.
