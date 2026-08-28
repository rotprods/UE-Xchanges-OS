# CURRENT OPERATIONAL OVERRIDE — MASS APPLY

Effective: **2026-08-29**

Read this immediately after `goal-state.json` until the next canonical release updates the main operating contract.

## Decision

The former execution principle “optimise high-value acceptances per application hour; do not optimise raw submission volume” is superseded for the current campaign by:

> Prepare and submit every live Spain-compatible opportunity that passes objective mandatory gates. Prioritisation orders the queue; it does not remove viable opportunities.

## What remains unchanged

The override does **not** relax:

- source verification;
- Spain/residence/nationality eligibility;
- deadline checks;
- mandatory role, age, language, degree, affiliation or participation limits;
- evidence and temporal-scope integrity;
- AI/application policy;
- duplicate prevention;
- human review/authentication;
- receipt-backed submission state.

Confirmed hard `FAIL` blocks only the affected call. `UNKNOWN` becomes a verification task.

## Current aggregate state

- canonical opportunity rows: **156**;
- application/dossier nodes: **144**;
- source inbox nodes: **88**;
- dedicated mass-apply queue rows: **144**;
- submission receipts stored in this wave: **0**;
- verified TOY-qualifying trainer references: **0**.

Private CRM and original source evidence remain higher-authority than this public projection.

## Queue order

`T0 today/tomorrow → T1 2–3 days → T2 4–7 days → T3 8–14 days → T4 later/rolling`.

All non-terminal rows must end in either:

- `SUBMITTED` with a stored receipt; or
- a verified objective terminal reason: deadline passed, Spain ineligible, hard requirement fail, call closed, invalid route or duplicate.

See `docs/MASS_APPLY_POLICY.md`.
