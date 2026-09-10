# RG2.2 Scheduled Production Canary

Status: fail-closed operational runbook for **one** scheduled production-path canary.
It does not authorize recurring scheduling, Agent_Next execution, canonical-domain
mutation, authentication, payment, PREFILL, or Submit.

## 1. Authority and session

1. Resolve current GitHub `main`.
2. Read `AGENTS.md` and `agent_context/bootstrap_manifest.json` from that main.
3. Read every public/private item required by the manifest.
4. Create a **new unique** session ID. Never reuse a prior session ID for writes.
5. Emit `SESSION_STARTED`, then `BOOTSTRAP_CONTEXT_LOADED` with the manifest-required
   public-read proof, private EventBus watermark, lease scan time, agent ID, session
   ID, context ID, manifest version, and observed main SHA.
6. Only currently **unexpired** `Work_Leases` are live fences. An old row that still
   says `ACTIVE` after `expires_at` is historical hygiene debt, not live authority.

## 2. Bounded normal-writer health

Do not perform full historical archaeology in the authorization critical path.
Historical hygiene belongs to the watchdog / `CONTROL_PLANE_REPAIR` workflow.

Build authorization health from the exact evidence needed for the proposed normal
`DERIVED_PROJECTION` writer:

- exact stable-ID lookup of the new session; require exactly one row;
- the real `BootstrapGuard` decision for this exact session, ACK, proposed lease,
  current manifest, and prelease evidence;
- currently-unexpired leases only, plus exact owner-session rows for those live
  leases.

Use `uexchanges.bounded_writer_health.evaluate_bounded_writer_authorization_health`
when that helper is present on current main. Persist its scope metadata with any
health evidence; `historical_hygiene_evaluated=false` is not a global-green claim.

Required `DERIVED_PROJECTION` SLOs are exactly those required by current
`WriterAuthorization`: `bootstrap_compliance`, `session_identity_uniqueness`, and
`lease_fencing_integrity`. Any required SLO failure is fail-closed.

## 3. Authorization critical section

After broad bootstrap reads are complete, refresh only the critical inputs:

- current main SHA;
- live EventBus watermark;
- exact current-session uniqueness evidence;
- currently-unexpired leases and exact live owners;
- fresh bounded authorization health.

Then:

1. Evaluate the real `WriterAuthorization` broker for one exact unique RG2.2
   `DERIVED_PROJECTION` lease.
2. Issue the canonical content-addressed `WriterAuthorizationReceipt` with
   `ttl_seconds=300` and the current `BootstrapPolicy` prelease-age limit.
3. Persist `WRITER_AUTHORIZATION_GRANTED`.
4. Acquire **that exact proposed lease immediately**. Do no unrelated work between
   receipt persistence and lease acquisition.
5. Exact-ID readback must prove the lease `ACTIVE` before source work.

If receipt/prelease evidence is genuinely stale, discard that receipt unused,
refresh the critical inputs, create a **new lease ID**, and retry once. Never reuse
an aged, denied, mismatched, or failed receipt.

An unexpired overlapping source/projection lease means yield and terminal close.
`runtime_action` leases never authorize RG2.2 to execute `Agent_Next`.

## 4. Source micro-batch

A canary is not a backlog drain. Process at most **one adapter slice**:

1. canonical strong-receipt evidence inbox when nonempty; otherwise
2. the oldest/most-overdue due cursor among Gmail organiser replies,
   Form Gateway safe evidence, and authoritative official source.

Hard budget per activation:

- at most 5 new/late-unique source candidates;
- at most 2 exact `application_id` / `opportunity_id` subgraphs;
- never a second adapter in the same activation.

If more candidates remain, preserve a continuation boundary and never advance a
cursor past unprocessed evidence.

Authority rules:

- only explicit adapter-contract facts can change derived state;
- Gmail raw prose or absence is never authority and cannot directly be a receipt;
- strong receipt requires canonical evidence bound to exact submission identity;
- never route by title, fuzzy match, similarity, or embeddings;
- at-least-once delivery, deterministic idempotency, monotonic cursors;
- same transient strategy at most 3 times;
- poison/unroutable normalized events go to `Dead_Letters`.

## 5. Derived reconciliation only

For the selected adapter and at most two affected subgraphs, rebuild deterministic
expected state and repair only actual mismatches on:

- `Command_Center`
- `Human_Now`
- `Agent_Next` (projection only; never execute it)
- `Claim_Registry`
- `Dispatcher_State`
- `Source_Cursors`
- `Dead_Letters`
- Todoist runtime projection, only with an exact persisted
  `runtime_action_id -> task_id` binding.

Never self-heal canonical `Opportunities`, `Applications`, `Mass_Apply_Queue`,
`Execution_Log`, `Agent_Event_Bus`, `Agent_Sessions`, `Work_Leases`,
`Autofill_Profile`, or `Human_Gates` as a RuntimeGraph projection repair.
Control-plane records may only be changed by their own coordination lifecycle or a
separately authorized `CONTROL_PLANE_REPAIR` plan.

## 6. Stable-ID mutation law

Immediately before every mutable coordination-row write, resolve the row again by
its stable entity ID. Never reuse a cached row index. Read the exact entity back
after writing. If a provider result is ambiguous, reconcile exact identity and
idempotency evidence before any retry.

## 7. Closure budget

Reserve the final **40%** of the activation for closure. Once closure begins, start
no new source/provider/projection operation.

Before reporting success:

1. read back every allowed mutation;
2. release every own lease by exact stable ID;
3. prove each lease `RELEASED`;
4. set the session terminal;
5. emit `SESSION_COMPLETED`.

If release + terminal session cannot be proven, report a coordination incident,
not success.

## 8. PASS contract

Only a fully successful scheduled run may append `SCHEDULER_PRODUCTION_CANARY_PASS`.
The payload must include:

- current main SHA;
- session ID;
- lease ID;
- receipt ID;
- bounded-health scope and required-SLO results;
- selected adapter and candidate count;
- continuation boundary when applicable;
- source result and projection result;
- Human Frontier before/after;
- strong receipt count;
- Dead_Letter count;
- cursor changes;
- Todoist mutation count;
- exact release readback;
- `historical_hygiene_green=false` unless independently proven;
- `recurring_production_enabled=false`.

A canary PASS does **not** by itself certify recurring production. Promotion
requires additional clean scheduled runs under the release policy.

## Absolute prohibitions

Never pay, authenticate, handle credentials/OTP/cookies, externally PREFILL,
irreversibly Submit, execute `Agent_Next`, infer receipt from Gmail, or fabricate a
terminal/domain state.
