# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read: `goal.md` → `goal-state.json` → this file → `ARCHITECTURE.md` → relevant `knowledge/` and `docs/` files.

## Mission lock
Build an evidence-first operating system that finds legitimate EU youth-mobility and trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes.

**North Star: accepted high-value funded opportunities per human application hour. Never optimize raw submission volume.**

## Truth hierarchy
1. Original official page / original infopack / application form.
2. Provider metadata/timestamps.
3. Normalised canonical record.
4. Deterministic rules/calculations.
5. LLM extraction/classification with explicit provenance.
6. Heuristic ranking.

`UNKNOWN` is a first-class state. Never silently coerce it to `PASS`.

## Source-of-truth topology
- Official source / original infopack = authority for opportunity facts.
- GitHub = executable/versioned truth: schemas, rules, collectors, tests, public knowledge.
- Google Drive = private profile/evidence, infopacks, dossiers, CRM and trainer references.
- Library `/git.local/UE-Xchanges-OS` = portable cold-start snapshot.
- Graph projections = disposable/rebuildable from evidence + append-only events.

## Public/private boundary
The public repository may contain code, schemas, public source facts, anonymised fixtures and aggregate metrics. It must not contain identity/contact documents, private application text/emails, medical/accessibility data, restricted infopacks, secrets or private applicant evidence.

Private operational data belongs under `07_PERSONAL_TRAVEL/01_TRAVEL/UE_XCHANGES_OS/` in Drive.

## Opportunity lifecycle
`DISCOVERED → FETCHED → VERIFIED → NORMALISED → DEDUPED → ELIGIBILITY_CHECKED → SCORED → DOSSIER_READY → HUMAN_REVIEW → SUBMITTED → FOLLOW_UP → ACCEPTED|REJECTED|WAITLISTED|WITHDRAWN|EXPIRED`

No application skips `VERIFIED` or `ELIGIBILITY_CHECKED`.

## Hard gates
Block on a confirmed mandatory failure: deadline, residence/nationality, age, dates/availability, role/profile, previous-participation rule, support/sending organisation, mandatory language/conditions, duplicate submission or application policy.

Gate output: `PASS`, `FAIL`, `UNKNOWN`. Any confirmed `FAIL` forces opportunity score = `0/BLOCKED`. `UNKNOWN` creates verification debt.

## AI-policy gate
Classify every call as `AI_ALLOWED`, `AI_ASSIST_ONLY`, `AI_FINAL_TEXT_PROHIBITED`, or `AI_UNKNOWN`.

When final AI text is prohibited, agents may research and organise evidence but must not draft/rewrite final applicant answers. `AI_UNKNOWN` blocks final-text automation until verified.

## Personalisation contract
No adjective without proof. Every proposal must map claims to private evidence objects with `evidence_id`, fact, source, recency, competencies/topics, confidence and external-use status.

Selection advantage is:
`criterion → verified proof → concrete contribution → credible learning goal → multiplier/dissemination`.

Never fabricate credentials, youth-work history, fewer-opportunities status, language level, availability or circumstances.

## Role lanes
`PARTICIPANT` · `YOUTH_WORKER` · `FACILITATOR` · `TRAINER` · `EXPERT`.

Positioning is role-aware. Participant applications must not read as attempts to hijack a project as trainer; trainer calls require methods, educational responsibility, outcomes and references.

## Trainer progression
Target path:
`Participant/Youth Worker → Contributing Participant → Session Contributor → Assistant Facilitator → Qualifying Full-time International Trainer Ref #1 → #2 → #3 → TOY-ready → TOY-active → Paid Trainer Calls → Repeat Organiser Network`.

A candidate TOY reference must independently pass: international/intercultural; youth-work field; >=3 training days; NFE; full-time trainer; responsibility for educational goals; validatable reference. Participant/group-leader status or an isolated workshop does not automatically count.

Current private evidence state: **0 verified TOY-qualifying references. BUILD, do not CLAIM.**

## Graph contract
History is append-only. Projections are rebuildable.

Core nodes: `Person`, `Opportunity`, `Programme`, `Organisation`, `Call`, `Infopack`, `Application`, `Evidence`, `Requirement`, `Competency`, `Topic`, `Country`, `Activity`, `TrainerReference`, `Outcome`, `Source`.

Core edges: `PUBLISHED_BY`, `HOSTED_BY`, `SUPPORTED_BY`, `ELIGIBLE_FOR`, `REQUIRES`, `MATCHES`, `SUPPORTED_BY_EVIDENCE`, `APPLIED_TO`, `RESULTED_IN`, `PARTNERED_WITH`, `TRAINED_AT`, `FACILITATED`, `VALIDATED_BY`, `DERIVED_FROM`.

Do not introduce Neo4j/Qdrant or another specialised graph/vector store until real queries/scale justify it. SQLite is sufficient for single-operator collector state; Postgres/Supabase is the v1 shared persistence target.

## Provider access modes
Never treat a zero-result generic scraper as success.
- SALTO Training Calendar: `STATIC_PAGINATED_HTML`.
- SALTO Calls for Trainers: `AUTH_INDEX_PUBLIC_DETAILS`; never bypass MySALTO login. Public detail URLs may be ingested when legitimately discovered.
- European Youth Portal ESC: `DYNAMIC_INDEX`; use supported browser/API/search-backed discovery.
- Eurodesk Finder: `DYNAMIC_INDEX`; use supported browser/query/search-backed discovery.

Externally discovered public URLs enter through deterministic canonicalisation, fingerprinting, provenance and seen-state.

## Agent roles
**Scout** discovers; **Verifier** resolves source facts; **Infopack Analyst** extracts criteria/logistics/policy; **Eligibility Engine** owns hard gates; **Ranker** scores after gates; **Evidence Retriever** reads private proof; **Application Strategist** maps criteria→proof→value; **Policy Guard** blocks unsafe/duplicate modes; **Trainer Career Agent** tracks references/calls; **Outcome Analyst** updates priors.

One agent may perform several roles but must preserve boundaries in outputs.

## Dossier definition of done
A dossier is not `READY` unless source/infopack, eligibility-critical facts and AI policy are resolved; mandatory questions/documents are captured; every proposed claim maps to evidence; gaps are explicit; canonical submission mode is known; duplicate check passes; and human review is explicit.

## Commit/checkpoint protocol
Before ending a coherent execution wave: update `goal-state.json`; update this checkpoint; run deterministic tests; record gaps; refresh `git.local` when handoff changes materially.

## Checkpoints — 2026-08-27

### Wave 0 — Definition & architecture ✅
- [x] `/define-goal`, North Star, SLOs.
- [x] provenance/truth model, graph contract, privacy boundary.

### Wave 1 — Deterministic core ✅
- [x] canonical domain models/schemas.
- [x] deadline/residence/age/availability/language hard gates.
- [x] eligibility-aware scoring and separate competitiveness contract.
- [x] AI-policy detector/readiness guard.
- [x] graph event/projection primitives.
- [x] infopack HTML/PDF text primitives and criterion→evidence mapping.

### Wave 2a — Discovery primitives ✅
- [x] source registry, bounded HTTP fetch/hash.
- [x] URL canonicalisation, stable fingerprint hierarchy, URL dedupe.
- [x] deterministic TOY-reference qualification.
- [x] first live CRM seed: 7 current/watch opportunities.

### Wave 2b — Incremental provider state ✅
- [x] SQLite ETag/Last-Modified/content-hash/fetch state.
- [x] idempotent candidate seen-set.
- [x] SALTO Training Calendar offset pagination scanner.
- [x] explicit dynamic/auth provider modes and safe blocked reasons.
- [x] external candidate ingest for browser/search-backed discovery.
- [x] source access matrix and live-seed manifest.
- [x] **27 deterministic tests passed / 0 failed locally.**

### Drive / private intelligence ✅ foundation
- [x] canonical workspace/folder taxonomy.
- [x] native Opportunity & Application CRM in Europe/Madrid.
- [x] Master Applicant Profile upgraded from template to verified evidence + explicit hard-gate debt.
- [x] Applicant Evidence Bank seeded with EV-001..EV-007 and allowed-claim limits.
- [x] Infopack/Application/Trainer Reference templates.
- [x] first personalised dossier: SALTO 15092 ON/OFF, status `NEEDS_VERIFICATION`.
- [x] programme/source/trainer/selection knowledge docs.
- [x] Library `/git.local/UE-Xchanges-OS` snapshot foundation.

### Next — highest-value bottlenecks
- [ ] SALTO detail-page → canonical Opportunity normalizer.
- [ ] automatic CRM upsert from deterministic ingestion.
- [ ] supported browser/search adapters for dynamic EYP/Eurodesk indexes.
- [ ] organisation-watch collector and relationship graph.
- [ ] resolve private hard-gate debt: legal residence, age/DOB, availability, actual youth-work/NFE history, delivered training/references.
- [ ] form parser + application AI-policy verification.
- [ ] trainer-call collector + TOY readiness dashboard.
- [ ] outcome feedback/acceptance analytics + deadline watcher.

## Current resumable state
The system is operational as a foundation plus live validation: 7 current/watch opportunities are in the CRM; a private evidence graph has 7 seeded evidence items; the first personalised application dossier exists; and discovery/provider state is tested. Eligibility remains deliberately `UNKNOWN` wherever private mandatory facts or role evidence are unresolved. The next engineering bottleneck is repeatable canonical detail ingestion and verification of real applicant hard-gate evidence—not more schema or graph infrastructure.
