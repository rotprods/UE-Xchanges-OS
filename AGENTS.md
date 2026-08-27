# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read `goal.md`, `goal-state.json`, this file, then `ARCHITECTURE.md` before modifying the system.

## 0. Mission lock

Build an evidence-first system that finds legitimate EU youth mobility and trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes over time.

Do not optimize raw application volume. Optimize **accepted high-value opportunities per human hour**.

## 1. Truth hierarchy

1. Original official page / original infopack / application form.
2. Provider metadata and timestamps.
3. Normalised canonical record.
4. Deterministic rules and calculations.
5. LLM extraction/classification with explicit provenance.
6. Heuristic ranking.

Lower layers may never overwrite contradictory higher-layer facts without recording a new evidence event.

## 2. Public/private boundary

### GitHub may contain
- code, tests, schemas, scoring logic;
- public programme facts and source URLs;
- anonymised fixtures;
- aggregate metrics without personal application text.

### GitHub must NOT contain
- passport/ID/contact details;
- private applicant narrative or medical/accessibility information;
- application answers, private emails, unpublished infopacks under access restrictions;
- OAuth/API secrets.

Private operational data belongs in Drive paths documented in `docs/DRIVE_MAP.md`.

## 3. Opportunity lifecycle

`DISCOVERED -> FETCHED -> VERIFIED -> NORMALISED -> DEDUPED -> ELIGIBILITY_CHECKED -> SCORED -> DOSSIER_READY -> HUMAN_REVIEW -> SUBMITTED -> FOLLOW_UP -> ACCEPTED|REJECTED|WITHDRAWN|EXPIRED`

No transition may skip `VERIFIED` or `ELIGIBILITY_CHECKED`.

## 4. Hard gates

An opportunity is blocked if any confirmed hard requirement fails:
- deadline elapsed;
- residence/nationality condition fails;
- age condition fails;
- dates are impossible;
- role/profile requirement is objectively unmet;
- previous-participation rule fails;
- required sending/support organisation cannot be satisfied;
- applicant refuses mandatory conditions;
- application policy blocks the proposed automation mode.

Hard-gate output is explainable: `PASS`, `FAIL`, or `UNKNOWN`. `UNKNOWN` requires human/source verification; it is never silently treated as `PASS`.

## 5. AI policy gate

Classify every call:
- `AI_ALLOWED`
- `AI_ASSIST_ONLY`
- `AI_FINAL_TEXT_PROHIBITED`
- `AI_UNKNOWN`

When final AI text is prohibited, agents may organise facts and show source evidence but must not draft/rewrite final applicant answers.

## 6. Personalisation contract

Application proposals must be built from verified evidence objects, not persona improvisation. Every evidence item should include:
- `evidence_id`
- claim/fact
- source/location
- date/recency
- relevant competencies/topics
- confidence
- externally usable? yes/no

Use specificity over adjectives. Prefer a concrete example + result + relevance over generic motivation language.

## 7. Acceptance-advantage policy

Legitimate competitiveness comes from better fit and lower organiser risk, never deception. Prioritise:
- exact thematic relevance;
- proof of contribution;
- credible learning goals;
- reliability and full-date availability;
- language fit;
- useful dissemination/content skills;
- non-formal education/facilitation evidence;
- prior collaboration/references;
- prompt, complete application;
- a concrete post-project multiplier plan.

Penalise generic claims, copied templates, contradictions and unsupported self-promotion.

## 8. Trainer progression graph

Target path:

`Participant/Youth Worker -> Contributing Participant -> Workshop/Session Contributor -> Assistant Facilitator -> Full-time International Trainer Reference #1 -> #2 -> #3 -> TOY Eligible -> TOY Active -> Paid Trainer Calls -> Repeat Organiser Network`

Important: TOY references must satisfy SALTO criteria. Youth-exchange group leadership, being a participant, or isolated sessions do not automatically count as full-time trainer references.

## 9. Graph contract

Use append-only events as history. Graph projections are disposable/rebuildable.

Core node types:
- `Person`
- `Opportunity`
- `Programme`
- `Organisation`
- `Call`
- `Infopack`
- `Application`
- `Evidence`
- `Requirement`
- `Competency`
- `Topic`
- `Country`
- `Activity`
- `TrainerReference`
- `Outcome`
- `Source`

Core edges:
- `PUBLISHED_BY`
- `HOSTED_BY`
- `SUPPORTED_BY`
- `ELIGIBLE_FOR`
- `REQUIRES`
- `MATCHES`
- `SUPPORTED_BY_EVIDENCE`
- `APPLIED_TO`
- `RESULTED_IN`
- `PARTNERED_WITH`
- `TRAINED_AT`
- `FACILITATED`
- `VALIDATED_BY`
- `DERIVED_FROM`

Every edge that encodes a factual relationship should carry provenance where possible.

## 10. Scoring policy

Never mix eligibility with desirability.

1. Run hard gates.
2. If `FAIL`, score = 0.
3. If `UNKNOWN`, mark verification debt.
4. Score opportunity value/fit.
5. Score application competitiveness separately.
6. Store component scores, not only totals.

Weights are versioned in `configs/scoring.json`.

## 11. Agent roles

- **Scout**: discovers candidates; may not declare eligibility.
- **Verifier**: resolves source facts and freshness.
- **Infopack Analyst**: extracts requirements, finance, selection criteria, policy, logistics.
- **Eligibility Engine**: deterministic hard gates.
- **Ranker**: expected-value scoring.
- **Evidence Retriever**: retrieves private proof from Drive.
- **Application Strategist**: maps criteria -> evidence -> value proposition.
- **Policy Guard**: blocks prohibited AI/submission modes.
- **Trainer Career Agent**: tracks competencies, references and paid calls.
- **Outcome Analyst**: updates empirical priors from results.

One agent may perform multiple roles, but outputs must retain role boundaries.

## 12. Commit/checkpoint protocol

Use one coherent commit per completed execution wave. Before ending a working session:
1. update `goal-state.json`;
2. update this file's checkpoint table;
3. ensure tests for changed deterministic rules;
4. record known gaps explicitly;
5. push a portable `git.local` snapshot when the persistent handoff materially changed.

## 13. Current checkpoints

### Wave 0 — Definition & architecture
- [x] `/define-goal` written
- [x] goal-state machine contract
- [x] source-of-truth model
- [x] graph model
- [x] public/private boundary

### Wave 1 — Deterministic core
- [x] canonical domain models
- [x] eligibility hard-gate engine
- [x] opportunity scoring engine
- [x] AI-policy detector
- [x] graph event/projection primitives
- [x] infopack text extraction primitives
- [x] regression tests

### Wave 2 — Discovery connectors
- [ ] European Youth Portal collector
- [ ] SALTO European Training Calendar collector
- [ ] SALTO Call for Trainers collector
- [ ] Eurodesk / Eurodesk Spain collector
- [ ] organisation-watch collector
- [ ] canonical deduplication

### Wave 3 — Persistent data + Drive sync
- [ ] Postgres/Supabase adapter
- [ ] Drive evidence adapter
- [ ] infopack archive/sync
- [ ] opportunity CRM projection

### Wave 4 — Application intelligence
- [ ] private applicant evidence ingestion
- [ ] criterion-to-evidence retrieval
- [ ] dossier generator
- [ ] application form parser
- [ ] human-review queue

### Wave 5 — Compounding trainer path
- [ ] TOY readiness dashboard
- [ ] trainer calls collector
- [ ] trainer reference ledger
- [ ] fee/working-condition parser
- [ ] organiser relationship graph

### Wave 6 — Analytics + automation
- [ ] outcome feedback model
- [ ] source precision/recall analytics
- [ ] deadline/expiry watch
- [ ] recurring opportunity brief

## 14. Definition of done for an application dossier

A dossier is not `READY` unless:
- source and infopack were verified;
- deadline/date/country/age checks are resolved;
- AI policy is resolved;
- all mandatory questions are captured;
- each proposed claim maps to verified evidence;
- missing evidence is called out, not hallucinated;
- submission URL/mode is canonical;
- human review is explicit.

## Wave 2 incremental checkpoint — 2026-08-27
- [x] source registry loader
- [x] bounded HTTP fetch primitive + content hash
- [x] canonical URL normalisation
- [x] source-pattern link discovery primitives
- [x] stable opportunity fingerprint hierarchy
- [x] URL-level dedupe
- [x] deterministic TOY-reference qualification gates
- [x] application readiness / duplicate / evidence-gap gates
- [x] regression suite: 19 tests, 0 failures
- [ ] provider-specific pagination/extraction adapters
- [ ] persistent fetch state + incremental change detection
- [ ] first real opportunity batch persisted to CRM
