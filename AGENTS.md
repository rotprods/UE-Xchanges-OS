# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session contract for v0.8.0. Read:
> `goal.md` → `goal-state.json` → this file → `ARCHITECTURE.md` → `docs/MASS_APPLY_POLICY.md` → `docs/GRAPH_OPERATING_PROTOCOL.md` → current checkpoint.

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
- Drive stores applicant identity/evidence, private emails, original/restricted infopacks, answers, final assets and receipts.
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

- `AI_UNKNOWN`: source extraction and evidence mapping may continue; final AI-generated prose stays blocked.
- `AI_FINAL_TEXT_PROHIBITED`: Roberto writes final answers.
- Absence of a visible prohibition is not proof of permission.

## 9. Dossier contract

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

## 10. Personalisation and claims

Externally used claims follow:

`criterion → private evidence → allowed factual claim → specific contribution → credible learning → dissemination`

Never fabricate current youth-work, NFE, trainer/facilitator history, degree, CEFR, student status, organisation mandate, availability, residence, disability, fewer opportunities or any sensitive circumstance.

Media contribution is optional and secondary. It requires organiser approval, consent, privacy and safeguarding, especially with minors, prisons, detention, vulnerable groups or sensitive settings.

## 11. Submission integrity

`SUBMITTED` requires the correct authorised channel plus:

- human review/ownership;
- legitimate authentication;
- submission timestamp;
- receipt/capture or explicit authoritative confirmation;
- CRM and Execution_Log update.

Missing receipt is not proof of submission and not proof of non-submission.

## 12. Provider access

- SALTO calendar: public listing/detail and legitimate MySALTO routes.
- SALTO trainer calls: public calls only; never bypass login/access controls.
- EYP/ESC and Eurodesk: supported public/search/browser/API routes.
- Social/Telegram: discovery only until corroborated.
- Organisation calls: verify current source, country route, deadline and authorised form.

A zero-result scraper is not successful coverage.

## 13. Dedupe

Prefer:

1. provider/call ID;
2. provider post ID;
3. canonical source/application URL;
4. `(host, normalised title, start date, country)`.

Raw duplicates remain provenance nodes; only one canonical application is submitted.

## 14. Current canonical checkpoint

Reconciled at `2026-08-29T18:30:51+02:00`:

- opportunities: **159**;
- application/dossier rows: **148**;
- non-terminal: **140**;
- objective terminal: **8**;
- Source Inbox: **93**;
- organisations: **17**;
- execution events: **24**;
- outcomes: **4**;
- receipts: **0**;
- TOY references: **0**.

The live Drive CRM is authoritative. Temporary root overrides are retired; `goal-state.json` contains the canonical public projection.

## 15. Current bottlenecks

- 45/148 rows have an application route recorded.
- 16/148 rows have an infopack URL recorded.
- 2/148 rows have AI policy resolved.
- Human availability/residence/role/language/ESC-limit gates remain call-specific.
- Receipts remain 0.

## 16. Execution order

`T0 today/tomorrow → T1 2–3 days/ASAP → T2 4–7 days → T3 8–14 days → T4 later/rolling`.

Inside each bucket:

1. verified short form;
2. infopack-ready route;
3. source/form extraction;
4. external clarification;
5. complex assets.

Continue until each non-terminal row ends in receipt-backed submission or a sourced objective terminal state.

## 17. Release protocol

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
