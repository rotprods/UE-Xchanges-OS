# UE-Xchanges-OS — MEMORY.md

> **Durable semantic memory, not live state.**
>
> This file stores slow-changing lessons, invariants and recurring failure patterns that every agent should know before acting. It is deliberately **not** authoritative for volatile counts, deadlines, frontier membership, active leases, current opportunity states or receipt status.

## Authority

When this file conflicts with a newer source, the newer authoritative source wins:

1. current official source / authorised form / organiser confirmation / contract / receipt;
2. private Drive CRM + evidence graph + `Agent_Event_Bus`;
3. current GitHub policies, schemas, code and root recovery state;
4. RuntimeGraph derived state;
5. `agent_context/**`, Notion, Todoist, HubSpot and other projections;
6. chat memory.

Never use `MEMORY.md` to override a receipt, organiser reply, live lease, current form or newer checkpoint.

## Durable mission memory

- Project: `UE-Xchanges-OS`.
- Global context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`.
- Operating policy: **APPLY EVERYTHING VIABLE**. Priority orders execution; it does not exclude objectively viable routes.
- Portfolio objective: global mobility + remote-work continuity + progression toward paid trainer/facilitator and adjacent international work.
- Submission north star: receipt-backed applications per live Spain-compatible opportunity.

## Durable truth rules

- `UNKNOWN` is verification debt, never permission.
- `ROUTE_QUERY_SENT != APPLICATION_SUBMITTED`.
- `ELIGIBLE != SELECTED`.
- `INVITED_TO_APPLY != ACCEPTED`.
- `PAYMENT_REQUIRED_FOR_PLACE != CONFIRMED`.
- `SubmissionAttempt != SubmissionReceipt`.
- Todoist completion, Notion status, open form, draft asset, organiser encouragement or an agent statement are never submission evidence.
- Latest authoritative evidence may supersede an older state; latest edit timestamp alone does not establish authority.
- Never majority-vote conflicting facts. Preserve conflict and route to verification.

## Durable multi-agent memory

- Chat memory is never the continuity system.
- Every writer creates a unique Session ID. Never reuse an old session for writes.
- Every writer reads current main, bootstrap manifest, Drive sessions, **currently unexpired** leases and Event Bus tail before mutation.
- A writer must emit `BOOTSTRAP_CONTEXT_LOADED` before acquiring a write lease.
- A lease is a fencing token for its exact scope, not a global lock.
- Expired/released leases do not block; stale rows must be reconciled rather than blindly trusted.
- Every material mutation emits an append-only event and is read back before closure.
- Projection divergence is a real defect: fix or explicitly log it before declaring a wave complete.
- Never claim a GitHub PR/merge/CI result before GitHub itself proves it. If Drive and GitHub disagree about code state, GitHub is authoritative for code/CI.

## Durable memory model

Use the following separation:

```text
Official evidence / receipts      = external truth
Drive CRM + Event Bus             = canonical operational truth
GitHub policies/code/recovery     = versioned system contract
RuntimeGraph                      = derived execution truth
agent_context/**                  = derived zero-context navigation
MEMORY.md                         = slow-changing semantic memory
Notion / Todoist / HubSpot        = reconstructible projections
chat                              = disposable working context
```

Do **not** store live counts or transient frontier membership in this file. Those belong in `STATE.md`, `HANDOFF.md`, current checkpoints, `LIVE-STATE-OVERRIDE.json`, Drive and `agent_context/context.md` with explicit watermarks.

## Durable profile/evidence memory

- Historical programme participation does not prove current youth-worker, trainer, facilitator or group-leader status.
- Attendance never implies delivery responsibility.
- Do not infer degree, CEFR, safeguarding, first aid, disability/fewer-opportunities status, work rights, student status, current affiliation, experience duration or sensitive personal facts.
- Search `Autofill_Profile` and `Profile_Interview` before asking Roberto for information already persisted.
- Private applicant values, answers, identity details and restricted evidence never belong in public GitHub.

## Durable Form Execution Gateway memory

The Form Execution Gateway exists to remove the manual form bottleneck without weakening evidence or secret boundaries.

Persistent rules:

- secrets remain local to the authenticated browser/runtime;
- passwords, OTP, cookies and storage state are not model outputs;
- BLACK fields are human-only;
- RED fields require human confirmation;
- AI policy controls narrative assistance;
- fingerprint + validation signature + canonical payload form the execution identity;
- approval tokens are short-lived and bound to the exact plan;
- duplicate/ambiguous submission attempts block blind retry;
- **clicking Submit is not proof of submission**;
- only receipt/authoritative confirmation may advance submission truth.

Current capability state must always be read from current code/recovery artifacts. `MEMORY.md` must never be used to infer that external PREFILL or Submit is enabled.

## Durable RuntimeGraph memory

- RuntimeGraph is derived, never a second opportunity/application authority.
- Execution law: `READ → READY FRONTIER → CLAIM UNDER LEASE → EXECUTE → VERIFY → EMIT EVENT → RECOMPUTE`.
- Exact entity/application IDs are required for state-changing routing.
- Source cursors are monotonic ingestion watermarks, not source authority.
- Late unique events may still be processed idempotently; never rewind a cursor to represent them.
- Dead-letter after bounded retry rather than silently dropping or looping forever.
- Human-only irreversible actions remain separated from reversible agent work.

## Recurring failure patterns to remember

1. **Stale dashboard / stale snapshot** — aggregate projections may lag canonical events.
2. **Prepared != submitted** — forms, drafts and email queries have repeatedly been mistaken for application evidence.
3. **Outcome proves historical application but not its timestamp** — preserve `UNRECOVERED` rather than fabricate provenance.
4. **Stale lease flag** — a session may be completed while an old lease row still says ACTIVE; expiry/event evidence matters.
5. **Premature merge claim** — never record a PR as merged before GitHub proves it.
6. **Projection column/schema drift** — read-back exact target cells/IDs after mutation.
7. **Source-access block != processed** — inaccessible Telegram/source items remain unresolved.
8. **Provider session != agent authority** — being logged in does not grant PREFILL or Submit capability.
9. **A capability is not a credential** — local HMAC authorization may permit one bounded operation but must not expose browser secrets.
10. **Volatile facts in stable docs rot quickly** — stable contracts point to live state instead of embedding current counts.

## Memory write policy

Add something to `MEMORY.md` only when all are true:

1. it is expected to remain useful across many sessions;
2. it is not sensitive/private applicant data;
3. it is not merely a current count/status/deadline;
4. it represents a durable invariant, architecture law, recurring failure pattern or verified long-lived decision;
5. it does not duplicate a more authoritative source verbatim.

Every memory change should cite its causal event/decision in the PR or Event Bus. Delete or revise memory when an architecture law intentionally changes.

## Mandatory bootstrap pointer

The machine-readable cold-start contract is `agent_context/bootstrap_manifest.json`.
Every compliant writer must follow it and emit `BOOTSTRAP_CONTEXT_LOADED` before acquiring a write lease.
