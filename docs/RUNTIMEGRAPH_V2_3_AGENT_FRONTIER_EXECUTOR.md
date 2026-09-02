# RuntimeGraph V2.3 — Autonomous Agent Frontier Executor

Status: implementation contract.

## Objective

RG2.3 closes the gap between **knowing the next reversible agent action** and actually executing it under bounded authority.

```text
Agent_Next
   ↓
select READY AGENT action
   ↓
autonomy safety gate
   ↓
action-level WorkLease
   ↓
lease_id = fencing token
   ↓
handler executes reversible evidence work
   ↓
verify evidence + exact application scope
   ↓
NormalizedIngress → RG2 dispatcher
   ↓
RuntimeGraph transition
   ↓
release action lease
   ↓
RG2.2 self-heal
   ↓
new Agent/Human Frontier
```

The runtime does **not** introduce another queue, database, worker service or scheduler. It composes existing `RuntimeGraph`, `WorkLease`, `ClosedLoopRuntime`, `AutonomousEventDispatcher` and RG2.2 projection repair.

## Authority ceiling

RG2.3 may execute only reversible, evidence-backed AGENT actions.

Default safe families:

```text
VERIFY_*
CAPTURE_*
INGEST_*
SCAN_*
PREPARE_*
EXTRACT_*
RECONCILE_*
CHECK_*
RESOLVE_*
```

Fail-closed tokens include:

```text
PAY / TRANSFER / PURCHASE / BOOK_TRAVEL
LOGIN / AUTH / PASSWORD / OTP / 2FA / CAPTCHA
COOKIE / PRIVATE_FIELD / SENSITIVE_FIELD
HUMAN_FINAL / APPLICANT_OWNED
RECORD_VIDEO
SUBMIT
SEND_EMAIL / SEND_MESSAGE / REPLY_EMAIL
EXTERNAL_PREFILL
```

Even if an upstream compiler accidentally labels one of these actions `AGENT`, RG2.3 refuses to claim it.

## Handler boundary

The pure runtime kernel does not own Gmail, browser or web connector credentials. The current tool environment supplies an `AgentActionHandler` for a safe action family.

A handler receives only:

```text
action_id
application_id
action_type
instruction
expected_output
priority
observed_at
value-safe metadata
```

It returns:

```text
disposition
stable evidence refs
optional NormalizedIngress events
single-line reason code
```

A successful action without durable evidence is invalid.

A handler may not return an ingress for another application. Cross-application output is a deterministic contract failure before dispatcher mutation.

## Action-level lease fencing

Each execution acquires:

```text
resource_type = runtime_action
resource_id   = <action_id>
lease_id      = unique takeover/claim ID
```

`lease_id` is the fencing token.

Why this is sufficient in the current architecture:

- every fresh takeover receives a different lease ID;
- the coordination kernel already requires mutating events to reference the supplied lease ID;
- an old/stale writer therefore cannot author a valid transition against a newer lease;
- no extra fencing database is justified yet.

An unexpired foreign action lease blocks execution. A released/expired lease may be taken over, but the takeover must receive a new ID and be evented.

## Retry model

Maximum repeated identical strategy attempts: **3**.

```text
attempt 1 fails transiently
→ WAITING + retry_at
→ release lease

retry_at reached
→ resume
→ fresh action lease/fencing token
→ attempt 2

attempt 3 still fails
→ action FAILED / strategy must change
```

External waiting is different from retryable failure. `WAITING_EXTERNAL_EVIDENCE` stays waiting until a source event reopens the action.

## Evidence law

`COMPLETED` requires at least one durable evidence reference.

Examples:

```text
official:<source-id>
gmail:<message-id>
formplan:<plan-id>
receipt:<receipt-id>
drive:<evidence-node-id>
```

Evidence values themselves, credentials and sensitive applicant fields are not execution-record payloads.

## Stable-ID control-plane writes

RG2.2 exposed a real concurrency defect: a cached Sheets row index changed after another writer appended rows.

RG2.3 establishes the mutation law:

```text
NEVER cache physical row number across writers.

Before every mutable Agent_Sessions / Work_Leases row update:
1. fresh-read table;
2. resolve exact stable entity ID;
3. fresh-read again at mutation boundary;
4. re-resolve / compare identity;
5. write only the fresh location;
6. fail closed on missing or duplicate ID.
```

`control_plane_rows.py` provides the provider-neutral invariant and regression tests. Connector agents must implement the same two-read stable-ID procedure.

## Cycle selection

The executor is bounded. Default operational policy:

```text
max_actions_per_cycle = 3
lease_ttl              = 10 minutes
action_retry_budget    = 3
```

Selection comes directly from RuntimeGraph ordering:

```text
priority DESC
→ deadline ASC
→ action_id
```

Human actions are never part of the agent cycle.

## Live tool-agent workflow

For each action:

```text
1. Read current Agent_Next and canonical source refs.
2. Resolve exact application/action identity.
3. Acquire action-level lease.
4. Perform reversible tool work.
5. Persist source evidence upstream.
6. Produce value-safe NormalizedIngress.
7. Dispatch incremental event.
8. Verify resulting evidence/gates/frontier.
9. Complete / WAIT / retry / fail action.
10. Release action lease.
11. RG2.2 self-heals derived surfaces.
```

The executor must never mark `SUBMITTED` or `RECEIPT_CONFIRMED` merely because it prepared or inspected an application.

## Current first live frontier

At the RG2.3 start watermark:

```text
I-PLAY
→ capture current infopack/form/funding/travel/fee/questions

Game of Nature
→ prepare participant route; GL remains blocked

Step Into Paralympics
→ wait for transport-date reply; application action is human-side

Building With Our Hands
→ verify receipt or valid late route after deadline

Receipt sweep
→ scan only after human actions; strong receipt contract still applies
```

Two newly discovered P1 opportunity nodes (`Unheard Voices`, `EC Youth Start-Up Challenge`) remain outside the application frontier until exact Application nodes/routes are created by the canonical domain workflow. RG2.3 must not synthesize mappings.

## Required gauntlet

- HUMAN action cannot be claimed.
- AGENT action containing SUBMIT/PAY/AUTH/HUMAN_FINAL cannot be claimed.
- no handler → no mutation.
- success without evidence is invalid.
- unexpired foreign action lease blocks.
- expired lease takeover receives a new fencing token.
- handler output for another application fails before dispatch.
- retry 1/2 resumes with fresh lease; third identical failure terminates the strategy.
- max actions per cycle is bounded.
- concurrent inserted Sheets row cannot redirect a stable-ID update.
- duplicate/missing stable IDs fail closed.
- no receipt/submission state may be inferred from action completion.

## Definition of Done

RG2.3 is complete when:

1. executor kernel and handler contracts exist;
2. safety denylist and safe-family allowlist are tested;
3. action-level leases/fencing are tested;
4. evidence requirement and cross-application isolation are tested;
5. retry budget is tested;
6. stable-ID row guard closes coordination issue #54 at the contract level;
7. exact-head CI passes and merge is green;
8. at least one live Agent_Next action is executed end-to-end through safe evidence → EventBus → updated frontier;
9. an hourly condition-watch is installed to run bounded executor cycles;
10. no payment, authentication, applicant-owned final text, external PREFILL or Submit is performed by the autonomous executor.
