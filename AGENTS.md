# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session contract for multi-agent control-plane v1. Read in order:
> `goal.md` → `goal-state.json` → this file → `ARCHITECTURE.md` → `docs/MULTI_AGENT_CONTROL_PLANE.md` → `docs/GLOBAL_MOBILITY_AND_INCOME_STRATEGY.md` → `docs/MASS_APPLY_POLICY.md` → `docs/GRAPH_OPERATING_PROTOCOL.md` → current checkpoint → private Drive context/events/leases.

## 1. Mission lock

Discover, register, verify, prepare and execute **every legitimate live Spain-compatible opportunity** across:

- Erasmus+ Youth Exchanges and organisation calls;
- European Solidarity Corps and Humanitarian Aid Volunteering;
- Eurodesk and Eurodyssey/professional mobility;
- SALTO training and paid trainer/facilitator/expert calls;
- paid monitor, camp/activity leader and project roles;
- international communication/media/digital roles;
- reputable global humanitarian, youth and adjacent professional sources.

Portfolio objective: enable Roberto to expand globally beyond Murcia while maintaining or delegating online work.

`APPLY EVERYTHING VIABLE` remains mandatory. Priority orders execution only.

## 2. North-star hierarchy

Coverage:

`receipt-backed applications / live Spain-compatible opportunities`

Economic ordering:

`verified net cash / verified work hour → verified net cash / committed hour → total net cash`

Career:

`subject expertise → current youth-facing delivery → co-facilitation → references → paid international trainer/facilitator work`

All are constrained by zero known hard-SLO violations.

## 3. Strategic scheduling

After all hard gates, use the versioned priority vector:

- paid cash-rate potential: 35%;
- payment and contract certainty: 15%;
- total net cash: 10%;
- trainer/facilitator trajectory: 12%;
- outside-Europe/globality: 10%;
- rarity/scarcity: 8%;
- remote-work compatibility: 5%;
- exceptional experience/network value: 5%.

Preferred roles: `TRAINER → FACILITATOR → PAID_MONITOR/CAMP_LEADER → PROJECT_COORDINATOR → PAID_MEDIA/COMMUNICATIONS → FUNDED_PARTICIPANT`.

This order never fabricates role eligibility. Duration has no global hard ceiling. Shorter work is preferred only when verified yield is better.

## 4. Truth hierarchy

1. Current original official page, infopack, authorised form, organiser confirmation, contract or receipt.
2. Private Drive CRM event bus and evidence graph.
3. GitHub versioned policy, schemas, code and aggregate state.
4. Portable snapshots.
5. Todoist/interface projections.

`UNKNOWN` is first-class verification debt. The latest edit is not automatically authoritative.

## 5. Source topology and privacy

- GitHub is public: code, schemas, public policies/facts, tests and aggregate state only.
- Drive is private: applicant data/evidence, answers, sessions, events, leases, forms, restricted infopacks, dossiers and receipts.
- Gmail/provider portals are communication/submission evidence channels.
- Todoist is an execution projection only.

Never place phone, DOB, addresses, identity numbers, health data, emergency contacts, private references, applicant answers or restricted files in public GitHub.

## 6. Mandatory multi-agent cold start

Before any canonical write, every chat/agent must:

1. read the current GitHub contract and checkpoint;
2. read private `Context_Registry`;
3. inspect `Agent_Sessions` and unexpired `Work_Leases`;
4. read `Agent_Event_Bus` after the context cursor;
5. reconcile the target projection;
6. register a unique Session ID;
7. emit `SESSION_STARTED`;
8. acquire the smallest safe lease;
9. execute only transitions within that lease.

Unregistered sessions are read-only.

Current context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`.

## 7. Sessions, leases and events

Session IDs follow:

`SES-<PROJECT>-<PLATFORM>-<YYYYMMDDTHHMMSS>-<NN>`

Stable Agent IDs identify roles, not conversations.

Default lease TTL is 120 minutes. Target heartbeat is 15 minutes while writing. Another session's unexpired lease blocks mutation. Expired/released takeover requires an event.

Every material mutation emits an append-only event containing project/context/session/agent/entity identity, state before/after, source, causal parent, correlation, lease, writer version and idempotency key.

Idempotency:

`SHA-256(project_id | entity_type | entity_id | operation | authoritative_source_version)`

Same operation + same source version = no-op replay.

## 8. Consistency limitations

The current Drive-based bus provides near-real-time shared state through mandatory read-before-write. It is not a push broker: an already-running chat does not receive updates automatically. Every material operation must refresh events and leases immediately before mutation.

A projection changed without an event, or an event missing from required projections, creates `PROJECTION_DIVERGENCE` and blocks wave closure.

## 9. Apply-everything contract

Every non-duplicate call enters CRM when Spain is listed, a Spanish route exists, or that route remains plausibly verifiable and the deadline is not proven closed.

Only objective terminal reasons remove a call:

`DEADLINE_PASSED · SPAIN_NOT_ELIGIBLE · HARD_REQUIREMENT_FAIL · CALL_CLOSED · APPLICATION_ROUTE_INVALID · DUPLICATE_SUBMISSION`

Low score, duration, cost, overlap, destination or predicted acceptance never terminate a viable application.

## 10. Mandatory graph

`DISCOVERED → INGESTED → DEDUPED → SOURCE_VERIFIED → SPAIN_ROUTE_VERIFIED → DEADLINE_VERIFIED → ROLE_PROFILE_EXTRACTED → INFOPACK_CAPTURED → INFOPACK_ANALYSED → FORM_CAPTURED → APPLICATION_POLICY_RESOLVED → EVIDENCE_MAPPED → ANSWER_DRAFTED → HUMAN_OWNED_FINAL_TEXT → QA → SUBMITTED → RECEIPT_STORED → OUTCOME_RECORDED → ACCEPTANCE_DECISION`

No arbitrary next state and no skipped gate.

## 11. Hard gates

Gate output: `PASS | FAIL | UNKNOWN`.

Mandatory checks include:

- source/current status and deadline/time zone;
- Spain/residence/nationality and age;
- exact dates/availability and travel feasibility;
- role/profile, language, degree, licence or certification;
- affiliation/mandate/team composition;
- previous participation and ESC/EVS limits;
- sending/support organisation;
- safety, visa, insurance, legal/tax and remote-work restrictions when relevant;
- authorised form/channel and duplicate state;
- AI/application policy;
- final human declarations and receipt path.

Urgency accelerates verification; it never bypasses it.

## 12. Temporal and role evidence

Historical youth-sector experience, current youth-work context, delivered facilitation and trainer qualification are separate facts.

Verified private aggregate context:

- two completed Erasmus+ KA1 Youth Staff professional-development mobilities;
- one completed Erasmus+ Youth Exchange;
- current youth-work context: `UNKNOWN`;
- TOY-qualifying trainer references: `0`.

Attendance never implies group leadership, facilitation or trainer responsibility. Exact roles remain in the private `Profile_Interview` queue until evidenced.

## 13. Ask-once profile contract

`Autofill_Profile` stores verified reusable facts. `Profile_Interview` stores unresolved questions.

Agents must:

- search both before asking Roberto anything;
- ask only unresolved and call-relevant questions;
- update the canonical question immediately after an answer;
- record evidence strength and external-use rule;
- collect minimum necessary sensitive data;
- never infer degree, CEFR, youth work, certifications, residence duration, emergency/health facts or commercial authority.

## 14. AI/application policy

Classify each route:

`AI_ALLOWED | AI_ASSIST_ONLY | AI_FINAL_TEXT_PROHIBITED | AI_UNKNOWN`

- `AI_UNKNOWN`: source extraction/evidence mapping may continue; final AI prose is blocked unless independently authored by the applicant.
- `AI_ASSIST_ONLY`: structure, evidence, gap analysis and QA are allowed; final wording follows organiser guidance and remains applicant-owned.
- `AI_FINAL_TEXT_PROHIBITED`: facts/outline only; no final-answer drafting or rewriting.
- Absence of a visible prohibition is not permission.

## 15. Infopack and form factory

For each canonical opportunity:

1. preserve original source/infopack;
2. extract eligibility, role, dates, location, funding, accommodation, travel, fees, language and conditions;
3. capture exact current form, questions and character limits;
4. resolve AI policy;
5. map questions to private evidence;
6. create a project-specific answer pack;
7. create/update required CV, letter, portfolio, video script or attachments;
8. route missing facts to `Profile_Interview`;
9. obtain human-owned final wording and declarations;
10. submit through the authorised route;
11. store a durable receipt.

Infopacks are analysed; forms and attached templates are completed.

## 16. Personalisation and claims

Every external claim follows:

`criterion → verified evidence → allowed claim → specific contribution → credible learning → proportionate multiplier`

Never fabricate current youth work, NFE delivery, trainer experience, degree, CEFR, student status, organisation mandate, availability, disability, fewer-opportunities status, safeguarding, practical experience or other sensitive circumstances.

## 17. Media contribution

Photography/video/content may be offered only when relevant and subject to organiser approval, consent, privacy, safeguarding, local law and full participation. Never promise recording involving minors, vulnerable groups, detainees or sensitive settings without explicit authorisation.

## 18. Opportunity economics

Cash and non-cash funded value are separate.

Net cash requires verified gross compensation and every compulsory cost. Net/hour additionally requires verified actual working hours. Unknown inputs remain `ECONOMICS_VERIFICATION_DEBT`.

Do not call pocket money, accommodation, meals, travel reimbursement, insurance or training a salary.

For paid roles capture:

- currency, amount and fee unit;
- working days/hours and preparation;
- total commitment/travel days;
- payment schedule and legal payer;
- fee inclusions/exclusions;
- programme, visa, insurance, travel and tax costs;
- cancellation/payment-risk terms;
- remote-work compatibility.

Economic scores order execution; they never determine eligibility.

## 19. Global source coverage

Use source tiers:

- T1: original official provider/employer;
- T2: established network/programme platform;
- T3: aggregator/social/user-supplied discovery.

T3 may discover but does not authorise when an original source exists.

Operational coverage requires every active source scanned inside SLA, every item captured, deterministic dedupe, recursive original-source resolution, and explicit unresolved/inaccessible frontier counts.

Never call a zero-result or blocked scraper complete.

## 20. Trainer progression

`L0 self-description → L1 verified affiliation → L2 delivered youth activity → L3 external reference/repeated delivery → L4 qualifying international trainer reference`

Build, do not claim. Historical participation supports programme literacy only.

## 21. Submission boundary

`SUBMITTED` requires:

- correct authorised channel;
- all public/private/policy gates pass;
- human review/ownership;
- legitimate authentication;
- timestamp;
- receipt/capture or authoritative confirmation;
- CRM/event/log update.

Connectors may discover, read, prepare, prefill facts, create documents, draft/send authorised email routes and update systems. Arbitrary authenticated forms, CAPTCHA, MySALTO/EYP/Eurodyssey declarations require Roberto's legitimate final interaction unless an explicit connected action supports submission.

The handoff must be `READY_FOR_HUMAN_SUBMIT` with exact fields/assets, not “write this yourself”.

## 22. Todoist

Every active task must map to a graph transition and include entity ID, state, next transition, deadline/time zone, owner, Drive/form ref, blockers and receipt condition.

Completing a Todoist task without an event and canonical transition is invalid.

## 23. Dedupe and conflicts

Identity order:

1. provider/call ID;
2. provider post ID;
3. canonical application URL;
4. `(host, normalised title, start date, country)`.

Raw duplicates remain provenance. Conflicting authoritative facts are preserved and routed to verification; never majority-vote them.

## 24. Handoff and release

Before ending a session:

1. refresh target/events;
2. emit final domain events;
3. reconcile Drive/GitHub/Todoist projections;
4. record tests and CI actually observed;
5. set exactly one next transition per active node;
6. update session output/handoff;
7. emit `HANDOFF_READY` and `SESSION_COMPLETED`;
8. release every lease.

Historical sessions are backfilled only from evidence. Unknown identity stays unknown.

## 25. Current checkpoint

W9 baseline remains:

- 167 opportunities;
- 156 application/dossier and mass-apply rows;
- 96 Source Inbox nodes;
- 22 organisations;
- 52 execution-log events;
- 35 urgent rows classified;
- 60 unique Telegram posts unresolved;
- 0 receipts;
- 0 TOY references.

Control-plane v1 adds eight private tables, one canonical global context and the first registered session without changing the application baseline or claiming submissions.

## 26. Immediate bottlenecks

1. Functional EYP/ESC account and private PRN.
2. MySALTO access/form capture.
3. Applicant-owned YUPI assets and receipt-backed submissions.
4. P0 profile intake: exact Erasmus roles/activities, delivered youth work, education, professional timeline, portfolio links, invoicing and remote-work constraints.
5. Economics verification for live paid roles.
6. T1 scans for paid trainers, humanitarian/outside-EU, paid monitors/camps and professional mobility.
7. Resolve all 60 Telegram posts.
8. Keep every writer sessioned, leased, idempotent and reconciled.

## 27. Release protocol

Before merge/release:

1. re-read main and active leases;
2. update policy/state/checkpoint;
3. run focused local tests when possible;
4. open PR;
5. observe exact-head CI;
6. merge only green;
7. observe main push CI;
8. update private event/session/lease state and Todoist;
9. never claim an operation that did not occur.
