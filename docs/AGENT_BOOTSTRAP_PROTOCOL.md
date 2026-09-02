# UE-Xchanges-OS — Agent Bootstrap Protocol v1.1

## Purpose

Make zero-context recovery **mandatory, fail-closed and auditable** for every agent that can write to UE-Xchanges-OS.

The existence of recovery documents is not enough. A compliant writer must prove that it loaded current context **and** that the generic writer-authorization broker approved one exact proposed lease before that lease is acquired.

Machine-readable contract: `agent_context/bootstrap_manifest.json`.

Supporting contracts:

- `docs/WRITER_AUTHORIZATION_AND_RELIABILITY_WATCHDOG.md`
- `docs/WRITER_AUTHORIZATION_RECEIPT.md`

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

A `WriterAuthorizationReceipt` is **coordination evidence only**. It never means a domain mutation, payment, authentication, browser/provider operation or Submit is permitted.

## Mandatory cold start

Every writer must execute the bootstrap manifest before any write lease is acquired.

### Phase A — public/versioned context

1. Record current GitHub `main` SHA.
2. Read `goal.md`.
3. Read `AGENTS.md`.
4. Read `MEMORY.md`.
5. Read `agent_context/bootstrap_manifest.json`.
6. Read `LIVE-STATE-OVERRIDE.json`.
7. Read current `STATE.md` and `HANDOFF.md`.
8. Read `agent_context/README.md` and the required files declared in the manifest.
9. Read the writer-authorization contracts declared by the manifest.
10. Read the newest relevant checkpoint.

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

This acknowledgement establishes bootstrap compliance. It does **not** yet authorize a lease.

## Writer authorization law

Immediately before a write lease is acquired:

1. refresh current GitHub main if code/docs are in scope;
2. refresh currently unexpired leases;
3. refresh Event Bus tail;
4. produce/refresh a current `ControlPlaneHealthReport`;
5. inventory explicit overlapping unexpired lease IDs for the proposed scope;
6. construct the exact proposed lease identity/scope/intent;
7. run generic `authorize_writer(...)`;
8. if the decision is denied, remain read-only and do not acquire the lease;
9. if allowed, issue one `UEX_WRITER_AUTHORIZATION_RECEIPT@1.0.0` bound to that exact proposal;
10. append `WRITER_AUTHORIZATION_GRANTED` with the receipt payload;
11. only then create/acquire the lease row/event.

The subsequent `LEASE_ACQUIRED` evidence must reference:

```text
authorization_receipt_id
authorization_decision_digest
writer_authorization_receipt_version
```

Required order:

```text
SESSION_STARTED
→ BOOTSTRAP_CONTEXT_LOADED
→ PRELEASE REFRESH
→ CONTROL-PLANE HEALTH
→ WriterAuthorization(ALLOWED)
→ WRITER_AUTHORIZATION_GRANTED
→ LEASE_ACQUIRED
→ bounded write
```

A receipt is one proposed lease only. Changing lease ID, session, agent, context, main SHA, scope, intent, health snapshot or decision requires a new authorization/receipt.

## Receipt boundary

Receipt invariants:

```text
coordination_allowed = true
domain_authority      = false
external_capability   = false
```

The receipt default acquisition TTL is short-lived. The lease must be acquired while the receipt is valid. Historical audit later checks that acquisition occurred inside that authorization window; the receipt does not need to remain unexpired for the entire lease lifetime.

Do not add HMAC or browser credentials to the receipt. Browser/Form capability tokens remain a separate security boundary.

`EXTERNAL_SIDE_EFFECT` remains denied by generic WriterAuthorization and requires a separately versioned capability contract.

## Lease acquisition law

A stale historical row containing the word `ACTIVE` is not enough to block forever. Status, expiry, heartbeat and later release/takeover events must be reconciled.

The lease remains the actual fencing token after acquisition. The authorization receipt is proof that acquiring that fence was allowed; it is not a substitute for the fence.

## Write law

For every material transition:

```text
READ CURRENT AUTHORITY
→ VERIFY VALID AUTHORIZATION RECEIPT / CLAIM NARROW LEASE
→ EXECUTE BOUNDED OPERATION
→ READ BACK EXACT TARGET
→ EMIT IDEMPOTENT EVENT
→ RECOMPUTE ONLY AFFECTED DERIVED PROJECTIONS
→ RELEASE
```

A writer may not silently widen its scope. Scope expansion requires a new writer-authorization evaluation, a new receipt and an appropriately scoped lease before touching the additional resource.

## Migration law

Writer Authorization Receipt enforcement is **non-retroactive**.

- leases acquired before bootstrap manifest v1.1 becomes authoritative are not violations merely because receipts did not yet exist;
- already-running sessions must refresh the manifest before their **next lease acquisition**;
- an already-acquired valid lease is not retroactively invalidated by the v1.1 release;
- new post-v1.1 leases must follow the receipt sequence.

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

Before each material mutation it must refresh Event Bus + leases. If `AGENTS.md`, `MEMORY.md` or the bootstrap manifest materially changes during a long-running session, refresh those contracts before continuing significant work.

After v1.1, a session that bootstrapped under v1.0 may finish an already-acquired lease, but it must refresh v1.1 and issue `WRITER_AUTHORIZATION_GRANTED` before acquiring another write lease.

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

`tests/test_agent_bootstrap_contract.py` enforces repository-level invariants including:

- mandatory files exist;
- manifest version/sequence declares bootstrap ACK + WriterAuthorization + authorization receipt before lease;
- AGENTS and HANDOFF reference the manifest/MEMORY/context pack;
- MEMORY declares itself non-authoritative and forbids volatile counts;
- receipt contract is listed as a required read;
- forbidden shortcuts explicitly reject post-v1.1 lease acquisition without receipt.

CI cannot prove a remote agent actually read a file or emitted a real Event Bus event. The operational Event Bus sequence and later lease↔receipt audit supply that proof.
