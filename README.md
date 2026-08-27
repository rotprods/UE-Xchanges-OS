# UE-Xchanges-OS

EU mobility intelligence + application operating system for Erasmus+ Youth, European Solidarity Corps, youth-worker mobility and paid trainer/facilitator opportunities.

## North Star

**Maximise accepted, high-value, funded mobility/trainer opportunities per hour of application effort — with zero eligibility errors, zero duplicate submissions, zero fabricated claims and zero policy violations.**

## Core loop

1. Discover across official portals + trusted organisations.
2. Normalise and deduplicate.
3. Verify freshness and eligibility-critical facts.
4. Run deterministic hard gates before writing.
5. Read pages/infopacks into evidence-backed facts.
6. Score fit/value separately from application competitiveness.
7. Build a personalised dossier from verified private evidence.
8. Enforce call-specific AI policy.
9. Human review + submit.
10. Track organisation, application, outcome and trainer progression as a graph.

## Truth model

- Official source / original infopack = authority for opportunity facts.
- GitHub = executable/versioned truth for code, schemas, policies and public knowledge.
- Google Drive = private operational knowledge, evidence, infopacks and application dossiers.
- git.local / ChatGPT Library = portable snapshot/handoff.
- Derived projections are rebuildable from source facts + graph events.

## Hard safety rules

- Never invent experience, fewer-opportunities status, qualifications, language level or availability.
- Never auto-submit when a call forbids AI-generated answers or requires the applicant's own words.
- Never score a known-ineligible opportunity above zero.
- Never treat an LLM inference as a source fact.
- The repository is public: private applicant data is excluded by design.

## Lanes

`PARTICIPANT` · `YOUTH_WORKER` · `FACILITATOR` · `TRAINER` · `EXPERT`

## Project map

- `AGENTS.md` agent contract/checkpoints
- `goal.md` /define-goal
- `goal-state.json` machine-readable state
- `ARCHITECTURE.md` boundaries/data flow
- `knowledge/` programme/trainer/selection knowledge
- `schemas/` canonical contracts
- `src/uexchanges/` deterministic decision core
- `tests/` regressions
- `configs/` source registry and scoring weights

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m uexchanges.cli demo
```
