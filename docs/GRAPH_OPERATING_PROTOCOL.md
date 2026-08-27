# Graph Operating Protocol — Waves × Agents × Mandatory Gates

This protocol makes every execution path explicit. No agent may choose an arbitrary next step: the current node state, verified evidence and transition guards determine the next allowed operation.

## 1. Core invariant

Every actionable object is a graph node with:

- `node_id`
- `node_type`
- `state`
- `source_refs[]`
- `evidence_refs[]`
- `verification_debt[]`
- `decision_code`
- `decision_inputs`
- `rule_version`
- `next_required_transition`
- `assigned_agent_role`
- `updated_at`

Every material decision emits an append-only event. Projections may be rebuilt; history may not be silently rewritten.

## 2. Canonical execution path

```text
SOURCE_DISCOVERED
  -> INGESTED
  -> DEDUPED
  -> SOURCE_VERIFIED
  -> ELIGIBILITY_EVALUATED
  -> INFOPACK_ANALYSED
  -> FIT_SCORED
  -> EXECUTION_PRIORITISED
  -> APPLICATION_POLICY_RESOLVED
  -> EVIDENCE_MAPPED
  -> DOSSIER_READY
  -> HUMAN_REVIEW
  -> SUBMITTED
  -> OUTCOME_RECORDED
  -> LEARNING_EVENT
```

Alternative terminal states:

`DUPLICATE_MERGED` · `BLOCKED_INELIGIBLE` · `EXPIRED` · `CLOSED` · `WITHDRAWN` · `HUMAN_WRITE_REQUIRED`.

## 3. Transition guards

| Current state | Required evidence | Next state | Agent |
|---|---|---|---|
| DISCOVERED | source URL/provider key | INGESTED | Scout |
| INGESTED | stable identity key | DEDUPED or DUPLICATE_MERGED | Deduper |
| DEDUPED | original page/infopack provenance | SOURCE_VERIFIED or VERIFICATION_DEBT | Verifier |
| SOURCE_VERIFIED | hard-gate inputs | ELIGIBILITY_EVALUATED | Eligibility Engine |
| ELIGIBILITY_EVALUATED | no confirmed FAIL | INFOPACK_ANALYSED | Infopack Analyst |
| INFOPACK_ANALYSED | criteria + funding + logistics + AI policy signals | FIT_SCORED | Ranker |
| FIT_SCORED | score components | EXECUTION_PRIORITISED | Ranker |
| EXECUTION_PRIORITISED | application/form policy | APPLICATION_POLICY_RESOLVED | Policy Guard |
| APPLICATION_POLICY_RESOLVED | verified applicant evidence | EVIDENCE_MAPPED | Evidence Retriever |
| EVIDENCE_MAPPED | no unsupported external claim | DOSSIER_READY | Application Strategist |
| DOSSIER_READY | human approval | HUMAN_REVIEW / SUBMITTED | Human owner |
| SUBMITTED | submission receipt | OUTCOME_RECORDED | Outcome Analyst |

No transition may skip a required predecessor.

## 4. Decision codes

Every decision uses an explicit code rather than free-form intuition:

- `DUPLICATE_PROVIDER_KEY`
- `DUPLICATE_CANONICAL_URL`
- `BLOCK_COUNTRY`
- `BLOCK_AGE`
- `BLOCK_DEADLINE`
- `BLOCK_ROLE_REQUIREMENT`
- `BLOCK_PREVIOUS_PARTICIPATION`
- `VERIFY_CONFLICTING_DATE`
- `VERIFY_UNKNOWN_COUNTRY`
- `VERIFY_UNKNOWN_AI_POLICY`
- `VERIFY_PRIVATE_EVIDENCE`
- `APPLY_HIGH_FIT_HIGH_URGENCY`
- `TRACK_HIGH_FIT_LOW_URGENCY`
- `ARCHIVE_CLOSED`
- `HUMAN_WRITE_AI_PROHIBITED`

A new decision code requires documentation + regression coverage if it changes deterministic behavior.

## 5. Score separation

Never collapse eligibility, fit and urgency into one opaque number.

### Hard eligibility

`PASS | FAIL | UNKNOWN`

A confirmed `FAIL` blocks submission regardless of fit.

### Fit Score 0–100

How strategically attractive the opportunity is independent of deadline:

- thematic/personal fit
- contribution fit
- learning value
- role/career leverage
- funding/logistics value

### Media Value 0–100

How much the applicant's professional photo/video capability can legitimately improve project dissemination/documentation. This is a secondary contribution, not a substitute for project motivation.

### Trainer Leverage 0–100

How strongly the activity advances facilitator/trainer competence, valid references, organiser relationships or paid-trainer positioning.

### Deadline Urgency 0–100

Pure time pressure. It changes execution order, never thematic fit.

### Execution Priority

Used only to decide what the system works on next. A high-fit node with unresolved evidence can rank highly for **verification** without being eligible for **submission**.

## 6. Wave ownership

### Wave 2B — Ingestion + dedupe
Owner: Scout/Deduper.

Outputs: provider keys, canonical URLs, content hashes, duplicate merges, raw-source provenance.

### Wave 2C — Verification
Owner: Verifier/Infopack Analyst.

Outputs: authoritative dates, country/age/role requirements, funding, organisers, AI policy, conflicts and confidence.

### Wave 3 — Private evidence graph
Owner: Evidence Retriever.

Outputs: applicant facts, proof objects, portfolio/references, availability, language evidence, media contribution evidence, trainer evidence.

### Wave 4 — Application intelligence
Owner: Application Strategist + Policy Guard.

Outputs: criterion -> evidence -> contribution -> learning goal -> multiplier plan, then human review. No final AI-authored answers if forbidden.

### Wave 5 — Trainer path
Owner: Trainer Career Agent.

Outputs: qualifying reference ledger, methods portfolio, TOY readiness, paid-call pipeline, organiser relationship graph.

### Wave 6 — Outcomes
Owner: Outcome Analyst.

Outputs: accepted/waitlisted/rejected/no-response events, feedback, source/organisation priors and calibrated scoring.

## 7. Conflict protocol

Conflicting evidence never resolves by majority vote or LLM preference.

1. Preserve both claims.
2. Rank sources by authority and freshness.
3. Create `VERIFICATION_DEBT`.
4. Block submission if the conflict affects eligibility, deadline, dates, fee or application policy.
5. Resolve only with a newer/higher-authority source or direct organiser confirmation.

## 8. Anti-duplicate protocol

Identity hierarchy:

1. provider project/call ID;
2. provider/channel post ID;
3. canonical application/opportunity URL;
4. fingerprint `(host, normalised title, start date, country)`.

Raw duplicates remain as provenance nodes but only one canonical opportunity may be promoted.

## 9. Completion contract

An application node may enter `READY_TO_SUBMIT` only when:

- canonical opportunity identity resolved;
- source verified and current;
- hard eligibility is PASS;
- deadline is open;
- infopack/form requirements captured;
- AI policy resolved;
- mandatory documents ready;
- every external claim maps to evidence;
- human owner has reviewed the final submission.
