# Checkpoint — 2026-08-29 — User-supplied opportunity batch

## Scope

Three supplied calls were converted into canonical opportunity/application/source/organisation events. Public GitHub records only public call facts and routing decisions; applicant identity/contact/private answers remain in Drive.

## 1. E.A.S.Y. — Economically Advanced and Smart Youth

- Type: Erasmus+ Youth Exchange.
- Host: Above Foundation, Hungary.
- Location/dates: Csolnok, 3–12 November 2026.
- Original infopack visually verified and archived in the private operational workspace.
- Spain appears as a partner country; participant baseline is 5 young people + 1 leader per country.
- Spain travel ceiling: EUR 309; accommodation and three meals/day stated.
- Public applicant baseline provisionally passes for the private profile as participant.
- Verification debt: exact deadline, remaining Spain places, Spanish sending route, authoritative topic, exact form questions and AI/application-writing policy.
- Material content conflict: the shared announcement says financial literacy/money management; the infopack mainly describes intercultural communication/teamwork/creativity.
- Host clarification sent. No application submitted.
- State: `PROVISIONAL_PASS_EXTERNAL_FACTS_PENDING`.

## 2. FRATERNITAS Poronin networking event

- Type: private self-funded networking event; **not Erasmus+ or EU-funded**.
- Intended body/post dates: 10–14 December 2026, Poronin, Poland.
- Open 18+; shared rooms; English; no prior international experience required.
- No travel reimbursement and no organised meals.
- Material conflicts retained:
  - announcement EUR 117 vs PDF EUR 140;
  - PDF filename 03–07 December vs body/post 10–14 December;
  - breakfast-food wording and exact inclusions;
  - deadline, payment and refund terms unknown.
- Organiser clarification sent. No registration/payment made.
- State: `FACT_CONFLICT_VERIFY_BEFORE_PAYMENT`.

## 3. SALTO 15257 — Volunteering Teams as a Tool to Support Inclusion

- Type: SALTO/ESC Partnership-building Activity.
- Residential activity: Metsäkartano, Finland, 5–9 October 2026.
- Online preparation: 16 September 2026.
- Current deadline: 7 September 2026; selection 14 September.
- Spain is listed among programme countries.
- Mandatory target is institutional/professional: volunteering-organisation representative, volunteering-team implementer, organisation active in individual volunteering exploring teams, or current social/youth-worker inclusion route.
- Current private evidence does not establish an organisational mandate or implementation role; historical Erasmus attendance is insufficient.
- State: `HARD_REQUIREMENT_FAIL_CURRENT_CYCLE`.

### Deduplication

Listing `15257` is a cancellation-fill/reopened CallVersion for the same underlying Finland event previously published as SALTO `14954` (same title, dates, venue and profile; original deadline 9 August 2026). The graph keeps:

- one canonical Event/Opportunity;
- original CallVersion `14954` = closed;
- reopened CallVersion `15257` = current;
- all source/provenance records;
- no duplicate application or opportunity metric.

## Operational projections updated

- Drive: three dossiers; both supplied PDF infopacks copied into the private infopack archive.
- CRM: `Opportunities`, `Applications`, `Organisations`, `Source_Inbox`, `Mass_Apply_Queue`, `Execution_Log`, `Human_Gates`.
- Gmail: clarification requests sent to Above Foundation and FRATERNITAS; tracked under `UEX/Waiting Reply`.
- Todoist: one P0 E.A.S.Y. application task, one Poronin verification task, one blocked/future institutional-route task.

## Safety/quality decisions

- No deadline inferred from a live form.
- No private event represented as Erasmus-funded.
- No payment before fee/date/refund conflicts resolve.
- No organisation-representative claim without a genuine mandate.
- No final application copy generated while the call-specific AI policy is unknown.
- No form submission state without a receipt.

## Next deterministic actions

1. Ingest Above Foundation reply -> resolve deadline/places/route/topic/policy -> capture form -> human-owned answers -> submit -> receipt.
2. Ingest FRATERNITAS reply -> resolve cost/date/deadline/payment/refund -> value/cost decision -> register or archive.
3. Archive SALTO 15257 current-cycle application while using its requirements to drive the legitimate organisation/ESC credential path.
