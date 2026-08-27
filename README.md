# UE-Xchanges-OS

Evidence-first EU mobility intelligence, application and trainer-progression operating system for Erasmus+ Youth, European Solidarity Corps, youth-worker mobility and paid trainer/facilitator opportunities.

## North Star

**Maximise accepted, high-value, funded mobility/trainer opportunities per human application hour — with zero known eligibility false-passes, zero duplicate submissions, zero fabricated claims and zero known application-policy violations.**

## Mandatory operating graph

```text
DISCOVERED
→ INGESTED
→ DEDUPED
→ SOURCE_VERIFIED
→ ELIGIBILITY_EVALUATED
→ INFOPACK_ANALYSED
→ FIT_SCORED
→ EXECUTION_PRIORITISED
→ APPLICATION_POLICY_RESOLVED
→ EVIDENCE_MAPPED
→ DOSSIER_READY
→ HUMAN_REVIEW
→ SUBMITTED
→ OUTCOME_RECORDED
→ LEARNING_EVENT
```

Alternative terminal/routing states include `DUPLICATE_MERGED`, `BLOCKED_INELIGIBLE`, `EXPIRED`, `CLOSED`, `VERIFICATION_DEBT` and `HUMAN_WRITE_REQUIRED`.

No score or agent may skip a hard gate.

## Truth topology

- Original official source / infopack / form / organiser confirmation = authority for opportunity facts.
- GitHub = executable/versioned truth for code, schemas, policies, public knowledge and tests.
- Google Drive = private operational knowledge, applicant evidence, infopacks, dossiers and CRM.
- Todoist = execution projection only.
- `/git.local/UE-Xchanges-OS` = portable cold-start snapshot.
- Graph projections are rebuildable from evidence + append-only events.

## Safety / integrity locks

- Never invent youth-work history, volunteering, trainer experience, fewer-opportunities status, language level, qualifications or availability.
- `UNKNOWN` is never silently converted to `PASS`.
- If a call prohibits AI-written final answers, final-text generation is disabled.
- If AI policy is unknown, final submission text remains blocked until verified.
- Never score a known-ineligible opportunity as actionable.
- Never auto-submit a duplicate.
- Public repository contains no private applicant application text or sensitive profile data.

## Scoring v1.1

Eligibility is separate from desirability.

- **Fit Score** — thematic/contribution/learning/career/funding fit.
- **Media Value** — legitimate value of professional photography/video/storytelling for the project.
- **Trainer Leverage** — NFE competence, organiser network, facilitation/reference path.
- **Deadline Urgency** — time pressure only.
- **Execution Priority** — decides what the system works on next; it never overrides hard gates.

## Media contribution

Photography/videography is an optional secondary contribution, not an eligibility shortcut. When relevant and approved, the applicant may contribute professional project documentation/dissemination at no charge, subject to organiser approval, consent, privacy and safeguarding.

See `knowledge/MEDIA_CONTRIBUTION.md`.

## Trainer / credential path

Current verified TOY-qualifying references: **0**. Strategy: **BUILD, DO NOT CLAIM**.

```text
L0 self-description
→ L1 artifact
→ L2 delivery proof
→ L3 outcome/reference
→ L4 TOY-qualifying reference
```

See `knowledge/CREDENTIAL_ACQUISITION_GRAPH.md` and `knowledge/TRAINER_PATH.md`.

## Current live checkpoint — 2026-08-27

Private Drive CRM currently tracks:

- **23 canonical opportunity rows**;
- **21 opportunities** from the supplied opportunity document;
- **61 raw Telegram references / 60 unique provider keys / 1 exact duplicate**;
- **7 application nodes**;
- **9 organisation-intelligence nodes**;
- active P0/P1 dossiers for `Unleashing Creativity`, `CTRL+REAL`, `Game of Nature` and `Building With Our Hands`;
- eligibility-gated dossiers for Blue Book and Amani Pamoja.

Strongest current discovery nodes include:

- `Unleashing Creativity: From Lens to Life` — photography/Photovoice; Fit 100 / Media 100 / Trainer Leverage 98; role evidence unresolved.
- `CTRL+REAL — Manipulated Realities DECODED` — AI/deepfakes/media literacy; Fit 100 / Trainer Leverage 100; role evidence unresolved.

Known false positives have already been blocked rather than pushed into the application queue: country-ineligible, expired, closed and conflicting-date calls remain in history with explicit decision codes.

## Repository map

- `AGENTS.md` — canonical agent contract and resumable state.
- `goal.md` — `/define-goal` / North Star.
- `goal-state.json` — machine-readable checkpoint.
- `ARCHITECTURE.md` — boundaries and data flow.
- `docs/GRAPH_OPERATING_PROTOCOL.md` — mandatory transition guards / decision codes.
- `checkpoints/` — immutable wave snapshots.
- `knowledge/` — programme, selection, media, trainer and credential knowledge.
- `schemas/` — canonical contracts.
- `src/uexchanges/` — deterministic decision/discovery/routing core.
- `tests/` — regressions.
- `configs/` — source registry and scoring weights.

## Quality truth

Baseline merged PR #1:

- **27 tests passed, 0 failed**;
- GitHub Actions workflow run `33091677275`: **success**.

Changes added after PR #1 merge (graph protocol, scoring v1.1, workflow router, credential graph):

- **14 focused checks passed, 0 failed**;
- full remote CI is intentionally marked **pending PR #2** until a workflow run is actually observed.

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m uexchanges.cli demo
```

Read `AGENTS.md` before continuing any execution wave.
