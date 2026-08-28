# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read in order:
> `goal.md` → `goal-state.json` → `AGENTS.md` → `ARCHITECTURE.md` → `docs/GRAPH_OPERATING_PROTOCOL.md` → relevant protocol/knowledge files.

## 1. Mission lock
Build an evidence-first operating system that discovers legitimate EU youth-mobility/trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes.

**North Star:** accepted high-value funded opportunities per human application hour. Never optimise raw submission volume.

## 2. Truth hierarchy
1. Original official page / original infopack / application form / organiser confirmation.
2. Platform eligibility rules + provider metadata/timestamps.
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

`DISCOVERED → INGESTED → DEDUPED → SOURCE_VERIFIED → PLATFORM_ELIGIBILITY_APPLIED → ELIGIBILITY_EVALUATED → INFOPACK_ANALYSED → FIT_SCORED → EXECUTION_PRIORITISED → APPLICATION_POLICY_RESOLVED → EVIDENCE_MAPPED → DOSSIER_READY → HUMAN_REVIEW → SUBMITTED → OUTCOME_RECORDED → LEARNING_EVENT`

Post-selection:
`ACCEPTED → PORTFOLIO_RESOLUTION? → COMMITTED`.

Credential-gap route:
`CREDENTIAL_GAP_IDENTIFIED → OUTREACH_PREPARED → HUMAN_REVIEW → COLLABORATION_CONFIRMED → ACTIVITY_DESIGNED → ACTIVITY_DELIVERED → EVIDENCE_PACK_CAPTURED → PROFILE_GATE_REEVALUATED`.

Terminal/alternate states include:
`DUPLICATE_MERGED`, `BLOCKED_INELIGIBLE`, `EVIDENCE_BLOCKED`, `EXPIRED`, `CLOSED`, `VERIFICATION_DEBT`, `HUMAN_WRITE_REQUIRED`, `WITHDRAWN`.

No agent chooses an arbitrary next step.

## 6. Hard gates
Block on a confirmed mandatory failure: platform target-group eligibility, deadline, residence/nationality, age, dates/availability, role/profile, previous-participation rule, support/sending organisation, mandatory language/conditions, duplicate submission or application policy.

Gate output = `PASS | FAIL | UNKNOWN`.
- `FAIL` blocks submission regardless of fit.
- `UNKNOWN` creates verification/evidence debt.
- High urgency may prioritise **verification**, never bypass a gate.

## 7. Platform eligibility is mandatory
Some sources impose eligibility before call-specific fit.

### SALTO European Training Calendar
Treat current SALTO ETC applicant guidance as a source-level requirement for existing youth-work/youth-training involvement or another target explicitly situated in the youth-work context.

After normalisation, `src/uexchanges/platform_policy.py` applies:
`salto_calendar -> requires_youth_work_context = true`.

Private profile state:
`youth_work_context_verified = true | false | null`.
- `true` only from real private evidence.
- `false` only from verified evidence.
- `null` when evidence is insufficient.

Do not auto-pass from subject expertise, a CV saying mentor/trainer, undelivered workshop material, photography/video work, AI expertise or self-description.

High Fit/Media/Trainer scores may make credential acquisition urgent; they never override the gate.

See `docs/PLATFORM_ELIGIBILITY_PROTOCOL.md`.

## 8. AI policy
Classify every call:
`AI_ALLOWED | AI_ASSIST_ONLY | AI_FINAL_TEXT_PROHIBITED | AI_UNKNOWN`.

- `AI_FINAL_TEXT_PROHIBITED`: research/evidence organisation allowed; final-answer drafting/rewrite disabled.
- `AI_UNKNOWN`: final-answer generation blocked until resolved.
- Do not treat lack of a visible prohibition as proof that AI is allowed.

## 9. Personalisation contract
No adjective without proof. Application value is:

`criterion → verified proof → concrete contribution → credible learning goal → multiplier/dissemination`.

Every externally used claim maps to a private Evidence Node. Never fabricate credentials, youth-work history, volunteering, fewer-opportunities status, language level, availability, organisation membership, disability/access needs or circumstances.

## 10. Score separation
Eligibility is not desirability.

- **Fit Score:** strategic/thematic value independent of deadline.
- **Media Value:** legitimate value of professional photo/video/storytelling.
- **Trainer Leverage:** potential to build NFE competence, organiser relationships, responsibility or qualifying references.
- **Deadline Urgency:** time pressure only.
- **Execution Priority:** chooses the next operation; never overrides hard gates.
- **Portfolio option cost:** represented by overlap graph, not hidden inside Fit Score.

Weights are versioned in `configs/scoring.json`.

## 11. Media contribution rule
Photography/videography is a reusable secondary value proposition, not automatic eligibility.

Safeguards:
- organiser approval;
- informed consent/privacy;
- safeguarding for minors/vulnerable/sensitive contexts;
- full programme participation remains primary;
- no over-promising deliverables.

## 12. Role lanes
`PARTICIPANT · YOUTH_WORKER · FACILITATOR · TRAINER · EXPERT`.

Positioning is role-aware. Participant applications do not pretend to be trainer applications. Trainer calls require educational responsibility, methods, outcomes and references.

## 13. Credential / trainer progression
Current verified TOY-qualifying references: **0**.

Strategy: **BUILD, DO NOT CLAIM.**

Credential ladder:
`L0 self-description → L1 verified affiliation/collaboration → L2 delivered youth activity → L3 external reference/repeated practice → L4 TOY-qualifying international full-time trainer reference`.

Target path:
`Professional subject expertise → verified youth-work context → participant/youth-facing activity → real NFE contribution → organiser reference → co-facilitation → full-time international trainer refs #1–#3 → TOY-ready → paid trainer calls`.

A local short workshop can build L2/L3 evidence; it is not silently a TOY reference.

See `docs/CREDENTIAL_ACQUISITION_LOOP.md` and `knowledge/TRAINER_PATH.md`.

## 14. Graph contract
History is append-only; projections are rebuildable.

Core nodes:
`Person`, `Opportunity`, `Programme`, `Organisation`, `Call`, `Infopack`, `Application`, `Evidence`, `Requirement`, `Competency`, `Topic`, `Country`, `Activity`, `TrainerReference`, `Outcome`, `Source`.

Core edges include:
`PUBLISHED_BY`, `HOSTED_BY`, `SUPPORTED_BY`, `ELIGIBLE_FOR`, `REQUIRES`, `MATCHES`, `SUPPORTED_BY_EVIDENCE`, `APPLIED_TO`, `RESULTED_IN`, `PARTNERED_WITH`, `TRAINED_AT`, `FACILITATED`, `VALIDATED_BY`, `DERIVED_FROM`, `MUTUALLY_EXCLUSIVE_IF_ACCEPTED`.

Do not introduce specialised graph/vector infrastructure until real queries/scale justify it.

## 15. Fact conflicts
Never resolve conflicting evidence by majority vote or LLM preference.

Use `src/uexchanges/facts.py`:
- missing -> `VERIFY_MISSING_FACT`
- consistent -> `RESOLVE_CONSISTENT_FACT`
- conflict default -> `VERIFY_CONFLICTING_FACT`
- only a unique, highest-authority, live-current and strictly newer peer claim may produce `LIVE_SOURCE_SUPERSEDES_STALE_ARTIFACT`.

## 16. Portfolio commitment guard
Opportunity applications may overlap. Preserve option value.

Before `ACCEPTED -> COMMITTED`, use the portfolio graph. An overlapping `ACCEPTED/COMMITTED` node routes to `PORTFOLIO_RESOLUTION`. An empty calendar is not proof of real-world availability.

See `docs/PORTFOLIO_CONFLICT_GRAPH.md`.

## 17. Provider access rules
Never treat a zero-result generic scraper as success and never bypass authentication/access controls.

- SALTO Training Calendar: static/paginated discovery + platform eligibility policy + verified detail pages.
- SALTO Calls for Trainers: public detail pages only when legitimately discoverable.
- European Youth Portal / Eurodesk: supported browser/search/API-backed discovery for dynamic indexes.
- Telegram/social archives: discovery only; promote facts after stable identity + higher-authority verification.

## 18. Anti-duplicate hierarchy
1. provider project/call ID;
2. provider/channel post ID;
3. canonical application/opportunity URL;
4. fallback `(host, normalised title, start date, country)`.

Raw duplicates remain provenance nodes; only one canonical opportunity is promoted.

## 19. Agent roles
- **Scout** — discovery only.
- **Deduper** — canonical merge.
- **Verifier** — source facts/freshness/conflicts.
- **Platform Policy Guard** — source-level target requirements.
- **Infopack Analyst** — requirements/funding/logistics/policy.
- **Eligibility Engine** — hard gates.
- **Ranker** — score components/execution priority.
- **Evidence Retriever** — private proof.
- **Credential Builder** — turns evidence gaps into legitimate activity/outreach plans; never fabricates completion.
- **Application Strategist** — criteria→proof→value mapping.
- **Policy Guard** — duplicate/AI/submission blocks.
- **Portfolio Guard** — acceptance/commitment conflicts.
- **Trainer Career Agent** — credential/reference/call graph.
- **Outcome Analyst** — results and empirical priors.

One agent may hold several roles, but outputs must preserve role boundaries.

## 20. Dossier definition of done
`READY_TO_SUBMIT` requires:
- canonical identity resolved;
- source/current call verified;
- platform requirements applied;
- hard eligibility = PASS;
- deadline open;
- infopack/form requirements captured;
- AI policy resolved;
- mandatory documents ready;
- every external claim mapped to evidence;
- duplicate check passed;
- human review completed.

A strategic dossier may exist earlier but must be visibly marked `EVIDENCE_BLOCKED`, `NEEDS_EVIDENCE`, `NEEDS_VERIFICATION`, or `NOT FINAL SUBMISSION TEXT`.

## 21. Todoist rules
Dedicated project creation is currently blocked by the account's active-project limit; no workspace fallback is available.

Until a project slot exists:
- use Inbox master graph task + labels + Wave subtasks;
- preserve truth in CRM/GitHub;
- never archive/delete unrelated projects automatically;
- recurring daily discovery is allowed.

## 22. Commit/checkpoint protocol
Before ending a coherent wave:
1. update `goal-state.json`;
2. update AGENTS/protocol docs when routing changes;
3. run relevant deterministic tests;
4. record local vs remote test scope honestly;
5. open PR and observe exact-head CI;
6. merge only after green exact-head CI;
7. refresh git.local when handoff changes materially.

## 23. Current checkpoint — 2026-08-28
Main release: v0.3 merged, PR #4 and main push CI green.

Operational truth:
- 23 canonical opportunities + Decision Queue in Drive CRM;
- supplied Telegram raw refs: 61 / 60 unique / 1 exact duplicate;
- private evidence bank seeded, but delivered youth-work/NFE evidence remains unverified;
- SALTO high-fit nodes Digi-Hack, Unleashing Creativity and CTRL+REAL are now `EVIDENCE_BLOCKED`, not application-ready;
- Credential Acquisition Loop exists in Drive/Todoist;
- collaboration drafts to Euroacción, 585m² Espacio Joven and Murcia Youth Service are prepared and unsent;
- participant-youth-exchange/ESC lane continues independently under its own call-specific eligibility.

## 24. Next mandatory operations
1. Finish v0.4 Platform Eligibility PR + CI.
2. Review/send credential-acquisition drafts only with human approval.
3. Deliver a real youth activity; capture L2 evidence; re-evaluate private youth-work context.
4. Continue daily discovery of participant Youth Exchanges/ESC and broader opportunities where no SALTO platform gate applies.
5. Promote only `PASS + policy-resolved` nodes to final submission.
6. Capture submission receipts/outcomes and update organisation/source priors.
