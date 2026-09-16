# UE-Xchanges-OS — Operating Policy vNext

Status: implementation contract
Date: 2026-09-16

## North Star
Maximise truthful, valid, receipt-backed Erasmus+/ESC applications and completed high-value mobility experiences per unit of human attention.

Infrastructure, research, documentation, agent activity, commits and email volume are not outcomes.

## Authority order
1. Current official/organiser evidence and authoritative submission receipts.
2. Private Drive CRM + append-only EventBus.
3. Current GitHub policy/schema/code/recovery contracts.
4. RuntimeGraph derived projection.
5. Task/UI/agent projections.
6. Chat context.

A lower layer MUST NOT resurrect an action invalidated by a higher, newer authority.

## Application fast path
`DISCOVER → DEDUPE → VERIFY HARD GATES → QUALIFY → PREPARE → QA → APPLY VIA AUTHORISED ROUTE → CAPTURE RECEIPT → RECONCILE → WAIT/OUTCOME`

For each opportunity the qualification pass MUST resolve to exactly one operational disposition:
- `APPLY`
- `VERIFY_ONE_BLOCKER`
- `SKIP`
- `EXPIRED`
- `DUPLICATE`

`PREPARATION_QUEUED` is not a durable resting state.

## Apply-first contact policy
When an authorised application route exists and hard eligibility gates pass, prefer applying over emailing for redundant clarification.

Email an organisation only when a material blocker remains, such as:
- genuinely ambiguous eligibility;
- contradictory authoritative dates or requirements;
- broken/inaccessible application route;
- mandatory sending-organisation data not available from authoritative sources;
- information required to submit truthfully that cannot otherwise be resolved.

Do not send reassurance-seeking, status-chasing, duplicate clarification or post-submit confirmation messages merely to create activity.

Default contact budget: one necessary initial contact plus at most one reasonable follow-up unless the organisation actively continues the conversation or a new material blocker appears.

## Truth and tool-disclosure policy
Applicant facts and claims MUST remain truthful and evidence-bound. Internal tools, agents, browser automation or implementation details are normally irrelevant to recipient-facing correspondence and MUST NOT be introduced gratuitously. If an application explicitly asks about authorship, AI/tool use, or imposes a relevant policy, answer truthfully and comply with it.

## Erasmus email signature gate
Qualifying Erasmus+/youth-project/global-mobility email MUST use the canonical repository signature asset once merged and available on the active branch. Missing/substituted identity blocks send. Forms, portals and DMs retain their native identity requirements.

## Anti-zombie invariants
- `DECLINED`, `EXPIRED`, `CLOSED_WITHOUT_APPLICATION`, `REJECTED`, `ATTENDED`, `COMPLETED` produce no application/payment/contact action unless a new authoritative event explicitly reopens the case.
- `RECEIPT_CONFIRMED` forbids resubmission of the same application identity.
- `APPLIED`/partial receipt states forbid automatic resubmit; reconcile evidence first.
- A newer organiser answer satisfies older clarification tasks addressing the same question.
- A passed deadline terminates submission actions unless an organiser explicitly authorises a late route.
- Terminal transitions invalidate leases and queued actions whose premise depended on the previous state.
- RuntimeGraph is disposable/rebuildable derived state, never the source of truth.

## Browser/form completion semantics
Executor/process completion is not submission completion.

Required stages:
1. `FORM_OPENED`
2. `FIELDS_DISCOVERED`
3. `PREFILL_COMPLETED`
4. `REVIEW_READY`
5. `SUBMIT_ATTEMPTED`
6. `RECEIPT_OBSERVED`

Only authoritative evidence at stage 6 may produce `RECEIPT_CONFIRMED`. A browser run that terminates after partial field completion is `PARTIAL_EXECUTION`, not success.

## Receipt confidence
Receipts/events should distinguish at least:
- `NONE`
- `SELF_REPORTED`
- `ORGANISER_ACKNOWLEDGED`
- `PROVIDER_CONFIRMATION`
- `AUTHORITATIVE_RECEIPT`

Selection/acceptance is a separate outcome dimension and MUST NOT be inferred from submission evidence.

## CV truth model
Mobility history MUST separate:
- `ATTENDED_COMPLETED`
- `ACCEPTED_UPCOMING`
- `APPLIED_WAITING`
- `OTHER_INTERNATIONAL_EXPERIENCE`

Only attended/completed projects may be represented as completed Erasmus experience.

## Creative contribution
Where relevant and truthful, applications may surface filmmaking, photography, editing, VFX, storytelling and social-content capability as concrete contribution. Credit/tagging for produced content may be proposed naturally when appropriate, never represented as a condition of participation or selection.

## KPIs
Primary:
- valid applications submitted/week;
- receipt-confirmed applications/week;
- acceptance rate on resolved applications;
- acceptances per human hour;
- completed high-value mobilities.

Guardrails:
- emails/application;
- duplicate actions prevented;
- stale/zombie actions killed;
- partial executor runs incorrectly promoted to submit = 0;
- false applicant claims = 0.
