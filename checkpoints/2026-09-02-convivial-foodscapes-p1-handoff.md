# UE-Xchanges-OS — CONVIVIAL FOODSCAPES P1 handoff

Checkpoint: 2026-09-02 00:22 Europe/Madrid

Correlation: `CORR-20260902-CONVIVIAL-HANDOFF`
Canonical verification event: `EVT-20260902T002200-HOFF-002`

## Purpose

Persist the material P1 discovery from the mobility watch so a zero-context agent can recover it without chat memory.

## Canonical opportunity

- Opportunity ID: `non_salto-convivial-foodscapes-2026`
- State: `POLICY_GATE_PENDING`
- Priority: `P1`
- Role: `visual_artist`
- Programme: EU-funded `CONVIVIUM / New European Bauhaus` artist residency
- Title: `CONVIVIAL FOODSCAPES: call for an artist`
- Host: Quinta das Relvas x CONVIVIUM
- Location: Branca, Portugal
- Residency: `2026-11-01` → `2026-11-30`
- Deadline: `2026-09-15`
- Eligible-country gate: Spain passes; official call includes `BE, FR, NL, NO, PL, PT, ES`.
- Official source/application page: https://quintadasrelvas.pt/convivialfoodscapes/

## Funding captured from the official call

- flights covered;
- accommodation covered;
- meals excluded;
- €1,000 financial support covering residency costs;
- up to €150 for materials/small tools through reimbursement;
- possible later exhibition artwork transport/insurance support up to €1,250 if selected for the 2027 exhibition.

## Creative / professional fit

This is a high-value non-SALTO lane for visual/media trajectory rather than a conventional youth mobility application.

The call accepts visual, conceptual, digital, performative and research-based work. Captured facilities/equipment include visual-arts studio, analogue photography lab subject to availability, DSLR, studio lighting and multimedia equipment.

Application package captured in CRM:

- portfolio: maximum 5 pages;
- website/social link;
- CV;
- one-page motivation letter.

## Hard gates — do not bypass

1. `AI_POLICY_UNKNOWN`
2. `FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED`

Eligibility currently reads:

`PASS_COUNTRY_AND_VISUAL_ARTIST_PROFILE; AI_POLICY_UNKNOWN; FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED`

Required next gate:

`VERIFY_AI_POLICY_AND_NOVEMBER_AVAILABILITY_THEN_PREPARE`

Do **not** recommend submission, create `APPLICATION_SUBMITTED`, or enqueue this opportunity into `Mass_Apply_Queue` while either hard gate remains unresolved.

## Canonical placement at checkpoint

Drive CRM `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`:

- `Opportunities` row 178 contains the canonical record;
- `Decision_Queue` row 26 exposes it as P1 with the required verification gate;
- `Mass_Apply_Queue` has no row for this opportunity by design while the hard gates remain unresolved.

Aggregate state after this discovery:

- canonical opportunities: **176**;
- Mass Apply / application nodes: **164**;
- organisations: **30**;
- current-wave receipt-backed submissions: **0**.

The stored RuntimeGraph v1 materialisation still reflects the 164-row Mass Apply queue and therefore does not need a new application node for this gated discovery. Recompute projections after a material canonical/application mutation, not merely to force this opportunity into an executable queue prematurely.

## SALTO paid trainer watch from the same scan

No newly verified open paid trainer/facilitator call crossed the trajectory-changing alert threshold. The previously announced September facilitator wave — 2 plenary facilitators + 5 co-creation-lab facilitators — remains watch-only until the actual calls open and fee/eligibility evidence exists.

## Recovery rule

A fresh agent must read the private Drive CRM/evidence first, then `LIVE-STATE-OVERRIDE.json`, `STATE.md`, `HANDOFF.md`, this checkpoint and the current Event Bus tail. Official/current source evidence overrides this checkpoint if any deadline, funding, AI-policy or eligibility term changes.
