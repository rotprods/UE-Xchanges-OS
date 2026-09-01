# RuntimeGraph V2.2 — Source Adapters + Self-Healing Projections

Status: implementation contract.

## Objective

Close the remaining gap between external evidence channels and RuntimeGraph without granting those channels authority they do not possess.

```text
Gmail / Official Source / Form Gateway / Receipt Reconciler
                         ↓
                value-safe adapter
                         ↓
                 NormalizedIngress
                         ↓
              RG2.1 Dispatcher
                         ↓
              incremental reducer
                         ↓
             expected projections
                         ↓
           health / drift comparison
                         ↓
             deterministic repair
```

## Authority boundary

Adapters are translators, not judges.

They may translate **explicit already-extracted facts** into normalized events. They may not inspect raw prose and infer eligibility, current youth-work status, deadline extension, receipt state or submission state by themselves.

Authority remains:

1. current official source / original infopack / authorised form / organiser confirmation / receipt;
2. private Drive CRM + Evidence/Event graph;
3. GitHub executable contracts;
4. RuntimeGraph / Command Center / Todoist projections.

## Source adapters

### Gmail

`GmailSourceAdapter` accepts only concise structured facts such as:

```text
message_id
application_id
Gate = Spain Route
Result = PASS
Reason = ORGANISER_CONFIRMED_SPAIN_ROUTE
```

It has deliberately **no receipt method**. A normal organiser email cannot become a receipt by string matching.

### Official source

`OfficialSourceAdapter` may normalize:

- exact deadline changes;
- exact open/closed/eligibility gates;
- explicit official evidence facts.

Dates must be timezone-aware. Historical values are superseded through new events rather than silently overwritten.

### Form Gateway

`FormGatewayAdapter` reuses the existing value-free `FormExecutionPlan` bridge. It emits form fingerprint/state and AI-policy gate events without field answers, cookies, passwords or secret values.

### Receipt Reconciler

`ReceiptSourceAdapter` accepts only canonical `SubmissionReceipt` objects that already satisfy the strong receipt contract. It emits `RECEIPT_CONFIRMED` only when submission identity is bound.

## Self-healing projection law

Self-heal is permitted only for explicitly derived surfaces:

```text
Command_Center
Human_Now
Agent_Next
Claim_Registry
Dispatcher_State
Source_Cursors
Dead_Letters
```

Self-heal is forbidden for canonical/private authority surfaces including:

```text
Opportunities
Applications
Mass_Apply_Queue
Execution_Log
Agent_Event_Bus
Agent_Sessions
Work_Leases
Autofill_Profile
Human_Gates
```

A repair never guesses canonical truth. It rebuilds a read model from already-authoritative RuntimeGraph inputs.

## Projection health

Each derived surface is compared using:

```text
source_revision
+ event watermark
+ deterministic row fingerprint
```

States:

```text
HEALTHY
MISSING
DRIFTED
STALE
```

Repairs:

```text
CREATE_DERIVED_SURFACE
REPLACE_DERIVED_ROWS
```

Running the same repair against an already healthy projection must be a no-op.

## Todoist self-heal

Todoist remains an execution projection only.

The stable identity is `runtime_action_id`, not task title.

Diff operations are:

```text
CREATE — a READY human action has no projected task
UPDATE — the projected task differs from the current human action
RETIRE — the task still exists but the runtime action is no longer READY
```

Todoist completion never proves submission or receipt.

## PII / secret policy

Derived projections may expose only the minimum execution metadata required for the operator.

`Claim_Registry` deliberately omits claim values. It may expose claim key, status, temporal/role scope and evidence IDs, but not private values.

No adapter/projection may persist:

- passwords, OTPs, cookies or browser storage;
- PRN or identity-document numbers;
- bank details;
- medical/sensitive applicant values;
- raw application answers;
- raw organiser-email bodies.

## Recovery

A zero-context agent can recover RG2.2 by reading:

1. current GitHub main;
2. active `Agent_Sessions` and `Work_Leases`;
3. `Agent_Event_Bus` after the context cursor;
4. private CRM state;
5. RuntimeGraph dispatcher cursors/dead letters;
6. current Command Center projection.

Then:

```text
rebuild runtime
→ produce expected ProjectionDocuments
→ observe current derived surfaces
→ build repair plan
→ apply only derived repairs
→ verify fingerprints/watermarks
```

## Definition of Done

RG2.2 passes when:

- Gmail adapter cannot accept raw multiline prose as gate reason;
- Gmail adapter cannot emit a receipt;
- official deadlines require timezone-aware values;
- Form Gateway remains value-free;
- Receipt adapter requires canonical strong receipt evidence;
- projection rebuild is deterministic;
- claim values never appear in projection rows;
- row drift and stale watermarks are detected;
- canonical surfaces are impossible self-heal targets;
- Todoist CREATE/UPDATE/RETIRE is driven by `runtime_action_id`;
- exact-head CI passes;
- one real Command Center drift/reconciliation cycle is executed without touching canonical application truth.
