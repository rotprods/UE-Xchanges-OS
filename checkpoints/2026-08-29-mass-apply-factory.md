# Checkpoint — Mass Apply & Infopack Factory

Date: 2026-08-29  
State: `MASS_APPLY_FACTORY_LIVE`

## Policy transition

Execution changed from selective P0/P1 preparation to complete viable coverage.

Priority now controls processing order only. A call is excluded from submission only by a verified objective terminal condition.

## Private CRM projection

Verified after write:

- 156 canonical opportunity records;
- 144 application/dossier records;
- 144 `Mass_Apply_Queue` rows;
- 88 `Source_Inbox` nodes;
- 0 submission receipts in this wave.

The queue includes current SALTO training listings compatible with Spain, discovered ESC and Eurodesk opportunities, existing organisation-watch calls, repaired orphan opportunity/application relationships and a trainer/facilitator watch lane.

## Drive state

Existing workspace topology was reused rather than duplicated:

- `00_READ_FIRST`
- `01_PROFILE_EVIDENCE`
- `02_PROGRAMME_KNOWLEDGE`
- `03_OPPORTUNITIES`
- `04_INFO_PACKS`
- `05_APPLICATIONS`
- `06_TRAINER_PATH`
- `07_ORGANISATIONS`
- `08_OUTCOMES_ANALYTICS`
- `09_AGENT_HANDOFF`
- `99_ARCHIVE`

A private master document, `UE-Xchanges-OS — MASS APPLY & INFOPACK FACTORY v1.0`, was placed in `00_READ_FIRST`.

## Todoist projection

The existing fallback master task was renamed to `UE-Xchanges-OS — Mass Apply Opportunity Graph` and updated with current counts and policy.

Wave W8 contains:

- T0–T4 deadline buckets;
- ESC verification;
- Eurodesk/traineeship hard-gate verification;
- paid trainer/facilitator watch;
- recurring Infopack Factory;
- recurring Application Factory;
- recurring Submission Gate;
- Acceptance Decision.

The CRM remains canonical; Todoist intentionally does not mirror all 144 rows as individual tasks.

## Hard invariants

- `UNKNOWN` is verification debt, not a discard reason.
- No final submission text while AI policy is unresolved.
- No fabricated youth-work, NFE, trainer, degree, language, affiliation, availability or sensitive-attribute claims.
- Historical youth-sector experience does not auto-pass current-context requirements.
- No `SUBMITTED` state without a receipt or explicit human confirmation tied to the call.
- Calendar conflicts are resolved after acceptance, not during discovery.
- Verified TOY-qualifying trainer references remain 0.

## Immediate processing front

1. T0 deadlines: 29–30 August.
2. T1 deadlines: 31 August–1 September.
3. Existing almost-ready dossiers with human/private gates.
4. ESC and Eurodesk routes with short upcoming deadlines.
5. Later and rolling calls.

## Definition of done

Every non-terminal queue row reaches either:

- `SUBMITTED → RECEIPT_STORED`; or
- a source-backed terminal state with an explicit reason.

Public policy: `docs/MASS_APPLY_POLICY.md`.  
Temporary read-order override: `MASS_APPLY_OVERRIDE.md`.
