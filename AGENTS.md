# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session operating contract. Read in order:
> `goal.md` → `goal-state.json` → `AGENTS.md` → `ARCHITECTURE.md` → `docs/GRAPH_OPERATING_PROTOCOL.md` → `docs/PLATFORM_ELIGIBILITY_PROTOCOL.md` → `docs/TEMPORAL_EVIDENCE_PROTOCOL.md` → `docs/OUTCOME_LEARNING_PROTOCOL.md` → relevant knowledge/checkpoints.

## 1. Mission lock
Build an evidence-first operating system that discovers legitimate EU youth-mobility/trainer opportunities, verifies eligibility, reads infopacks, ranks expected value, prepares truthful personalised dossiers, and compounds acceptance/trainer outcomes.

**North Star:** accepted high-value funded opportunities per human application hour. Never optimise raw submission volume.

## 2. Truth hierarchy
1. Original official page / original infopack / application form / organiser confirmation / official outcome evidence.
2. Platform eligibility rules + provider metadata/timestamps.
3. Normalised canonical record.
4. Deterministic rules/calculations.
5. LLM extraction/classification with explicit provenance.
6. Heuristic ranking or evidence-calibrated prior.

`UNKNOWN` is a first-class state. Never silently coerce it to `PASS`.

## 3. Source-of-truth topology
- Original official evidence = authority for opportunity/outcome facts.
- GitHub = executable/versioned truth for schemas, rules, collectors, tests and public knowledge.
- Google Drive = private applicant evidence, infopacks, dossiers, CRM, outcomes and trainer references.
- Library `/git.local/UE-Xchanges-OS` = portable cold-start snapshot.
- Graph projections = disposable/rebuildable from evidence + append-only events.
- Todoist = execution projection only; never authoritative opportunity data.

## 4. Public/private boundary
Public GitHub may contain code, public programme/source facts, anonymised fixtures and aggregate metrics. It must not contain identity/contact documents, historical application answers, medical/accessibility data, private emails, restricted infopacks, secrets or private applicant evidence.

Private operational data belongs under Drive `07_PERSONAL_TRAVEL/01_TRAVEL/UE_XCHANGES_OS/`.

## 5. Mandatory execution graph
Canonical application route:

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
- High urgency may prioritise verification, never bypass a gate.

## 7. Platform eligibility
Some sources impose eligibility before call-specific fit.

### SALTO European Training Calendar
Current source policy: listings target youth workers/trainers or people already involved in youth-work context. `src/uexchanges/platform_policy.py` sets `requires_youth_work_context = true` for `salto_calendar`.

Current-context gate uses only:
`youth_work_context_verified = true | false | null`.

Do not auto-pass from subject expertise, a CV saying trainer/mentor, undelivered materials, photography/video work, AI expertise, historical mobility, or self-description.

## 8. Temporal evidence semantics — mandatory
Historical youth-sector experience, current youth-work involvement, delivery/facilitation responsibility and trainer qualification are **four different facts**.

Private profile fields include:
- `youth_sector_experience_verified`
- `youth_sector_last_activity_date`
- `completed_erasmus_youth_staff_mobilities`
- `completed_erasmus_youth_exchanges`
- `youth_work_context_verified` — CURRENT context only.

Rules:
1. Historical verified mobility may support programme literacy, experience, fit and organisation priors.
2. Historical mobility never auto-promotes current youth-work context.
3. Attendance never implies facilitator/trainer responsibility.
4. Participant/group-leader/facilitator/trainer roles remain separate; unknown role stays unknown.
5. A call saying `currently active` requires current evidence regardless of historical experience.
6. A call asking for `experience in` may use historical evidence only to the strength of its verified `role_scope`.
7. Never claim first-time Erasmus participation when verified prior mobilities exist.

See `docs/TEMPORAL_EVIDENCE_PROTOCOL.md`.

## 9. Current private historical evidence — use by reference, not public replication
Private evidence currently verifies at least:
- 2 completed Erasmus+ KA1 Youth Staff professional-development mobilities (2022 Germany; 2023 Türkiye);
- 1 completed Erasmus+ Youth Exchange (January 2024; exact participant/group-leader role unresolved);
- Youthpass/attendance for the 2022 training;
- prior accepted/completed relationship with Ticket2Europe.

These facts belong in the private Evidence Graph. Public repo stores only schema/protocol semantics, never personal email/form content.

Current verified TOY-qualifying trainer references remain **0**.

## 10. AI policy
Classify every call:
`AI_ALLOWED | AI_ASSIST_ONLY | AI_FINAL_TEXT_PROHIBITED | AI_UNKNOWN`.

- `AI_FINAL_TEXT_PROHIBITED`: research/evidence organisation allowed; final-answer drafting/rewrite disabled.
- `AI_UNKNOWN`: final-answer generation blocked until resolved.
- Absence of a visible prohibition is not proof that AI is allowed.

## 11. Personalisation contract
No adjective without proof. Application value is:

`criterion → verified proof → concrete contribution → credible learning goal → multiplier/dissemination`.

Every externally used claim maps to a private Evidence Node. Never fabricate credentials, current youth-work history, volunteering, fewer-opportunities status, language level, availability, organisation membership, disability/access needs or circumstances.

Historical application answers are not objective evidence. A previously accepted application is a **selection prior**, not proof that every self-reported statement in it was true/current.

## 12. Score separation
Eligibility is not desirability.
- **Fit Score** — strategic/thematic value.
- **Media Value** — legitimate photo/video/storytelling contribution.
- **Trainer Leverage** — NFE/relationship/responsibility/reference leverage.
- **Deadline Urgency** — time pressure only.
- **Execution Rank** — chooses what operation happens next after state penalties/route bonuses.
- **Portfolio option cost** — represented by overlap graph, not hidden in fit.
- **Competition density / outcome priors** — may inform selection leverage but cannot fabricate rejection causes.

High strategic fit never outranks an executable route solely because fit is higher. `EVIDENCE_BLOCKED` and `CONSTRAINT_BLOCKED` receive routing penalties.

## 13. Outcome-learning contract — causal strength first
Do **not** fit an acceptance-probability model from sparse outcomes. `src/uexchanges/outcomes.py` determines which learning updates are allowed.

Canonical outcomes:
- `ACCEPTED_COMPLETED`
- `ACCEPTED`
- `WAITLIST_PRIORITY`
- `WAITLIST_UNRANKED`
- `REJECTED_WITH_FEEDBACK`
- `REJECTED_HIGH_COMPETITION`
- `REJECTED_NO_REASON`
- `NO_RESPONSE`
- `WITHDRAWN`

Rules:
1. Ranked waitlist 1–3 = weak near-accept/positive signal; never a negative application penalty without feedback.
2. Unranked waitlist = viable/near-accept with unknown strength; never invent rank, never assume top-3, never train negative penalty.
3. High-competition rejection without individual reason updates competition/base-rate prior only.
4. No-response updates organisation response behaviour only; it is not a verified rejection.
5. Accepted/completed supports a positive selection/relationship prior but does not prove every application component caused selection.
6. Only explicit organiser feedback may update a call-specific negative criterion heuristic.
7. Specific feedback stays call/criterion scoped and never becomes a universal rule.
8. One acceptance/rejection/waitlist never becomes a universal rule.
9. Organisation relationship priors are separate from eligibility.

See `docs/OUTCOME_LEARNING_PROTOCOL.md`. Private CRM `Outcome_History` is the operational projection.

## 14. Media contribution rule
Photography/videography is a reusable secondary value proposition, not automatic eligibility.

Use only when relevant to project outputs/documentation/dissemination. Safeguards:
- organiser approval;
- informed consent/privacy;
- special care with minors/vulnerable/sensitive contexts;
- full programme participation remains primary;
- no over-promising deliverables.

## 15. Role lanes and trainer progression
`PARTICIPANT · YOUTH_WORKER · FACILITATOR · TRAINER · EXPERT`.

Strategy: **BUILD, DO NOT CLAIM.**

Credential ladder:
`L0 self-description → L1 verified affiliation/collaboration → L2 delivered youth activity → L3 external reference/repeated practice → L4 TOY-qualifying international full-time trainer reference`.

Target path:
`professional subject expertise + verified historical programme experience → refreshed/current youth-work context → youth-facing contribution → co-facilitation → qualifying trainer refs #1–#3 → TOY-ready → paid trainer calls`.

Historical Youth Staff participation is useful context but not a trainer reference.

## 16. Fact conflicts
Never resolve conflicting evidence by majority vote or LLM preference.

`src/uexchanges/facts.py`:
- missing → `VERIFY_MISSING_FACT`
- consistent → `RESOLVE_CONSISTENT_FACT`
- conflict default → `VERIFY_CONFLICTING_FACT`
- only a unique, highest-authority, live-current and strictly newer peer claim may produce `LIVE_SOURCE_SUPERSEDES_STALE_ARTIFACT`.

## 17. Portfolio commitment guard
Applications may overlap. Preserve option value. Before `ACCEPTED → COMMITTED`, resolve overlapping accepted/committed nodes. Empty Calendar is weak evidence only, never proof of real-world availability.

## 18. Provider access rules
Never treat a zero-result generic scraper as success and never bypass authentication/access controls.
- SALTO Training Calendar: static/paginated discovery + source-level platform policy + verified details.
- SALTO Calls for Trainers: public detail pages only when legitimately discoverable.
- European Youth Portal / Eurodesk: supported browser/search/API-backed discovery for dynamic indexes.
- Telegram/social archives: discovery only until higher-authority verification.
- Sending-organisation archives may seed calls, but each call still needs current form/deadline validation.

## 19. Anti-duplicate hierarchy
1. provider project/call ID;
2. provider/channel post ID;
3. canonical application/opportunity URL;
4. fallback `(host, normalised title, start date, country)`.

Raw duplicates remain provenance nodes; only one canonical opportunity is promoted.

## 20. Agent roles
- Scout — discovery only.
- Deduper — canonical identity/merge.
- Verifier — source facts/freshness/conflicts.
- Platform Policy Guard — source-level target requirements.
- Temporal Evidence Guard — separates historical/current/role-scope evidence.
- Infopack Analyst — requirements/funding/logistics/policy.
- Eligibility Engine — hard gates.
- Ranker — fit/urgency/execution rank.
- Evidence Retriever — private proof.
- Credential Builder — legitimate activity/outreach to close gaps.
- Application Strategist — criteria→proof→value mapping.
- Policy Guard — duplicate/AI/submission blocks.
- Portfolio Guard — acceptance/commitment conflicts.
- Trainer Career Agent — credentials/references/paid calls.
- Outcome Analyst — causal-strength learning + organisation priors.

One agent may hold several roles, but outputs must preserve role boundaries.

## 21. Dossier definition of done
`READY_TO_SUBMIT` requires:
- canonical identity resolved;
- source/current call verified;
- platform requirements applied;
- hard eligibility = PASS;
- deadline open;
- infopack/form requirements captured;
- AI policy resolved;
- mandatory documents ready;
- every external claim mapped to evidence with correct temporal/role scope;
- duplicate check passed;
- human review completed.

Earlier dossiers must be visibly marked `EVIDENCE_BLOCKED`, `NEEDS_EVIDENCE`, `NEEDS_VERIFICATION`, `VERIFICATION_DEBT` or `NOT FINAL SUBMISSION TEXT`.

## 22. Todoist rules
Dedicated project creation is currently blocked by the account's active-project limit. Until a slot exists:
- use the existing master graph task + labelled Wave/subtasks;
- preserve truth in CRM/GitHub;
- never archive/delete unrelated projects automatically.

## 23. Commit/checkpoint protocol
Before ending a coherent wave:
1. update `goal-state.json`;
2. update AGENTS/protocol docs when routing changes;
3. add/update checkpoint;
4. run relevant deterministic tests;
5. record local vs remote test scope honestly;
6. open PR and observe exact-head CI;
7. merge only after green exact-head CI;
8. refresh git.local when handoff changes materially.

## 24. Current checkpoint — 2026-08-28 / v0.6
Operational truth:
- 34 canonical opportunities;
- 12 application nodes;
- 13 organisation nodes;
- 4 structured outcomes in `Outcome_History`;
- private Evidence Bank contains EV-001..EV-012;
- verified historical minimum: 2 Youth Staff professional-development mobilities + 1 Youth Exchange;
- current youth-work context remains unresolved;
- TOY-qualified trainer references = 0;
- Ticket2Europe relationship prior = `PAST_ACCEPTED_PARTICIPANT`;
- outcome fixtures: Ticket2Europe `ACCEPTED_COMPLETED`, BreGal `WAITLIST_PRIORITY_1`, Youth BCN `WAITLIST_UNRANKED`, Make it Happen `REJECTED_HIGH_COMPETITION` (430+ / no individual reason);
- P0 verification queue includes Thrive and Shine, Future Careers & AI, Building With Our Hands, O-live T.R.E.E.S. and Triglav;
- combined Ticket2Europe, Papaya and BreGal communications remain drafts, not sent;
- probabilistic acceptance forecasting remains disabled.

Release truth:
- v0.6 PR #7 exact head `1994fb6c3a2da892c964d03354089df7c7bae103` passed CI;
- merged commit `e3bb4d053114d68cf827e7e9d297303f9c05548d` passed main push CI.

## 25. Next mandatory operations
1. Refresh `/git.local/UE-Xchanges-OS` to v0.6 and run the full local suite before overwriting Library.
2. Keep Ticket2Europe/Papaya/BreGal communications as drafts until human send approval.
3. Resolve Future Careers date/current-call conflict and O-live Spanish application route.
4. Resolve Thrive original source and YUPI current call.
5. Progress Game of Nature only after current-profile criterion is resolved.
6. Continue outcome discovery/calibration without inventing rejection reasons or waitlist ranks.
7. Build current youth-work L2/L3 evidence; historical mobility does not replace current delivery evidence.
