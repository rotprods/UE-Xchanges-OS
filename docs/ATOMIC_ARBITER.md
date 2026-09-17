# UE-Xchanges-OS — Atomic Coordination Arbiter v1

Status: **WAVE 1 — DATABASE/CONTRACT IMPLEMENTATION**

## Problem proved by live recovery

The private Drive/EventBus control plane is valuable evidence and coordination state, but read-before-write over Google Sheets is not a transactional mutex across independent agents. Two agents can observe the same scope as free before either write becomes visible.

This arbiter is the smallest repair for that demonstrated race. It is **not** a new CRM, RuntimeGraph, memory system, scheduler or application database.

Wave 1 proves the transaction/fencing/effect semantics in ephemeral PostgreSQL CI. It does not deploy a production database and does not grant email/form/provider capability.

## Authority boundary

```text
official/provider/receipt truth
        ↓
private CRM + EventBus domain truth
        ↓
Atomic Arbiter = mutation/effect exclusion only
        ↓
RuntimeGraph / task projections
```

The arbiter answers only:

- who currently owns an exact mutation scope;
- which monotonic fencing token is current;
- whether an external effect identity has already been reserved/started/resolved;
- which coordination event still needs mirroring to Drive.

It never decides eligibility, application content, selection, receipt truth, payment, or provider policy.

## Minimal durable schema

Namespace: `uex_arbiter`.

1. `agent_sessions` — unique execution identities.
2. `work_leases` — one mutable lease per session, with monotonic `fencing_token`.
3. `scope_owners` — one current owner per elementary scope.
4. `external_effects` — operational at-most-once ledger.
5. `coordination_outbox` — transactionally co-written events for later Drive/EventBus mirroring.

The database clock is the only lease-time authority.

## Atomic scope claim

`claim_scope_set()`:

1. rejects empty/duplicate scopes;
2. canonicalises and sorts the set;
3. takes PostgreSQL transaction advisory locks in that deterministic order;
4. expires stale leases using `clock_timestamp()`;
5. rejects a second active mutable lease for the same session;
6. rejects any live foreign owner of any requested scope;
7. increments the global fencing sequence;
8. inserts the lease + all scope owners + outbox event in the same transaction.

All scopes are acquired or none are.

Example application mutation scope:

```text
APPLICATION:app-ticket2europe-lead-right-2026-v1
ORGCALL:ticket2europe:lead-right-2026
```

A worker carrying an older fencing token is a zombie and every mutation must reject it.

## External effect state machine

```text
ABSENT
  ↓ reserve
RESERVED
  ├─→ CANCELLED_BEFORE_START ─→ new reservation allowed
  ↓ provider invocation begins
STARTED
  ├─→ CONFIRMED            [terminal]
  ├─→ FAILED_NO_EFFECT     [new reservation allowed]
  └─→ UNCERTAIN
          ├─→ CONFIRMED    [terminal]
          └─→ FAILED_NO_EFFECT [new reservation allowed]
```

Critical invariant:

```text
STARTED / UNCERTAIN / CONFIRMED => NO BLIND RETRY
```

A timeout after provider invocation is uncertainty, never proof of failure.

A new worker may take the application scope after lease expiry, but if the effect is `STARTED` or `UNCERTAIN` its task is **reconciliation**, not replay.

## Effect identity is operational, not payload-based

Initial effects must not change merely because wording or source revision changes.

Reference keys from `src/uexchanges/atomic_arbiter.py`:

```text
v1:EMAIL_INITIAL:<application_id>
v1:FORM_INITIAL:<application_id>:<form_id>
v1:EMAIL_FOLLOWUP:<application_id>:<followup_number>
v1:EMAIL_REPLY:<thread_id>:<inbound_message_id>:<purpose>
```

A form resubmission gets a distinct identity only when tied to explicit provider-authorisation evidence. Changing an answer alone cannot mint a second initial-submit permission.

## Transactional outbox

Every successful lease/effect transition writes a `coordination_outbox` row in the same PostgreSQL transaction.

Therefore:

- DB commit + Drive mirror failure leaves a replayable outbox event;
- failed scope/effect claims do not create false success events;
- eventual Drive/EventBus mirroring can be idempotent using `idempotency_key`.

Wave 1 does not implement the mirror worker; that is a later integration wave.

## Security posture

The SQL revokes schema/table/sequence/function rights from `PUBLIC`. Production deployment must grant only a dedicated trusted server role. Client/browser/anon Supabase roles must never receive direct mutation rights.

No existing unrelated Supabase project is reused implicitly. Production deployment requires an explicitly selected/dedicated project and a separate migration/review wave.

## CI gauntlet

Wave 1 must pass both the dependency-free Python suite and a PostgreSQL 16 service job. The integration job proves at least:

- 50 simultaneous contenders for one scope => exactly one winner;
- opposite-order multi-scope claims => no deadlock, one winner;
- one active mutable lease per session;
- expired takeover => strictly larger fencing token;
- old fencing token cannot heartbeat/mutate;
- concurrent reservation of one external effect => exactly one winner;
- process death after `STARTED` => later reservation blocked;
- `UNCERTAIN` remains blocked until authoritative reconciliation;
- `CONFIRMED` cannot be reserved again;
- failed conflicting claim creates no false outbox event;
- release removes scope ownership and invalidates the old fence.

## Wave boundary

Wave 1 ends when the SQL/Python contract is merged to `main` with exact-head PR CI and main-push CI green.

It intentionally does **not**:

- deploy production Supabase;
- change the private CRM or RuntimeGraph schema;
- send email;
- call TinyFish/provider forms;
- migrate historical effects;
- enforce gateway-only execution in production.

Those require subsequent independently fenced waves.
