# UE-Xchanges-OS — AGENTS.md

> Canonical cross-session contract for every UE-Xchanges-OS agent/writer.
>
> Mandatory cold-start router: `agent_context/bootstrap_manifest.json`.
>
> Stable read order starts with:
> `CURRENT_GITHUB_MAIN_SHA` → `goal.md` → this file → `MEMORY.md` → `agent_context/bootstrap_manifest.json` → `LIVE-STATE-OVERRIDE.json` → `STATE.md` → `HANDOFF.md` → required `agent_context/**` navigation → current checkpoint → private Drive context/events/leases/RuntimeGraph cursors.
>
> A compliant writer must emit `BOOTSTRAP_CONTEXT_LOADED` before acquiring a write lease.

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
3. Current GitHub versioned policy, schemas, code and aggregate/recovery state.
4. RuntimeGraph and portable derived snapshots.
5. `agent_context/**`, `MEMORY.md`, Todoist and interface projections.
6. Chat memory.

`UNKNOWN` is first-class verification debt. The latest edit is not automatically authoritative.

`MEMORY.md` is slow-changing semantic memory, **not live state**. `agent_context/**` is derived zero-context navigation, **not canonical domain truth**.

## 5. Source topology and privacy

- GitHub is public: code, schemas, public policies/facts, tests and aggregate/recovery state only.
- Drive is private: applicant data/evidence, answers, sessions, events, leases, forms, restricted infopacks, dossiers and receipts.
- Gmail/provider portals are communication/submission evidence channels.
- Todoist is an execution projection only.

Never place phone, DOB, addresses, identity numbers, health data, emergency contacts, private references, applicant answers, receipt-private content, secrets/tokens or restricted files in public GitHub.

## 6. Mandatory multi-agent cold start

The canonical machine-readable contract is `agent_context/bootstrap_manifest.json`.

Before **any canonical or versioned write**, every chat/agent must:

1. read current GitHub `main` and record the SHA;
2. read `goal.md`, `AGENTS.md`, `MEMORY.md` and `agent_context/bootstrap_manifest.json`;
3. read the required public recovery/context files declared by the manifest, including current `STATE.md`, `HANDOFF.md` and required `agent_context/**` navigation;
4. read private `Context_Registry`;
5. inspect `Agent_Sessions` and **currently unexpired** `Work_Leases`;
6. read `Agent_Event_Bus` after the current context/event watermark;
7. read relevant RuntimeGraph Command Center/cursors/dead letters and fresh Gmail/official evidence when the intended action depends on external state;
8. register a **new** unique Session ID;
9. emit `SESSION_STARTED`;
10. emit `BOOTSTRAP_CONTEXT_LOADED` with manifest version, observed main SHA, context ID, public read-set refs/hash, private event watermark, lease-scan timestamp, agent ID and session ID;
11. refresh unexpired leases + Event Bus tail immediately before lease acquisition;
12. reconcile the target projection;
13. acquire the smallest safe lease;
14. execute only transitions within that lease.

`BOOTSTRAP_CONTEXT_LOADED` must occur **before** `LEASE_ACQUIRED` for compliant writers.

Unregistered sessions are read-only. A registered session that has not completed the bootstrap handshake is also read-only.

Never reuse a historical Session ID for writes.

Current global context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`.

## 6A. Memory and context contract

`MEMORY.md` stores only slow-changing semantic memory:

- mission/policy invariants;
- architecture laws;
- recurring failure modes;
- durable evidence rules;
- long-lived operational decisions.

Do **not** store volatile counts, frontier membership, deadline-sensitive states, current lease ownership, current receipt IDs or applicant-private values in `MEMORY.md`.

Volatile state belongs in authoritative/private systems and watermarked recovery artifacts (`STATE.md`, `HANDOFF.md`, current checkpoint, `LIVE-STATE-OVERRIDE.json`, Drive and `agent_context/**`).

An already-running session does not automatically learn a repository update. Before every material mutation it must refresh Event Bus + leases. If bootstrap contracts (`AGENTS.md`, `MEMORY.md`, manifest) changed materially during a long session, refresh them before continuing significant work.

## 7. Sessions, leases and events

Session IDs follow:

`SES-<PROJECT>-<PLATFORM>-<YYYYMMDDTHHMMSS>-<NN>`

Stable Agent IDs identify roles, not conversations.

Default lease TTL is 120 minutes. Target heartbeat is 15 minutes while writing. Another session's **unexpired, overlapping** lease blocks mutation. Expired/released takeover requires reconciliation/event evidence.

A stale row that still contains the word `ACTIVE` is not a perpetual lock: reconcile status, expiry, heartbeat and later release/takeover events.

Every material mutation emits an append-only event containing project/context/session/agent/entity identity, state before/after, source, causal parent, correlation, lease, writer version and idempotency key.

Idempotency:

`SHA-256(project_id | entity_type | entity_id | operation | authoritative_source_version)`

Same operation + same source version = no-op replay.

## 8. Consistency limitations

The current Drive-based bus provides near-real-time shared state through mandatory read-before-write. It is not a push broker: an already-running chat does not receive updates automatically. Every material operation must refresh events and leases immediately before mutation.

A projection changed without an event, or an event missing from required projections, creates `PROJECTION_DIVERGENCE` and blocks wave closure.

GitHub is authoritative for GitHub code/PR/CI state. Never claim a merge or green CI because a projection says it happened; observe GitHub itself.

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

Verified private aggregate context may exist in Drive, but public/versioned documents must not inflate it into unproven role claims.

Attendance never implies group leadership, facilitation or trainer responsibility. Exact roles remain in private evidence/Profile Interview until evidenced.

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
9. obtain human-owned final wording and declarations where required;
10. submit only through the authorised route and current capability policy;
11. store a durable receipt.

Infopacks are analysed; forms and attached templates are completed where authorised capability exists.

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

## 21. Submission and browser capability boundary

`SUBMITTED` requires:

- correct authorised channel;
- all public/private/policy gates pass;
- required human review/ownership;
- legitimate authentication;
- timestamp;
- durable receipt/capture or authoritative confirmation;
- CRM/event/log update.

`SubmissionAttempt != SubmissionReceipt`. Clicking a button, seeing a transient page, completing Todoist, preparing a form, sending an eligibility query or holding a browser session does not establish submission truth.

The Form Execution Gateway may expose progressively stronger capabilities, but each capability is independent. Authentication does not imply PREFILL permission. PREFILL does not imply Submit permission. A local HMAC capability is not a browser credential.

Current Form Gateway/Browser capability state must be read from **current code + current recovery artifacts**, not inferred from this stable contract or `MEMORY.md`.

Irreversible Submit remains blocked unless the current versioned capability contract explicitly enables it and all approval/attempt/receipt invariants pass. Payments remain separate from form execution.

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

1. refresh current main, target events and unexpired leases;
2. emit final domain/control events;
3. reconcile authoritative state and affected projections;
4. record tests, PRs, merge SHA and CI actually observed;
5. set exactly one next transition per active node;
6. persist durable semantic lessons in `MEMORY.md` only if they meet the memory-write policy;
7. update watermarked recovery/context artifacts when within lease;
8. update session output/handoff;
9. emit `HANDOFF_READY` when applicable and `SESSION_COMPLETED`;
10. release every lease.

Historical sessions are backfilled only from evidence. Unknown identity stays unknown.

## 25. Volatile-state contract

**Do not embed live counts, current frontier membership or transient opportunity states in this stable contract.**

For current scale/status read, in order:

1. current official/organiser/receipt evidence when entity-specific;
2. private Drive CRM + Event Bus;
3. current `LIVE-STATE-OVERRIDE.json`, `STATE.md`, `HANDOFF.md` and newest checkpoint;
4. watermarked `agent_context/context.md` / `progress.md` / `checkpoints.md` as navigation;
5. RuntimeGraph derived projections.

Any numeric snapshot in historical commits is historical only.

## 26. Immediate work selection

Do not maintain a static bottleneck list here.

Select work from live authority:

1. current Human/Agent/System Frontier;
2. deadlines and hard gates;
3. current source deltas / dead letters / receipts;
4. current Form Gateway capability ceiling;
5. current paid/global opportunity priorities;
6. unresolved profile/economics/source-access debt.

The current execution frontier belongs in Drive/RuntimeGraph/HANDOFF/agent_context with a timestamp, not in this stable contract.

## 27. Release protocol

Before merge/release:

1. re-read current main and unexpired leases;
2. confirm bootstrap handshake exists for the writer session;
3. update only files within lease;
4. run focused local tests when possible;
5. open PR;
6. observe exact-head CI;
7. verify merge-ref includes current base;
8. merge only green;
9. observe main push CI;
10. update private event/session/lease state and affected projections;
11. never claim an operation that did not occur.
