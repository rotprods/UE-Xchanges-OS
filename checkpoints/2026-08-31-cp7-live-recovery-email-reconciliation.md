# 2026-08-31 — CP7 live recovery + organiser email reconciliation

## Authority reconstructed

- Current GitHub main before this state-sync branch: `dec379a1033ee135f7d37895cacbfe09bc37f7e8`.
- Private live authority: Drive CRM `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`.
- Fresh session: `SES-UEX-CHATGPT-20260831T191400-08`.
- Correlation: `CORR-20260831-CP7-EMAIL-WAVE`.
- Private event watermark at public-state reconciliation: `EVT-20260831T194500-EMAIL-009`.
- Receipts: **0**. No application submission is claimed by this checkpoint.

## Stale V2 recovery incident

The earlier graph-refactor session `SES-UEX-GPT56PRO-20260830T120306-05` remained projected as ACTIVE after its lease `LSE-UEX-ARCH-V2-20260830T120306-05` expired on 30 August.

Live GitHub main does not contain the previously described V2 architecture/kernel release. Therefore:

- the stale session is reconciled as `FAILED_STALE_LEASE_EXPIRED`;
- the lease is `EXPIRED`;
- sandbox/local V2 artifacts are candidate evidence only;
- no `V2_FINAL`, CP6 release or production authority is inferred;
- any future V2 work must start from current main under a fresh session/claim/lease after deadline-critical W9 execution is protected.

## Current aggregate private projection

- 168 opportunities;
- 157 applications / mass-apply nodes;
- 97 Source Inbox nodes;
- 26 organisation nodes after adding Informajoven Murcia;
- 5 outcome-history rows;
- 0 receipts;
- 60 unresolved unique Telegram posts.

## Full-thread Gmail wave

The 27–31 August Erasmus/youth-project reply corpus was searched and relevant full threads were read. Material inbound replies were labelled `UEX/Reply Ingested` and reconciled into Drive.

### CIVIS LAB

Euroactiva-T directly confirms:

- current youth-work employment is not mandatory;
- Roberto may participate honestly through the Spanish partner route;
- no public application form is required by the Spanish sending organisation;
- a EUR 50 management + civil-liability-insurance payment is requested;
- other project costs are covered;
- travel must originate from Spain.

Interest was confirmed by reply and the exact payment beneficiary/concept, transfer deadline, reservation effect and refund/cancellation conditions were requested. **No payment has been executed.**

State: `WAITING_HUMAN_PAYMENT_GATE`.

### SABER / Soilpunk

The host reports the formal deadline has passed but:

- the public form remains open;
- a Spanish-group participant cancelled;
- Roberto is explicitly invited to apply anyway;
- AI use is explicitly permitted by the host.

State: `HOST_AUTHORISED_LATE_APPLICATION`. The generic deadline terminal assumption no longer controls this call.

### Next Chapter 5.0

Synergy Bulgaria confirms the activity already started with a complete group.

State: `CLOSED_NOT_SUBMITTED_HOST_FULL_GROUP`. This is not a rejection and does not update negative application-quality priors.

### Sapounofouska six-workshop cluster

The organiser directly confirms Roberto is welcome to apply to all six workshops based on an educator / AI / creative-learning profile. Direct youth-work delivery is preferred but not mandatory. Responsible AI assistance is allowed if final answers remain truthful, authentic and personal. Multiple workshop applications are allowed.

Five current SALTO application-procedure routes were captured for immediate human final/submission; the VR/AR route still requires capture. Deadline: 31 August, 24:00 UTC.

### Behind the Scenes

YUPI's 31 August email referenced EYP opportunity `50317`, an older Behind call. The current authoritative call is EYP `53846`, 21 September–13 November 2026, deadline 31 August 23:59 Europe/Madrid.

A clarification reply was sent asking whether YUPI wants the current 53846 EYP Apply route or a full email package. The stale `50317` link is not used as current authority.

State: `HUMAN_NOW_CURRENT_EYP_OPEN_ROUTE_CLARIFICATION_SENT`.

### Informajoven Murcia

Informajoven confirms Roberto's youth/AI/storytelling collaboration proposal was forwarded internally to its European Projects colleagues.

State: `WARM_INTERNAL_REFERRAL`. This is not yet current youth-work evidence, a confirmed collaboration or a trainer reference.

### Game of Nature

Papaya's direct reply confirms the participant lane is a strong fit and suggests possible group-leader consideration. Participant preparation remains valid; group-leader eligibility is kept separate and unresolved pending role clarification.

## Outbound during this wave

- CIVIS LAB: requested exact payment/reservation/refund terms after confirming interest.
- YUPI / Behind: corrected stale call reference and requested the current authorised application route.

No payment, portal submission or receipt is claimed.

## Immediate frontier

Human-now deadlines take precedence over architecture work:

1. create/verify EYP/ESC access and open current Behind 53846;
2. complete Building final assets/video/send/receipt;
3. complete Behind final assets and current authorised route/receipt;
4. complete host-authorised SABER late form/receipt;
5. complete the five captured Sapounofouska forms and capture VR/AR route;
6. review CIVIS payment terms when received before any transfer.

## Coordination rule

`REGISTER SESSION → REFRESH CURSOR → ACQUIRE NARROW LEASE → MUTATE → EMIT EVENT → RECONCILE PROJECTIONS → RELEASE → HANDOFF`.
