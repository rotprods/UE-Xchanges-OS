# Multi-Agent Control Plane

Version: 1.0.0 — 2026-08-29

## Purpose

UE-Xchanges-OS is operated by multiple chats and agents that do not share a guaranteed live memory. Coordination therefore depends on an external, evidence-backed control plane rather than conversational assumptions.

The private Google Drive CRM is the live operational store. GitHub is the versioned executable contract. Todoist is a projection. Gmail and provider portals are evidence channels.

## Consistency model

Current mode is **read-before-write, event-sourced coordination with exclusive leases**.

It provides near-real-time alignment when every agent follows the protocol. It is not a push-subscription system: an already-running chat does not receive another chat's update automatically. Before every material write, the agent must refresh the shared cursor, events and active leases.

A future transactional database may replace the Sheet projection without changing the event, lease or identity contracts.

## Canonical private tables

| Table | Purpose |
|---|---|
| `Context_Registry` | Canonical project context, objective, active wave, priority vector and event cursor. |
| `Agent_Sessions` | One row per actual agent/chat session, including heartbeat and handoff. |
| `Agent_Event_Bus` | Append-only causal event ledger. |
| `Work_Leases` | Exclusive writer claims over the smallest safe resource scope. |
| `Agent_Inbox` | Directed/broadcast cross-agent handoffs and acknowledgements. |
| `Opportunity_Economics` | Verified cash, hours, costs and non-cash funded value. |
| `Source_Coverage` | Source registry, cadence, cursor, frontier and owner. |
| `Profile_Interview` | Ask-once queue of unresolved personal facts and evidence. |

## Cold start

Every agent must complete this sequence before a canonical mutation:

1. Read `goal.md`, `goal-state.json`, `AGENTS.md`, this protocol and the current checkpoint on `main`.
2. Read `Context_Registry` and the target context.
3. Read active `Agent_Sessions` and `Work_Leases`.
4. Read `Agent_Event_Bus` after the context's `last_event_id`.
5. Reconcile the target CRM/GitHub/Todoist projection.
6. Register a unique session.
7. Emit `SESSION_STARTED`.
8. Acquire the smallest safe lease.
9. Execute one valid graph transition.
10. Emit the domain event and update projections.
11. Release the lease and write a handoff before termination.

Unregistered sessions are read-only.

## Identities

Session IDs:

```text
SES-<PROJECT>-<PLATFORM>-<YYYYMMDDTHHMMSS>-<NN>
```

Agent IDs are stable roles, for example:

```text
AGT-CHATGPT-PRO-ERASMUS-ORCHESTRATOR
AGT-GLOBAL-PAID-SCOUT
AGT-HUMANITARIAN-SCOUT
AGT-PAID-MONITOR-SCOUT
AGT-EU-MOBILITY-SCOUT
AGT-INFO-PACK-ANALYST
AGT-FORM-CAPTURE
AGT-PROFILE-EVIDENCE
AGT-APPLICATION-STRATEGIST
AGT-POLICY-GUARD
AGT-ECONOMICS-ANALYST
AGT-SUBMISSION-OPERATOR
AGT-TRAINER-CAREER
AGT-OUTCOME-ANALYST
```

A role may own many sequential sessions. A session ID is never reused.

## Lease semantics

A lease is scoped to one resource, for example:

```text
opportunity:eyp-53940
dossier:app-eyp-53940-v1
source-cursor:salto-calls-for-trainers
profile:erasmus-history
policy:global-priority
```

Defaults:

- TTL: 120 minutes;
- heartbeat target: 15 minutes while writing;
- another session's unexpired lease blocks mutation;
- the same owner may renew;
- an expired/released lease may be taken over only with an event;
- completion requires release and handoff.

A broad wildcard lease is allowed only for a bounded migration/control-plane operation and must list explicit exclusions.

## Event semantics

Every material operation emits one append-only event with:

- event, project, context, session and agent IDs;
- timezone-aware timestamp;
- event type, entity type/ID and operation;
- state before/after;
- source and causal parent;
- correlation and lease IDs;
- payload;
- idempotency key;
- severity, acknowledgement and writer version.

The idempotency key is derived from:

```text
project_id | entity_type | entity_id | operation | authoritative_source_version
```

Replaying the same transition for the same source version is a no-op. A changed authoritative source version produces a new event.

## Core events

```text
SESSION_STARTED
SESSION_HEARTBEAT
LEASE_ACQUIRED
LEASE_RENEWED
LEASE_BLOCKED
LEASE_TAKEN_OVER
SOURCE_SCANNED
SOURCE_ITEM_DISCOVERED
OPPORTUNITY_UPSERTED
DUPLICATE_MERGED
SOURCE_VERIFIED
FACT_CONFLICT_DETECTED
FACT_SUPERSEDED
INFOPACK_CAPTURED
INFOPACK_ANALYSED
FORM_CAPTURED
AI_POLICY_RESOLVED
ELIGIBILITY_RECOMPUTED
ECONOMICS_VERIFIED
DOSSIER_CREATED
ANSWER_PACK_CREATED
HUMAN_INPUT_REQUIRED
HUMAN_INPUT_RESOLVED
HUMAN_FINAL_REVIEWED
SUBMISSION_ATTEMPTED
SUBMISSION_CONFIRMED
RECEIPT_STORED
ORGANISER_REPLY_INGESTED
OUTCOME_RECORDED
PROJECTION_DIVERGENCE_DETECTED
PROJECTION_RECONCILED
HANDOFF_READY
SESSION_COMPLETED
```

## Mutation guard

A mutating event is admissible only when:

1. its idempotency key is unseen;
2. the referenced lease exists and is active;
3. event author equals lease owner;
4. project and context match;
5. entity is inside lease scope.

Read-only audit events may omit a lease, but they cannot change a projection.

## Conflict handling

The latest edit is not automatically true.

When sources or sessions disagree:

1. preserve both claims;
2. emit `FACT_CONFLICT_DETECTED`;
3. set the affected gate to `UNKNOWN` / `VERIFICATION_DEBT`;
4. resolve through authority and freshness rules;
5. emit `FACT_SUPERSEDED` only when the dominance rule is satisfied.

A Drive row changed without a corresponding event, or an event not reflected in required projections, is `PROJECTION_DIVERGENCE`. Wave closure is blocked until reconciled.

## Handoff contract

A terminating session must record:

- input state/ref and latest observed event;
- lease(s) acquired and released;
- entities changed;
- source/evidence references;
- tests/CI actually observed;
- unresolved blockers;
- exactly one next mandatory transition per active node;
- output state/ref and last emitted event.

Historical sessions may be backfilled only from verifiable GitHub, Drive revision, Gmail or execution-log evidence. Unknown chat identity remains `AGENT_OR_SESSION_UNKNOWN`; do not invent it.

## Failure policy

- Stale heartbeat alone does not prove abandonment before lease expiry.
- Missing receipt never proves submission or non-submission.
- Failed CI blocks merge.
- A connector failure is recorded as a blocked capability, not silently treated as success.
- A form requiring authentication/CAPTCHA remains `READY_FOR_HUMAN_SUBMIT` until the human completes the legitimate final interaction.
