# UE-Xchanges-OS Architecture

UE-Xchanges-OS is an evidence-first domain system with a small deterministic graph/event core. It uses COS-style provenance and event sourcing without importing a general graph platform prematurely.

## Layers

1. **Evidence** — official pages, PDFs/infopacks, forms, organiser replies, contracts and receipts.
2. **Canonical domain** — Opportunity, Organisation, Requirement, Application, Profile Evidence and Economics.
3. **Control plane** — Context, Agent Session, Event, Work Lease and Agent Inbox.
4. **Decision** — hard eligibility, AI/application policy, economics verification, ranking and dossier readiness.
5. **Projections** — Drive CRM, Todoist, dashboards, graph relationships and analytics.

```text
sources -> raw evidence -> extraction -> canonical record + provenance
canonical -> dedupe -> verify -> hard gates -> economics/fit -> execution queue
queue -> lease -> evidence retrieval -> dossier/form -> human ownership -> submit -> receipt
all material writes -> append-only event -> projections -> handoff
```

## Truth topology

1. Current original official source / infopack / authorised form / organiser confirmation / contract / receipt.
2. Private Drive CRM event bus and evidence graph.
3. GitHub versioned code, schemas, policies and aggregate state.
4. Portable snapshots.
5. Todoist and user-interface projections.

The latest edit is not automatically authoritative.

## Current persistence

Private Google Drive Sheets/Docs provide the operational store for identity, evidence, forms, sessions, events, leases and dossiers. GitHub is the public executable contract.

The Sheet-based event bus is **read-before-write and polling-oriented**, not a push broker or transactional database. It is sufficient for coordinated human-scale parallel sessions when every writer refreshes the cursor and lease state before mutation.

A future Postgres deployment may map the same contracts to:

```text
contexts
agent_sessions
agent_events
work_leases
agent_inbox
opportunities
applications
profile_evidence
opportunity_economics
sources
outcomes
```

The event schemas and deterministic guards remain stable across that migration. Neo4j/vector stores remain projections until query demand justifies them.

## Concurrency

Every canonical writer:

```text
register session -> read cursor/events -> acquire narrow lease
-> perform one valid transition -> append idempotent event
-> update projections -> release -> handoff
```

An unexpired lease owned by another session blocks mutation. Expired takeover is explicit. Projection divergence blocks wave closure.

## Idempotency

```text
SHA-256(project_id | entity_type | entity_id | operation | authoritative_source_version)
```

Replaying the same transition for the same source version becomes a no-op.

## Economics

Cash and funded value are separate models. Net/hour is calculated only when gross cash, actual hours and compulsory costs are verified. Unknown inputs remain unknown.

## Provenance

Facts may carry source URL/file ID, fetched timestamp, content hash, page/line/section locator, extraction mode, confidence, source version and last-verified timestamp.

## Dedupe

Provider/call ID, then provider post ID, canonical application URL, then `(host, normalised title, start date, country)`. Never dedupe solely by title.

## LLM boundary

Deterministic code owns deadlines/time-zone validation, age/country gates, duplicate keys, idempotency, lease enforcement, state transitions, cash calculations and policy enforcement after classification.

LLMs may assist fuzzy extraction, topic classification, criterion-to-evidence mapping, summaries and draft structure. Unknown facts remain unknown; final applicant ownership follows each call's policy.
