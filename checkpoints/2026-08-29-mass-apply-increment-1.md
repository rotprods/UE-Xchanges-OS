# Checkpoint — Mass Apply Increment 1

Date: 2026-08-29  
State: `MASS_APPLY_160_OPPORTUNITIES_148_DOSSIERS`

## Verified private CRM state

- canonical opportunity rows: **160**;
- application/dossier nodes: **148**;
- `Mass_Apply_Queue` rows: **148**;
- `Source_Inbox` nodes: **93**;
- submission receipts stored in this wave: **0**;
- verified TOY-qualifying trainer references: **0**.

## Added in this increment

### Under the Hood II — EYP 53940

- ESC Team Volunteering, Sint Maarten;
- Spain eligible, age 23–30;
- 10 October–7 December 2026;
- deadline shown as 29 August 2026 at 13:00, time zone unspecified;
- the correct route is the organiser form plus a human-owned motivation letter sent by email;
- ESC portal-only applications are not valid;
- private availability, prison/youth-detention setting consent, ESC/EVS cumulative participation and AI policy remain mandatory gates;
- urgent dossier and unsent Gmail draft created; no receipt exists.

### Next Chapter 5.0 — EYP 53751

- Spain eligible;
- activity began 26 August and has no published deadline;
- retained as `LATE_ENTRY_VERIFY` rather than discarded;
- remaining vacancy and acceptable arrival date must be confirmed before submission.

### Connect, Contribute, Grow — EYP 53992

- Spain eligible;
- Magdeburg, 1 November–11 December 2026;
- deadline 13 September 2026;
- accommodation, three meals per day, EUR 7/day pocket money and travel reimbursement stated;
- portal/private gates remain open.

### SABER — Soilpunk Youth Exchange

- Spain is listed in the live call route;
- Romania, 15–25 September 2026;
- source owner, Spanish sending route, exact `ASAP` deadline, form/infopack and AI policy require final verification;
- promoted to the queue, not marked submitted.

## Negative provenance

The current Madrid `Project Management and Communication` ESC call excludes Spain from its participant-country list. It is stored as `SPAIN_NOT_ELIGIBLE_CURRENT_CALL` in `Source_Inbox` and is not promoted as a candidate.

## Material correction

`The Get Together III — Practitioner As Person` was a listing-level false positive. The official detail shows a deadline of 31 May 2026 and no Erasmus+ travel reimbursement. It is now terminal:

`CLOSED_DEADLINE_PASSED → CALL_CLOSED → NO_SUBMISSION`.

## Execution projection

Todoist W8 and its master node were updated to 160 opportunities / 148 dossiers. Dedicated urgent tasks now exist for:

- Under the Hood II;
- SO.ART;
- SHIFT;
- Next Chapter 5.0 late-entry verification;
- SABER source/form verification.

## Integrity state

- No final submission has been claimed without a receipt.
- No current youth-work, prison-work, trainer, degree, CEFR, organisation-mandate, fewer-opportunities or sensitive-identity claim has been inferred.
- Media contribution is disabled by default in prison, juvenile-detention, minors and vulnerable-group contexts unless explicit safeguarding and consent rules permit it.
- Priority remains scheduling-only; confirmed objective hard fails remain call-specific terminal states.
