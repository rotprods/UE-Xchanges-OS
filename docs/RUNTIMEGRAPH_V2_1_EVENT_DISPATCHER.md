# RuntimeGraph V2.1 — Autonomous Event Dispatcher

## Authority

This dispatcher is an execution/control-plane component. It is **not** a new source of truth.

Authority remains:

1. current official source / original infopack / authorised form / organiser confirmation / receipt;
2. private Drive CRM + Event Bus + private evidence;
3. GitHub contracts/code/tests;
4. RuntimeGraph and Command Center projections;
5. Todoist projection.

## Purpose

Convert already-normalized source observations into bounded RuntimeGraph events without recompiling the complete application corpus.

```text
source observation
→ normalization outside dispatcher
→ NormalizedIngress
→ explicit route
→ authority validation
→ RuntimeDomainEvent
→ application-scoped reducer
→ frontier diff
→ projection
```

The dispatcher never interprets raw Gmail/web/form prose as eligibility or receipt evidence.

## Delivery semantics

The contract is **at-least-once + deterministic idempotency**.

It does not claim exactly-once delivery.

- duplicate normalized ingress → no domain mutation;
- duplicate domain event → reducer no-op;
- late unique event → still processed;
- cursor high-watermark → never moves backwards;
- retryable `RuntimeError` → cursor does not advance;
- maximum identical retry strategy → 3 attempts;
- after retry exhaustion → dead letter + durable cursor advance;
- invalid/unroutable input → dead letter rather than poisoning the stream.

## Routing

Routing is explicit only:

- `application_id`, or
- exact `opportunity_id → application_id` mapping.

No title similarity, embeddings, fuzzy names or LLM inference may authorise a mutation.

## Receipt security

`receipt_confirmed` additionally requires:

```text
strong receipt authority
+ receipt_ref
+ submission_identity_bound = true
```

Accepted authority classes are deliberately narrow:

- provider confirmation;
- email receipt;
- captured confirmation;
- explicit organiser submission confirmation.

A normal organiser email, a sent email, a click, a Todoist completion or a screenshot without bound submission identity does not prove submission.

## Source cursors

Each source has an opaque high-watermark.

A late event below the watermark may still be processed if it is unique. The cursor therefore represents ingestion progress, not authority and not exclusion of late data.

Cursor advances only after:

- applied;
- duplicate already durable;
- permanent dead letter;
- exhausted retry dead letter;
- unrouted dead letter.

It does not advance while an event is still retryable.

## Dead letters

Dead-letter records contain only safe dispatch metadata:

- ingress idempotency key;
- source reference;
- application hint;
- reason;
- attempt count;
- observed timestamp.

They must not persist raw message bodies, credentials, OTPs, cookies, form answers or sensitive applicant values.

## Human/Agent boundary

Dispatcher automation may:

- poll/read permitted sources;
- normalize explicitly verified facts;
- dedupe;
- route;
- apply reversible evidence/gate events;
- recompute frontiers;
- project READY human actions.

It may not autonomously:

- authenticate as the applicant;
- enter passwords/OTP;
- accept personal declarations;
- author prohibited/personal final text;
- record applicant video;
- make payment;
- irreversibly submit an application;
- infer a receipt from weak evidence.

## Projection rule

A frontier change is output data, not proof that the projected action happened.

Todoist/Command Center may display newly READY human actions, but completing a projection task never mutates the authoritative application state without separate evidence.

## Recovery

A zero-context agent restores dispatcher execution from:

1. current `main`;
2. latest Event Bus watermark;
3. current Work Leases;
4. RuntimeGraph snapshot/read model;
5. source cursor snapshot;
6. dead-letter ledger;
7. current Command Center.

Then it acquires a fresh session/lease before any mutation.

## Failure-family gauntlet

Permanent regression tests cover:

- duplicate delivery;
- one-event/one-application isolation;
- unroutable input;
- late/out-of-order delivery;
- weak-email receipt poisoning;
- strong identity-bound receipt;
- retry without cursor advance;
- retry exhaustion → dead letter.

## Infrastructure trigger

No Kafka/Redis/Postgres/worker service is justified yet. Current deterministic in-process contracts plus Drive/Event Bus projections remain canonical until measured throughput/concurrency requires another primitive.
