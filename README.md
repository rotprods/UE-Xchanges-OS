# UE-Xchanges-OS

Evidence-first EU mobility, application-execution and trainer-progression operating system for Erasmus+ Youth, European Solidarity Corps, Eurodesk, non-SALTO participant calls and paid trainer/facilitator opportunities.

## Current operating mode

**APPLY EVERYTHING VIABLE.**

Every live opportunity with a legitimate Spain-compatible route enters the CRM and preparation factory. Priority orders execution; it does not remove a viable opportunity. Selection between accepted options happens after acceptance.

`UNKNOWN` is verification debt. A confirmed objective hard `FAIL` blocks only the affected call.

## North Star

`valid receipt-backed applications / live Spain-compatible opportunities`

Subject to zero known eligibility false-passes, duplicate submissions, fabricated claims, AI-policy violations, invented sensitive attributes and guessed submission/receipt states.

## Canonical pipeline

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

## Canonical state — 2026-08-29T18:30:51+02:00

Private Drive CRM:

- **159** canonical opportunity rows;
- **148** application/dossier nodes;
- **140** non-terminal queue rows;
- **8** objective terminal rows;
- **93** Source Inbox nodes;
- **17** organisation nodes;
- **24** execution events;
- **0** submission receipts;
- **0** verified TOY-qualifying trainer references.

Provider coverage:

- `SALTO_ETC`: 112
- `EYP_ESC`: 14
- `ORGANISATION_WATCH`: 8
- `EXISTING_CRM`: 7
- `EURODESK`: 6
- `NON_SALTO_ORG_CALL`: 1

## Truth topology

1. Current official page, original infopack, authorised form, organiser confirmation and submission receipt.
2. Private Drive CRM and evidence graph.
3. GitHub versioned code, schemas, policies and aggregate state.
4. Portable release snapshot.
5. Todoist/execution projections.

Temporary root overrides are retired in v0.8; `goal-state.json` is the single canonical public state projection.

## Integrity locks

- Never invent current youth-work, NFE delivery, trainer/facilitator experience, languages, degree, affiliation, availability, fewer-opportunities status or sensitive attributes.
- Historical Erasmus+/Youth Staff participation never auto-proves current youth-work context or trainer responsibility.
- `AI_UNKNOWN` blocks AI-generated final applicant prose, not neutral source extraction or evidence mapping.
- `AI_FINAL_TEXT_PROHIBITED` requires human-authored final text.
- Never mark `SUBMITTED` without a receipt or explicit authoritative confirmation tied to the correct call.
- Public GitHub contains no private applicant answers, identity documents, restricted infopacks or sensitive evidence.

## Repository map

- `goal.md` — current objective and policy.
- `goal-state.json` — machine-readable canonical checkpoint.
- `AGENTS.md` — cross-session execution contract.
- `docs/MASS_APPLY_POLICY.md` — apply-everything rules.
- `docs/GRAPH_OPERATING_PROTOCOL.md` — transition guards.
- `docs/DRIVE_MAP.md` — private workspace topology.
- `checkpoints/EXECUTION-WAVE-CURRENT.md` — current immutable checkpoint.
- `src/uexchanges/` — deterministic core.
- `schemas/` — contracts.
- `tests/` — regressions.

## Quality gate

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Exact-head GitHub Actions is mandatory before merge. A release does not claim CI until the corresponding workflow run succeeds.

Read `goal-state.json` and `AGENTS.md` before continuing.
