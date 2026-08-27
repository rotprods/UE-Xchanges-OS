# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read `goal.md`, `goal-state.json`, this file, then `ARCHITECTURE.md` before modifying the system.

## Mission lock

Build an evidence-first system that finds legitimate EU youth mobility and trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes over time.

Do not optimize raw application volume. Optimize **accepted high-value opportunities per human hour**.

## Truth hierarchy

1. Original official page / original infopack / application form.
2. Provider metadata and timestamps.
3. Normalised canonical record.
4. Deterministic rules/calculations.
5. LLM extraction/classification with provenance.
6. Heuristic ranking.

Lower layers never overwrite contradictory higher-layer facts without a new evidence event.

## Public/private boundary

GitHub: code, tests, schemas, public programme knowledge, anonymised fixtures and aggregate metrics.

Drive/private storage: personal evidence, IDs/contact data, private applications, private emails, restricted infopacks and OAuth/secrets.

## Opportunity lifecycle

`DISCOVERED -> FETCHED -> VERIFIED -> NORMALISED -> DEDUPED -> ELIGIBILITY_CHECKED -> SCORED -> DOSSIER_READY -> HUMAN_REVIEW -> SUBMITTED -> FOLLOW_UP -> ACCEPTED|REJECTED|WITHDRAWN|EXPIRED`

No transition skips `VERIFIED` or `ELIGIBILITY_CHECKED`.

## Hard gates

Block when a confirmed requirement fails: deadline, residence/nationality, age, dates/availability, mandatory role/profile requirement, previous-participation rule, required support/sending organisation, mandatory conditions, or application policy.

Gate output is `PASS`, `FAIL`, or `UNKNOWN`. Unknown requires verification and is never silently treated as pass.

## AI policy gate

`AI_ALLOWED` · `AI_ASSIST_ONLY` · `AI_FINAL_TEXT_PROHIBITED` · `AI_UNKNOWN`.

When final AI text is prohibited, agents may organise source facts but must not draft/rewrite the applicant's final answers.

## Personalisation contract

Every proposed claim maps to verified evidence: evidence_id, fact, source, recency, competencies/topics, confidence, externally-usable flag. Gaps remain gaps; never improvise them away.

## Legitimate selection advantage

Prioritise exact thematic relevance, concrete contribution, learning goals, full-date reliability, language fit, dissemination/multiplier value, NFE/facilitation evidence, references/relationships and complete prompt applications. Penalise generic text, contradictions and unsupported claims.

## Trainer progression graph

`Participant/Youth Worker -> Contributing Participant -> Session Contributor -> Assistant Facilitator -> Full-time International Trainer Ref #1 -> #2 -> #3 -> TOY Eligible -> TOY Active -> Paid Trainer Calls -> Repeat Organiser Network`

TOY references must satisfy SALTO criteria; participant/group-leader experience or isolated sessions do not automatically qualify.

## Graph contract

Append-only events are history; projections are disposable/rebuildable.

Node types: Person, Opportunity, Programme, Organisation, Call, Infopack, Application, Evidence, Requirement, Competency, Topic, Country, Activity, TrainerReference, Outcome, Source.

Edges: PUBLISHED_BY, HOSTED_BY, SUPPORTED_BY, ELIGIBLE_FOR, REQUIRES, MATCHES, SUPPORTED_BY_EVIDENCE, APPLIED_TO, RESULTED_IN, PARTNERED_WITH, TRAINED_AT, FACILITATED, VALIDATED_BY, DERIVED_FROM.

## Agent roles

Scout; Verifier; Infopack Analyst; Eligibility Engine; Ranker; Evidence Retriever; Application Strategist; Policy Guard; Trainer Career Agent; Outcome Analyst.

One agent may hold multiple roles, but role boundaries remain explicit.

## Commit/checkpoint protocol

Before ending a coherent execution wave: update `goal-state.json`, update checkpoints, run relevant deterministic tests, record known gaps, and refresh git.local when persistent handoff materially changes.

## Checkpoints

### Wave 0 — Definition & architecture
- [x] /define-goal
- [x] goal-state contract
- [x] truth/provenance model
- [x] graph model
- [x] public/private boundary

### Wave 1 — Deterministic core
- [x] domain models
- [x] eligibility hard gates
- [x] opportunity scoring
- [x] AI-policy detector
- [x] graph event/projection primitives
- [x] infopack extraction primitives
- [x] regression tests

### Wave 2 — Discovery connectors
- [ ] European Youth Portal
- [ ] SALTO Training Calendar
- [ ] SALTO Call for Trainers
- [ ] Eurodesk / Eurodesk Spain
- [ ] organisation watch
- [ ] canonical deduplication

### Wave 3 — Persistence + Drive sync
- [ ] Postgres/Supabase adapter
- [ ] Drive evidence adapter
- [ ] infopack archive/sync
- [ ] opportunity CRM projection

### Wave 4 — Application intelligence
- [ ] private evidence ingestion
- [ ] criteria-to-evidence retrieval
- [ ] dossier generator
- [ ] form parser
- [ ] human-review queue

### Wave 5 — Trainer compounding
- [ ] TOY readiness dashboard
- [ ] trainer calls collector
- [ ] qualifying reference ledger
- [ ] fee/working-condition parser
- [ ] organiser relationship graph

### Wave 6 — Analytics + automation
- [ ] outcome feedback model
- [ ] source precision/recall analytics
- [ ] deadline watch
- [ ] recurring opportunity brief
