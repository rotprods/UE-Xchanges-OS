# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session contract for v0.8.1. Read:
> `goal.md` → `goal-state.json` → this file → `ARCHITECTURE.md` → `docs/MASS_APPLY_POLICY.md` → `docs/AUTOFILL_AND_APPLICATION_MODULE_POLICY.md` → `docs/GRAPH_OPERATING_PROTOCOL.md` → current checkpoint.

## 1. Mission lock

Discover, register, verify, prepare and execute **every live Spain-compatible opportunity** across Erasmus+ Youth Exchanges, ESC, Eurodesk, non-SALTO participant routes, SALTO training and paid trainer/facilitator calls.

**North Star:** valid receipt-backed applications per live Spain-compatible opportunity, subject to zero known hard-SLO violations.

Priority, fit and thematic value are scheduling fields. They do not exclude a viable application.

## 2. Truth hierarchy

1. Current official page / original infopack / authorised form / organiser confirmation / submission receipt.
2. Private Drive CRM and evidence graph.
3. Canonical GitHub state, policies, schemas and deterministic rules.
4. LLM extraction with provenance.
5. Heuristic ranking and execution projection.

`UNKNOWN` is first-class verification debt. Never silently coerce it to `PASS` or `FAIL`.

## 3. Source topology and privacy

- GitHub is public and stores code, schemas, public facts, aggregate state and tests.
- Drive stores applicant identity/evidence, private emails, original/restricted infopacks, autofill values, answers, final assets and receipts.
- Todoist is an execution projection only.
- No private applicant text or sensitive value enters public GitHub.

Private root: `07_PERSONAL_TRAVEL/01_TRAVEL/UE_XCHANGES_OS/`.

## 4. Apply-everything contract

Every non-duplicate call enters CRM when Spain is listed, a Spanish route exists, or that route remains plausibly verifiable and the deadline has not been proven closed.

Only objective terminal reasons remove a call:

`DEADLINE_PASSED · SPAIN_NOT_ELIGIBLE · HARD_REQUIREMENT_FAIL · CALL_CLOSED · APPLICATION_ROUTE_INVALID · DUPLICATE_SUBMISSION`

Low fit, duration, cost, potential overlap, topic or predicted acceptance are not terminal reasons. Conflicts are resolved after acceptance.

## 5. Mandatory graph

`DISCOVERED → INGESTED → DEDUPED → SOURCE_VERIFIED → SPAIN_ROUTE_VERIFIED → DEADLINE_VERIFIED → ROLE_PROFILE_EXTRACTED → INFOPACK_CAPTURED → INFOPACK_ANALYSED → FORM_CAPTURED → APPLICATION_POLICY_RESOLVED → EVIDENCE_MAPPED → ANSWER_DRAFTED → HUMAN_OWNED_FINAL_TEXT → QA → SUBMITTED → RECEIPT_STORED → OUTCOME_RECORDED → ACCEPTANCE_DECISION`

No agent chooses an arbitrary next state or skips a gate.

## 6. Gates

Gate output: `PASS | FAIL | UNKNOWN`.

Mandatory checks include source/current status, deadline/time zone, Spain/residence/nationality, age, dates/availability, role/profile, language, degree, affiliation, previous participation, ESC/EVS limits, sending/support organisation, form/channel, duplicate state and AI/application policy.

- `FAIL` is call-specific terminal.
- `UNKNOWN` creates a task with owner and deadline.
- Urgency accelerates verification; it never bypasses it.
- A broad private gate may pass once, but must be rechecked if call dates or conditions materially change.

## 7. Temporal and role evidence

Historical youth-sector experience, current youth-work context, delivery/facilitation responsibility and trainer qualification are separate facts.

Verified private aggregate context:

- two completed Erasmus+ KA1 Youth Staff professional-development mobilities;
- one completed Erasmus+ Youth Exchange;
- current youth-work context: `UNKNOWN`;
- TOY-qualifying trainer references: `0`.

Attendance never implies facilitator or trainer responsibility. Never claim first-time Erasmus participation.

## 8. AI/application policy

Classify each route as:

`AI_ALLOWED | AI_ASSIST_ONLY | AI_FINAL_TEXT_PROHIBITED | AI_UNKNOWN`

- `AI_UNKNOWN`: source extraction and evidence mapping may continue; final AI-generated prose stays blocked unless the applicant independently authors it.
- `AI_ASSIST_ONLY`: evidence, structure, gap analysis and QA are allowed; final wording follows organiser guidance and remains applicant-owned.
- `AI_FINAL_TEXT_PROHIBITED`: no final-answer drafting or rewriting; provide facts/outline only.
- Absence of a visible prohibition is not proof of permission.

Maximum application volume never overrides a call-specific policy.

## 9. Autofill profile contract

The private Drive CRM tab `Autofill_Profile` is the reusable factual profile.

Every field has a canonical private value, verification strength, allowed external use and an explicit next gate if incomplete. Blank means unknown.

The system may reuse verified factual fields, but must not infer or publicly expose phone, date of birth, identity-document details, emergency contacts, health/accessibility data or private addresses.

Current aggregate private-gate state is recorded in `goal-state.json`; exact values remain in Drive.

## 10. Application module contract

The private Drive CRM tab `Application_Modules` contains reusable evidence-backed building blocks. Modules are not final generic templates.

Every answer follows:

`call criterion → verified evidence → project-specific contribution → credible learning goal → proportionate multiplier`

A module must be adapted to the exact question, character limit, target group, project activities and AI policy.

## 11. Dossier contract

Every application row has:

1. canonical identity and source;
2. deadline and Spain route;
3. eligibility/funding/conditions extraction;
4. gate matrix;
5. infopack and form state;
6. exact questions/character limits when captured;
7. criterion → evidence_id → allowed claim map;
8. adapted contribution/learning/dissemination modules;
9. human-owned final assets;
10. QA and receipt block.

A skeleton is labelled as such. It is never described as a completed personalised application.

## 12. Personalisation and claims

Externally used claims follow:

`criterion → private evidence → allowed factual claim → specific contribution → credible learning → dissemination`

Never fabricate current youth-work, NFE, trainer/facilitator history, degree, CEFR, student status, organisation mandate, availability, residence, disability, fewer opportunities, practical experience or any sensitive circumstance.

A self-reported skill without task/date/location evidence may support willingness but not a concrete experience claim.

## 13. Media contribution rule

Photography/videography/content creation is a reusable **project-specific value proposition**, not automatic eligibility.

Use it when the call benefits from documentation, communication or dissemination:

- organiser approval;
- informed consent and privacy;
- safeguarding for minors or vulnerable/sensitive contexts;
- local law and explicit permission for drone use;
- full programme participation remains primary;
- no fixed deliverable quantities before agreement.

The applicant may offer useful visual assets free to participating organisations, but never as a substitute for the actual project duties.

## 14. Submission integrity and automation boundary

`SUBMITTED` requires the correct authorised channel plus:

- human review/ownership;
- legitimate authentication;
- submission timestamp;
- receipt/capture or explicit authoritative confirmation;
- CRM and Execution_Log update.

Current connectors support factual prefill packets, evidence mapping, drafts where allowed, QA and operational emails. They do **not** provide general-purpose typing/submission for arbitrary authenticated forms, CAPTCHA or legally meaningful declarations.

The human owner performs authentication, applicant-owned wording when required, final declarations, submit and receipt capture.

Missing receipt is not proof of submission and not proof of non-submission.

## 15. Provider access

- SALTO calendar: public listing/detail and legitimate MySALTO routes.
- SALTO trainer calls: public calls only; never bypass login/access controls.
- EYP/ESC and Eurodesk: supported public/search/browser/API routes.
- Social/Telegram: discovery only until corroborated.
- Organisation calls: verify current source, country route, deadline and authorised form.

A zero-result scraper is not successful coverage.

## 16. Source completeness semantics

Use four separate states:

- `CAPTURED`: raw link/text preserved with provenance.
- `CANONICAL`: deduplicated into one opportunity.
- `VERIFIED`: authoritative facts checked.
- `APPLICATION_READY`: public/private/policy gates pass and assets are ready.

Never describe captured Telegram URLs as fully processed opportunities.

Current supplied-source audit:

- project compilation: 21/21 represented canonically;
- Telegram document: 61 raw links, 60 unique, one duplicate, 60 content-unresolved.

Live T0/T1 applications continue while Telegram extraction runs in parallel.

## 17. Dedupe

Prefer:

1. provider/call ID;
2. provider post ID;
3. canonical source/application URL;
4. `(host, normalised title, start date, country)`.

Raw duplicates remain provenance nodes; only one canonical application is submitted.

## 18. Current canonical checkpoint

Reconciled after the 2026-08-29 private-gate intake:

- opportunities: **160**;
- application/dossier rows: **148**;
- Source Inbox nodes: **93**;
- organisations: **17**;
- execution events: **34**;
- outcomes: **4**;
- receipts: **0**;
- TOY references: **0**;
- private `Autofill_Profile`: live;
- private application modules: **15**.

Private broad gates now pass for Spain residence, current 18–30 age, September–November availability, travel-cost advance and broad accommodation/logistics tolerance. Exact values stay private.

`Guardians of Triglav` is `CLOSED_NOT_SUBMITTED` by direct human confirmation, not rejection.

Both YUPI calls have private gates passed and are prepared as mutually exclusive options. Final applicant-owned assets, submission and receipts remain.

## 19. Current bottlenecks

1. Create a functional European Youth Portal / ESC account and store the Participant Reference Number privately.
2. Execute live T0/T1 rows in deadline order.
3. Finalise and submit both YUPI applications.
4. Resolve Step Into Paralympics external target-profile conflict.
5. Extract and verify all 60 unique unresolved Telegram posts.
6. Capture forms, infopacks and AI policies for the remaining mass queue.
7. Store the first receipt-backed submissions.

## 20. Execution order

`T0 today/tomorrow → T1 2–3 days/ASAP → T2 4–7 days → T3 8–14 days → T4 later/rolling`.

Inside each bucket:

1. verified short form;
2. infopack-ready route;
3. source/form extraction;
4. external clarification;
5. complex assets.

Continue until each non-terminal row ends in receipt-backed submission, a sourced objective terminal state or explicit waiting external evidence.

## 21. Release protocol

Before closing a wave:

1. reconcile Drive CRM counts;
2. update `goal-state.json`, README, AGENTS and checkpoint;
3. retire obsolete overrides;
4. run local tests when the repo is available;
5. open PR;
6. observe exact-head CI;
7. merge only after green;
8. persist Drive release bundle and handoff;
9. record GitHub/Drive IDs in CRM Execution_Log.

Do not claim any step that did not occur.
