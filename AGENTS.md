# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read in order:
> `goal.md` → `goal-state.json` → `AGENTS.md` → `ARCHITECTURE.md` → `docs/GRAPH_OPERATING_PROTOCOL.md` → latest `checkpoints/` → relevant `knowledge/`.

## 1. Mission lock
Build an evidence-first operating system that discovers legitimate EU youth-mobility/trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes.

**North Star:** accepted high-value funded opportunities per human application hour. Never optimise raw submission volume.

## 2. Truth hierarchy
1. Original official page / original infopack / application form / organiser confirmation.
2. Provider metadata and timestamps.
3. Normalised canonical record.
4. Deterministic rules/calculations.
5. LLM extraction/classification with explicit provenance.
6. Heuristic ranking.

`UNKNOWN` is a first-class state. Never silently coerce it to `PASS`.

## 3. Source-of-truth topology
- Original official evidence = authority for opportunity facts.
- GitHub = executable/versioned truth for schemas, rules, collectors, tests and public knowledge.
- Google Drive = private applicant evidence, infopacks, dossiers, CRM and trainer references.
- Library `/git.local/UE-Xchanges-OS` = portable cold-start snapshot.
- Graph projections = disposable/rebuildable from evidence + append-only events.
- Todoist = execution projection only; never authoritative opportunity data.

## 4. Public/private boundary
Public GitHub may contain code, public programme/source facts, anonymised fixtures and aggregate metrics. It must not contain identity/contact documents, private application answers/emails, medical/accessibility data, restricted infopacks, secrets or private applicant evidence.

Private operational data belongs under Drive `07_PERSONAL_TRAVEL/01_TRAVEL/UE_XCHANGES_OS/`.

## 5. Mandatory graph execution path
Canonical route:

`DISCOVERED → INGESTED → DEDUPED → SOURCE_VERIFIED → ELIGIBILITY_EVALUATED → INFOPACK_ANALYSED → FIT_SCORED → EXECUTION_PRIORITISED → APPLICATION_POLICY_RESOLVED → EVIDENCE_MAPPED → DOSSIER_READY → HUMAN_REVIEW → SUBMITTED → OUTCOME_RECORDED → LEARNING_EVENT`

Terminal/alternate states include:
`DUPLICATE_MERGED`, `BLOCKED_INELIGIBLE`, `EXPIRED`, `CLOSED`, `VERIFICATION_DEBT`, `HUMAN_WRITE_REQUIRED`, `WITHDRAWN`.

No agent chooses an arbitrary next step. `docs/GRAPH_OPERATING_PROTOCOL.md` defines transition guards and decision codes.

## 6. Hard gates
Block on a confirmed mandatory failure: deadline, residence/nationality, age, dates/availability, role/profile, previous-participation rule, support/sending organisation, mandatory language/conditions, duplicate submission or application policy.

Gate output = `PASS | FAIL | UNKNOWN`.
- `FAIL` blocks submission regardless of fit.
- `UNKNOWN` creates verification debt.
- High urgency may prioritise **verification**, never bypass a gate.

## 7. AI policy
Classify every call:
`AI_ALLOWED | AI_ASSIST_ONLY | AI_FINAL_TEXT_PROHIBITED | AI_UNKNOWN`.

- `AI_FINAL_TEXT_PROHIBITED`: research/evidence organisation allowed; final-answer drafting/rewrite disabled.
- `AI_UNKNOWN`: final-answer generation blocked until resolved.
- Do not treat lack of a visible prohibition as proof that AI is allowed.

## 8. Personalisation contract
No adjective without proof. Application value is:

`criterion → verified proof → concrete contribution → credible learning goal → multiplier/dissemination`.

Every externally used claim maps to a private Evidence Node. Never fabricate credentials, youth-work history, volunteering, fewer-opportunities status, language level, availability, organisation membership, disability/access needs or circumstances.

## 9. Score separation
Eligibility is not desirability.

### Fit Score
Strategic/thematic value independent of deadline.

### Media Value
Potential legitimate value of professional photo/video/storytelling for project learning/documentation/dissemination.

### Trainer Leverage
Potential to build NFE competence, organiser relationships, facilitation responsibility or qualifying trainer references.

### Deadline Urgency
Time pressure only.

### Execution Priority
Chooses the next operation. It never overrides duplicate, expiry, conflict, eligibility or policy gates.

Weights are versioned in `configs/scoring.json`.

## 10. Media contribution rule
Professional photography/videography is a reusable secondary value proposition, not the reason someone is automatically eligible.

Use only when relevant and permitted. Required safeguards:
- organiser approval;
- informed consent/privacy process;
- special care with minors/vulnerable/sensitive contexts;
- no reduction in full programme participation;
- no over-promising deliverables.

See `knowledge/MEDIA_CONTRIBUTION.md`.

## 11. Role lanes
`PARTICIPANT · YOUTH_WORKER · FACILITATOR · TRAINER · EXPERT`.

Positioning is role-aware. Participant applications do not pretend to be trainer applications. Trainer calls require educational responsibility, methods, outcomes and references.

## 12. Credential / trainer progression
Current verified TOY-qualifying references: **0**.

Strategy: **BUILD, DO NOT CLAIM.**

Credential levels:
`L0 self-description → L1 artifact → L2 delivery proof → L3 outcome/reference → L4 TOY-qualifying reference`.

Target path:
`Professional subject expertise → youth-work eligibility confirmation → participation → real NFE/youth-facing contribution → organiser reference → co-facilitation → full-time international trainer refs #1–#3 → TOY-ready → paid trainer calls`.

A TOY candidate reference must independently satisfy the current SALTO criteria. Participant/group-leader status or one isolated workshop is not silently counted.

See `knowledge/CREDENTIAL_ACQUISITION_GRAPH.md` and `knowledge/TRAINER_PATH.md`.

## 13. Graph contract
History is append-only; projections are rebuildable.

Core nodes:
`Person`, `Opportunity`, `Programme`, `Organisation`, `Call`, `Infopack`, `Application`, `Evidence`, `Requirement`, `Competency`, `Topic`, `Country`, `Activity`, `TrainerReference`, `Outcome`, `Source`.

Core edges:
`PUBLISHED_BY`, `HOSTED_BY`, `SUPPORTED_BY`, `ELIGIBLE_FOR`, `REQUIRES`, `MATCHES`, `SUPPORTED_BY_EVIDENCE`, `APPLIED_TO`, `RESULTED_IN`, `PARTNERED_WITH`, `TRAINED_AT`, `FACILITATED`, `VALIDATED_BY`, `DERIVED_FROM`.

Do not introduce Neo4j/Qdrant or another specialised graph/vector store until real queries/scale justify it. SQLite is acceptable for single-operator collector state; Postgres/Supabase remains the v1 shared persistence target.

## 14. Provider access modes
Never treat a zero-result generic scraper as success.

- SALTO Training Calendar: static/paginated HTML plus verified detail pages.
- SALTO Calls for Trainers: public detail pages only when legitimately discoverable; never bypass MySALTO auth.
- European Youth Portal / Eurodesk: supported browser/search/API-backed discovery when their indexes are dynamic.
- Telegram/public social archives: discovery sources only; promote facts only after mapping to stable provider keys and higher-authority source/infopack where available.

## 15. Anti-duplicate identity hierarchy
1. provider project/call ID;
2. provider/channel post ID;
3. canonical application/opportunity URL;
4. fallback fingerprint `(host, normalised title, start date, country)`.

Raw duplicates remain as provenance nodes but only one canonical opportunity may be promoted.

## 16. Agent roles
- **Scout** — discovery only.
- **Deduper** — identity/canonical merge.
- **Verifier** — source facts/freshness/conflicts.
- **Infopack Analyst** — requirements/funding/logistics/policy.
- **Eligibility Engine** — hard gates.
- **Ranker** — score components and execution priority.
- **Evidence Retriever** — private proof retrieval.
- **Application Strategist** — criteria→proof→value mapping.
- **Policy Guard** — duplicate/AI/submission blocks.
- **Trainer Career Agent** — credential/reference/call graph.
- **Outcome Analyst** — results and empirical priors.

One agent may hold several roles, but outputs and decisions must preserve role boundaries.

## 17. Dossier definition of done
`READY_TO_SUBMIT` requires:
- canonical identity resolved;
- source/current call verified;
- hard eligibility = PASS;
- deadline open;
- infopack/form requirements captured;
- AI policy resolved;
- mandatory documents ready;
- every external claim mapped to evidence;
- duplicate check passed;
- human review completed.

A strategic/internal dossier may exist earlier but must be visibly marked `NEEDS_EVIDENCE`, `NEEDS_VERIFICATION`, or `NOT FINAL SUBMISSION TEXT`.

## 18. Todoist rules
Requested dedicated project creation currently fails because the Todoist account is at its active-project limit; no workspace fallback is available. Filter creation also hits the account filter limit.

Until a project slot exists:
- use the Inbox master graph task + labelled Wave/subtasks;
- preserve graph state in CRM/GitHub, not Todoist;
- do not archive/delete unrelated Todoist projects automatically;
- recurring daily opportunity/deadline sweep is allowed as execution projection.

## 19. Commit/checkpoint protocol
Before ending a coherent wave:
1. update `goal-state.json`;
2. create/update latest `checkpoints/` file;
3. update this AGENTS contract if routing/roles changed;
4. run relevant deterministic tests;
5. record test scope honestly;
6. observe remote CI after opening a PR;
7. refresh `git.local` when handoff changes materially.

## 20. Current checkpoint — 2026-08-27
Latest detailed state: `checkpoints/2026-08-27-wave2c-3.md`.

Current private CRM state:
- 23 canonical opportunity rows;
- 21 opportunities from supplied Doc 1;
- 61 raw Telegram references / 60 unique provider keys / 1 exact duplicate;
- P0/P1 active dossiers for Unleashing Creativity, CTRL+REAL, Game of Nature and Building With Our Hands;
- eligibility dossiers for Blue Book and Amani Pamoja;
- organiser-verification drafts created for AREAAA, YUPI and Papaya, not sent.

Current strongest nodes:
- `Unleashing Creativity: From Lens to Life` — subject fit 100 / media 100 / trainer leverage 98; role evidence unresolved.
- `CTRL+REAL` — subject fit 100 / trainer leverage 100; role evidence unresolved.
- `Building With Our Hands` — source/current-call/AI-policy verification pending.
- `Game of Nature` — community/youth/education-profile evidence pending.

Quality truth:
- merged PR #1 baseline: 27 tests / 0 failures; GitHub Actions run 33091677275 = success.
- post-PR1 scoring/workflow/credential changes: 14 focused checks / 0 failures; full remote CI pending PR #2.

## 21. Next mandatory operations
1. Open PR #2 and observe CI.
2. Review/send organiser eligibility/current-call queries.
3. Convert organiser replies into provenance-backed gate events.
4. Resolve private residence/age/availability and call-specific formal evidence.
5. Parse forms only for viable nodes.
6. Generate final submission answers only after policy/evidence gates pass.
7. Store submission receipt/outcome and update organisation priors.
