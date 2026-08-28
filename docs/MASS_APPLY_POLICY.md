# Mass Apply & Infopack Factory Policy

Status: **ACTIVE operational policy from 2026-08-29**.

This policy changes execution selection, not truth or safety standards.

## 1. Mandate

Discover, ingest, verify, prepare and submit every live opportunity that has a legitimate route for a person based in Spain, provided that:

- the deadline has not passed;
- the call is still open or genuinely rolling;
- Spain or a Spanish sending/support route is eligible;
- no mandatory requirement has a confirmed `FAIL`;
- the application is not a duplicate;
- the application policy, including AI rules, is respected;
- the applicant completes the required human-owned review, authentication and consent steps.

Strategic fit, topic, duration, option cost and calendar overlap do **not** exclude an application. They order work or inform the later acceptance decision.

## 2. North Star

`valid receipt-backed applications per live Spain-compatible opportunity`

Coverage is maximised subject to zero known false-pass, fabricated claims, duplicate submissions, AI-policy violations and guessed receipt states.

## 3. Canonical pipeline

```text
DISCOVERED
→ INGESTED
→ DEDUPED
→ SOURCE_VERIFIED
→ SPAIN_ROUTE_VERIFIED
→ DEADLINE_VERIFIED
→ ROLE_PROFILE_EXTRACTED
→ INFOPACK_CAPTURED
→ INFOPACK_ANALYSED
→ FORM_CAPTURED
→ APPLICATION_POLICY_RESOLVED
→ EVIDENCE_MAPPED
→ ANSWER_DRAFTED
→ HUMAN_OWNED_FINAL_TEXT
→ QA
→ SUBMITTED
→ RECEIPT_STORED
→ OUTCOME_RECORDED
→ ACCEPTANCE_DECISION
```

`UNKNOWN` is work to resolve. It is not silently converted to either `PASS` or `FAIL`.

## 4. Terminal exclusion reasons

Only objective terminal states exclude a submission:

- `DEADLINE_PASSED`
- `SPAIN_NOT_ELIGIBLE`
- `HARD_REQUIREMENT_FAIL`
- `CALL_CLOSED`
- `APPLICATION_ROUTE_INVALID`
- `DUPLICATE_SUBMISSION`

A low score, low thematic fit, long duration, possible calendar conflict or low perceived acceptance probability is not a terminal exclusion reason.

## 5. Priority semantics

Priority is a scheduling field only.

Deadline buckets:

- `T0`: deadline today or tomorrow;
- `T1`: 2–3 days;
- `T2`: 4–7 days;
- `T3`: 8–14 days;
- `T4`: later, rolling or deadline still being verified.

Inside a bucket, process routes with short verified forms first, then infopack-ready routes, then calls requiring external clarification or complex assets.

## 6. Infopack factory contract

Each opportunity dossier must capture:

### Identity and timing

- canonical opportunity ID;
- title, programme, host and Spanish sending/support route;
- country, city and exact activity/travel dates;
- deadline, time and time zone;
- official source, infopack and authorised form URL.

### Eligibility

- eligible countries/residence/nationality;
- age;
- mandatory and preferred profiles;
- mandatory experience, role, affiliation or organisational mandate;
- language;
- prior-participation constraints;
- ESC/EVS cumulative participation limits where applicable;
- availability and other private human gates.

### Funding and conditions

- accommodation, meals and pocket money;
- travel reimbursement/distance band;
- fee;
- insurance, visa and accessibility provisions;
- trainer/facilitator fee, daily rate and invoicing/tax conditions when applicable.

### Programme and outputs

- objectives, topics, methodology and activities;
- required outputs and dissemination;
- safeguarding, consent, privacy and media restrictions;
- conditions for legitimate photo/video/storytelling contribution.

### Application

- exact questions and character limits;
- required CV, portfolio, video, letter or certificates;
- application policy and AI classification;
- authorised channel;
- expected confirmation or receipt.

## 7. Application dossier contract

Every application node must contain:

1. opportunity brief;
2. `PASS | FAIL | UNKNOWN` gate matrix;
3. `criterion → evidence_id → allowed claim` map;
4. exact question/answer matrix;
5. adapted contribution module;
6. credible learning goals;
7. realistic dissemination plan;
8. human-owned final assets;
9. adversarial QA;
10. submission receipt.

Reusable modules are evidence components, not copy-paste final answers.

## 8. Integrity invariants

- Never fabricate youth-work, NFE, facilitation, trainer, language, degree, student, organisation, availability, accessibility or fewer-opportunities claims.
- Historical Erasmus+/Youth Staff participation does not automatically prove current youth-work context or trainer responsibility.
- Do not impersonate an experienced trainer when the supported lane is participant, contributor or emerging facilitator.
- `AI_UNKNOWN` blocks AI-generated final applicant text, but not source extraction, evidence organisation or neutral form mapping.
- `AI_FINAL_TEXT_PROHIBITED` requires human-authored final answers.
- Do not mark `SUBMITTED` without a verifiable receipt or explicit human confirmation tied to the correct call.
- Do not decide between overlapping opportunities before acceptance. Resolve conflicts at `ACCEPTANCE_DECISION`.

## 9. Source coverage

The complete queue draws from:

- SALTO European Training Calendar;
- SALTO Calls for Trainers;
- European Youth Portal / European Solidarity Corps;
- Eurodesk and Eurodesk Spain;
- host and sending organisations;
- official infopacks and forms;
- verified organiser replies;
- discovery-only social/Telegram records promoted only after stronger verification.

## 10. Operational projection

Private Drive CRM is authoritative for opportunity/application rows, private gates, evidence, answers and receipts. Todoist is an execution projection. Public GitHub stores this policy, schemas, aggregate checkpoints and executable rules only.
