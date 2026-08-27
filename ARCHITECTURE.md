# UE-Xchanges-OS Architecture

Use COS-style event/provenance thinking without importing a general graph engine into a domain system that does not need it.

## Layers

1. Evidence — raw pages, PDFs/infopacks, forms, provider metadata.
2. Canonical domain — Opportunity, Organisation, Requirement, Application, Evidence.
3. Decision — eligibility, scoring, policy gates, dossier readiness.
4. Graph projections — relationships/history for retrieval, analytics and compounding.

```text
sources -> fetch -> raw evidence -> extract -> canonical record + provenance
canonical -> dedupe -> verify -> hard gates -> score -> priority queue
priority -> private evidence retrieval -> dossier -> policy gate -> human review -> submit -> outcome events
```

## Persistence strategy

v0: JSON/JSONL + Drive documents for bootstrapping/tests.

v1: Postgres/Supabase canonical structured store with nodes/edges/events tables. Neo4j/Qdrant are deferred until real queries prove a need. This keeps projections rebuildable without premature multi-database complexity.

## Provenance

Facts may carry source URL/file ID, fetched timestamp, content hash, page/line/section locator, extraction mode, confidence and last-verified timestamp.

## Dedupe

Preferred identity: provider project/call ID; canonical application URL; then fingerprint `(host organisation, normalised title, start date, country)`. Never dedupe solely by title.

## LLM boundary

Deterministic code owns dates, age/country hard gates, duplicate keys, score aggregation, state transitions and enforcement after policy classification.

LLMs may assist fuzzy requirement extraction, topic/competency classification, criterion-to-evidence mapping and summarisation. Unknown facts remain unknown.
