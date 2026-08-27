# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read in this order: `goal.md` → `goal-state.json` → this file → `ARCHITECTURE.md` → relevant source/knowledge docs.

## 0. Mission lock

Build an evidence-first operating system that finds legitimate EU youth-mobility and trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes over time.

**Do not optimize raw application volume. Optimize accepted high-value opportunities per human application hour.**

## 1. Truth hierarchy

1. Original official page / original infopack / application form.
2. Provider metadata and timestamps.
3. Normalised canonical record.
4. Deterministic rules/calculations.
5. LLM extraction/classification with explicit provenance.
6. Heuristic ranking.

Lower layers may not overwrite contradictory higher-layer facts without a new evidence event. `UNKNOWN` is a first-class state; never silently coerce it to `PASS`.

## 2. Public/private boundary

### GitHub may contain
- code, tests, schemas, scoring logic;
- public programme facts/source URLs;
- anonymised fixtures;
- aggregate metrics without private application text.

### GitHub must not contain
- passport/ID/contact details;
- private applicant narrative or accessibility/medical data;
- final application answers/private emails;
- restricted/unpublished infopacks;
- OAuth/API secrets.

Private operational data belongs in Google Drive under `07_PERSONAL_TRAVEL/01_TRAVEL/UE_XCHANGES_OS/`.

## 3. Source-of-truth topology

- **Official source / original infopack** = authority for opportunity facts.
- **GitHub** = executable/versioned truth for schemas, rules, source adapters and public knowledge.
- **Google Drive** = private profile/evidence, infopacks, dossiers, CRM and trainer references.
- **Library `/git.local/UE-Xchanges-OS`** = portable cold-start snapshot/handoff.
- **Derived graph projections** = disposable/rebuildable from evidence + events.

## 4. Opportunity lifecycle

`DISCOVERED → FETCHED → VERIFIED → NORMALISED → DEDUPED → ELIGIBILITY_CHECKED → SCORED → DOSSIER_READY → HUMAN_REVIEW → SUBMITTED → FOLLOW_UP → ACCEPTED|REJECTED|WAITLISTED|WITHDRAWN|EXPIRED`

No application may skip `VERIFIED` or `ELIGIBILITY_CHECKED`.

## 5. Hard gates

Block an opportunity when a confirmed mandatory rule fails:
- deadline elapsed;
- residence/nationality;
- age;
- dates/availability;
- mandatory role/profile;
- previous-participation rule;
- required sending/support organisation;
- mandatory language/conditions;
- application policy / duplicate submission.

Gate output: `PASS`, `FAIL`, `UNKNOWN`.

If any confirmed hard gate = `FAIL`, opportunity desirability score is forced to `0` / `BLOCKED`.

## 6. AI-policy gate

Classify every call:
- `AI_ALLOWED`
- `AI_ASSIST_ONLY`
- `AI_FINAL_TEXT_PROHIBITED`
- `AI_UNKNOWN`

When final AI text is prohibited, agents may research, organise requirements and surface evidence, but must not generate/rewrite the applicant's final answers. `AI_UNKNOWN` blocks final-text automation until verified.

## 7. Personalisation contract

Proposals are assembled from verified evidence objects, not persona improvisation. Evidence should carry:
- `evidence_id`
- fact/claim
- source/location
- date/recency
- competencies/topics
- confidence
- `externally_usable`

**No adjective without proof.** Prefer concrete evidence + result + project relevance over generic motivation language. Missing proof remains an explicit gap.

## 8. Legitimate acceptance advantage

Selection advantage is created by lowering organiser uncertainty and increasing project-specific value:

`selection criterion → verified proof → concrete contribution → credible learning goal → multiplier/dissemination outcome`

Prioritise:
- exact thematic relevance;
- contribution assets useful to the activity;
- reliability/full-date availability;
- language fit;
- dissemination/documentation capability;
- NFE/facilitation evidence;
- organisation relationships/references;
- concrete post-project transfer;
- complete, prompt application.

Never fabricate credentials, youth-work history, fewer-opportunities status, language levels or circumstances.

## 9. Role lanes

`PARTICIPANT` · `YOUTH_WORKER` · `FACILITATOR` · `TRAINER` · `EXPERT`

Role-aware positioning matters. A participant application must not read as an attempt to hijack the project as trainer; trainer calls require methods, educational responsibility, outcomes and references.

## 10. Trainer progression graph

Target path:

`Participant/Youth Worker → Contributing Participant → Session Contributor → Assistant Facilitator → Qualifying Full-time International Trainer Ref #1 → #2 → #3 → TOY-ready → TOY-active → Paid Trainer Calls → Repeat Organiser Network`

A potential TOY reference must be independently checked for:
- international/intercultural activity;
- youth-work field;
- >= 3 training days;
- non-formal learning;
- full-time trainer role;
- responsibility for overall educational goals;
- validatable reference.

Participant/group-leader status or a short isolated workshop does not automatically qualify.

## 11. Graph contract

History is append-only. Projections are rebuildable.

### Core nodes
`Person`, `Opportunity`, `Programme`, `Organisation`, `Call`, `Infopack`, `Application`, `Evidence`, `Requirement`, `Competency`, `Topic`, `Country`, `Activity`, `TrainerReference`, `Outcome`, `Source`.

### Core edges
`PUBLISHED_BY`, `HOSTED_BY`, `SUPPORTED_BY`, `ELIGIBLE_FOR`, `REQUIRES`, `MATCHES`, `SUPPORTED_BY_EVIDENCE`, `APPLIED_TO`, `RESULTED_IN`, `PARTNERED_WITH`, `TRAINED_AT`, `FACILITATED`, `VALIDATED_BY`, `DERIVED_FROM`.

Factual edges should carry provenance. Do not introduce a specialised graph database until real query/scale evidence requires it; Postgres/Supabase projections are the v1 target.

## 12. Scoring contract

Never mix eligibility with desirability.

1. Run hard gates.
2. `FAIL` → score 0.
3. `UNKNOWN` → verification debt / cap priority.
4. Score opportunity value/fit.
5. Score application competitiveness separately.
6. Store components + scoring version, not just the total.

Weights live in `configs/scoring.json`.

## 13. Agent roles

- **Scout** — discovers candidates; never declares eligibility.
- **Verifier** — resolves source facts/freshness.
- **Infopack Analyst** — requirements, finance, selection, logistics, AI policy.
- **Eligibility Engine** — deterministic hard gates.
- **Ranker** — expected-value ranking after gates.
- **Evidence Retriever** — private evidence retrieval from Drive.
- **Application Strategist** — criteria → proof → contribution → learning/multiplier.
- **Policy Guard** — AI/submission/duplicate controls.
- **Trainer Career Agent** — qualifying references, paid calls, organiser graph.
- **Outcome Analyst** — acceptance/rejection feedback and empirical priors.

One agent may perform several roles, but outputs must preserve these boundaries.

## 14. Application dossier definition of done

A dossier is not `READY` unless:
- source/infopack verified;
- deadline/date/country/age and other mandatory rules resolved;
- AI policy resolved;
- mandatory questions/documents captured;
- each proposed claim maps to verified evidence;
- gaps are explicit;
- canonical submission URL/mode known;
- duplicate check passed;
- human review explicit.

## 15. Commit/checkpoint protocol

Before ending a coherent execution wave:
1. update `goal-state.json`;
2. update this checkpoint section;
3. run relevant deterministic tests;
4. record known gaps;
5. refresh `git.local` when handoff materially changes.

Prefer one coherent commit per completed wave/subwave.

## 16. Checkpoints

### Wave 0 — Definition & architecture ✅
- [x] `/define-goal`
- [x] North Star/SLOs
- [x] truth/provenance model
- [x] graph contract
- [x] public/private boundary

### Wave 1 — Deterministic core ✅
- [x] domain models/schemas
- [x] deadline/residence/age/availability/language gates
- [x] opportunity scoring
- [x] AI-policy detector
- [x] graph event/projection primitives
- [x] infopack HTML/PDF extraction primitives
- [x] criterion-to-evidence mapping
- [x] regression tests

### Wave 2a — Discovery core ✅
- [x] source registry loader
- [x] bounded HTTP fetch + content hash
- [x] URL canonicalisation
- [x] source-pattern discovery primitives
- [x] stable fingerprint hierarchy
- [x] URL-level dedupe
- [x] application readiness/duplicate/evidence-gap gates
- [x] deterministic TOY-reference qualification
- [x] regression suite: **19 passed / 0 failed**
- [x] first live CRM seed: **7 current/watch opportunities**, 2026-08-27

### Drive / handoff ✅ foundation
- [x] canonical Drive workspace/folder taxonomy
- [x] native Opportunity & Application CRM
- [x] private Master Applicant Profile template
- [x] private Evidence Bank
- [x] Infopack Analysis template
- [x] Application Dossier template
- [x] Trainer Reference Ledger
- [x] programme/source/trainer/selection knowledge docs
- [x] Library `/git.local/UE-Xchanges-OS` snapshot

### Wave 2b — Next
- [ ] provider-specific EYP collector/pagination
- [ ] SALTO Training Calendar collector/pagination
- [ ] SALTO Calls for Trainers collector
- [ ] Eurodesk/Eurodesk Spain collector
- [ ] organisation-watch collector
- [ ] persistent ETag/Last-Modified/content-hash state
- [ ] automatic CRM upsert replacing manual seed

### Wave 3 — Persistence
- [ ] Postgres/Supabase canonical adapter
- [ ] Drive evidence adapter
- [ ] infopack archive/sync
- [ ] graph event persistence/projections

### Wave 4 — Application intelligence
- [ ] verify private applicant hard gates/evidence
- [ ] criteria-to-evidence semantic retrieval
- [ ] dossier generator
- [ ] application form parser
- [ ] human-review queue

### Wave 5 — Trainer compounding
- [ ] trainer calls collector
- [ ] TOY-readiness dashboard
- [ ] fee/working-condition parser
- [ ] organiser relationship graph
- [ ] qualifying reference progression metrics

### Wave 6 — Analytics/automation
- [ ] outcome feedback model
- [ ] source precision/recall analytics
- [ ] deadline/expiry watcher
- [ ] recurring opportunity brief

## 17. Current resumable state — 2026-08-27

The repo/Drive/Library foundation is operational. The live CRM contains six verified SALTO youth-worker opportunities plus one future trainer/facilitator watch. Eligibility is intentionally `UNKNOWN` where the private evidence layer has not yet verified a mandatory applicant profile condition. The next engineering bottleneck is not more schema: it is repeatable provider ingestion + private applicant evidence verification.
