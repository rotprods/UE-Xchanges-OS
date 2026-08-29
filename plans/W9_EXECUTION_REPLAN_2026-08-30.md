# W9 Execution Replan — 30 August to 4 September 2026

Status: `PLAN_LOCKED / EXECUTION_FIRST`

This replan does not replace the W9 Controlled Submission Baseline. It reorders it from the verified live state at 30 August: 167 opportunities, 156 mass-apply rows, 35 urgent rows classified, zero receipts, 60 unresolved Telegram posts, EYP/ESC and MySALTO access not yet verified, two YUPI packages awaiting human assets, and one projection divergence still open.

## Executive decision

No further architecture work is authorised unless execution exposes a repeatable deterministic failure. The critical path is:

1. recover account and portal access;
2. resolve T0/T1 deadlines;
3. complete and submit receipt-backed applications;
4. ingest strategic deltas without displacing urgent execution;
5. complete source coverage and close W9 with reconciled state.

`APPLY_EVERYTHING_VIABLE` remains canonical. Priority schedules work; it does not exclude an otherwise viable call. Hard eligibility, truth, AI policy, authorised route, deadline and receipt gates remain non-negotiable.

## Consistency corrections

- **Harry Totter and the Facilitator’s Stone** already exists in the CRM as a listing-level record. Do not create a duplicate. Enrich the existing record, capture the official form and AI policy, resolve the active non-formal-learning/youth-work gate, and then rescore it.
- **CineVolunteers 3.0** is a genuine new-ingest candidate. Create one canonical identity and resolve its ten-month commitment, remote-work compatibility, ESC-history/limit, supporting route, full funding, form and AI-policy gates before any application recommendation.
- The EYP gate is functional account/profile access. Complete EU Login, MFA and the ESC profile, then store privately any official participant identifier the platform actually generates. Do not assume a field label before the portal shows it.
- **Under the Hood II** remains `DEADLINE_PASSED / NOT_SUBMITTED`. Reopen only on explicit organiser evidence of an extension or authorised late route.

## Execution phases

### F0 — State recovery

Freeze a fresh read of Drive, Gmail, GitHub and Todoist. Correct the stale W9 phase projection, recompute divergence, retain overdue human tasks as open rather than falsely completed, disable superseded W8 recurrences, and ensure every deadline inside 72 hours has exactly one owner and next action.

Exit gate: no pre-30-August assumption controls a live route.

### F1 — Human access

Complete EU Login/MFA/ESC profile, verify one functional EYP application route, verify MySALTO profile and draft access, and create/verify TCA-Net. Credentials, recovery codes and private identifiers never enter GitHub or Todoist.

Exit gate: portal access is `PASS` with evidence, or a reproducible external blocker is recorded.

### F2 — 30 August T0 control

Ingest organiser replies and recompute gates. Resolve SO.ART and SHIFT only after the role, form, AI and human gates pass. Close proven hard-fails with official evidence. Keep Under the Hood closed unless an explicit extension arrives.

Exit gate: every T0 is `SUBMITTED_WITH_RECEIPT`, `TERMINAL_OBJECTIVE`, or `WAITING_EXTERNAL_EVIDENCE` with sent query, owner and dated follow-up.

### F3 — Ask-once profile evidence

Resolve only the P0 evidence required by current calls: exact Erasmus metadata and roles, personally delivered activities, current youth affiliation if any, formal education, professional timeline, approved portfolio links, remote-work constraints, relevant ESC history and paid-role invoicing details. Every externally used claim must map to evidence.

### F4 — Short-form T1 execution

Capture and resolve Inside Track, CIVIS LAB, Game of Nature participant route and all 31 August/1 September SALTO details. For each call execute the full chain: official source → Spain route → deadline → role → funding → form → AI policy → evidence map → human final → QA → submit/terminal.

### F5 — YUPI asset factory

Complete factual CVs, applicant-owned motivation letters, maximum-90-second English videos, attachment manifests, file/link/audio/duration tests and final call-specific QA for Building With Our Hands and Behind the Scenes.

Exit gate: both packages are `HUMAN_REVIEW_READY`.

### F6 — First receipts

Use the internal 31 August buffer to submit both verified YUPI packages and every other objective-pass urgent route. Store sent evidence, timestamp, attachment manifest and acknowledgement immediately. Calendar conflict remains a portfolio edge until acceptance; it is not a reason to avoid applying.

Exit gate: receipt floor 2, target 5, or a source-backed impossibility report proving that fewer than two legitimate routes existed.

### F7 — Strategic delta and cohort completion

Ingest CineVolunteers 3.0. Enrich Harry Totter without duplication. Resolve all remaining T1 rows by 2 September and submit every objective-pass non-YUPI route. Keep participant, training/staff and paid trainer/facilitator lanes distinct.

### F8 — Source completeness

Resolve the 60 Telegram posts in four batches of 15 with provenance and dedupe. Refresh SALTO Training Calendar, SALTO Calls for Trainers, EYP/ESC, Eurodesk, hosts, partners, official forms and infopacks. A deadline inside seven days always pre-empts batch order.

### F9 — Trainer trajectory

No experienced-trainer or TOY claim is allowed without evidence. Build the route through one delivered youth-facing AI/media/storytelling activity, consent-safe artefacts, evaluation, organiser confirmation, external reference, documented NFE methods, trainer CV/portfolio and verified commercial terms. Harry Totter may become a bridge only if its current-role hard gate passes.

## Current routing

| Opportunity | Operational state | Next mandatory gate |
|---|---|---|
| Building With Our Hands | Prepare and submit after human assets | Human wording, video, attachment QA, authenticated send, receipt |
| Behind the Scenes | Prepare and submit after human assets | Human wording, video, attachment QA, authenticated send, receipt |
| Inside Track | Form capture and human submit pending | TCA-Net access, exact questions, AI policy, receipt |
| Game of Nature participant | Prepare | Exact route/form/policy; group-leader role remains separate |
| SO.ART | Hold | Organiser + human role/dissemination/form/AI gates |
| SHIFT | Hold | Active youth-work interpretation + MySALTO form |
| CIVIS LAB | Hold | Spanish partner reply + role/preselection/funding/policy |
| Under the Hood II | Deadline passed | Explicit extension only |
| Harry Totter | Existing listing; enrich and rescore | Active NFE/youth-work, form, AI policy |
| CineVolunteers 3.0 | New ingest required | Open status, 10-month commitment, ESC/funding/form/AI gates |
| September facilitator signal | Watch, not open | Published call and contractual terms |

## Projection changes required

- Drive: new CineVolunteers identity; Harry enrichment; Under the Hood closure semantics; W9 phase/divergence correction; receipt paths and event-sourced transitions.
- Todoist: preserve W9 as the control parent; reschedule access tasks without false completion; retire superseded W8 recurring controls; add only CineVolunteers and Harry delta tasks, not one task per CRM row.
- GitHub: update aggregate state only after Drive reconciliation; never publish private identifiers or application prose; exact-head CI before merge.
- Gmail: full-thread reply ingestion, not unread-only; silence is not rejection; the Under the Hood `DO NOT SEND` draft remains unsent.

## Notification contract

Notify the user only for a new significant P0/P1, a material deadline/route/status/eligibility/funding change, an outcome or receipt failure, a trajectory-changing paid trainer/facilitator call, or an immediate human gate. Routine P2 ingestion, dedupe, source extraction and heartbeats remain silent but are persisted.

Every notification includes source, eligibility facts, exact deadline/timezone, role, funding, why it matters, gate state and the next mandatory gate. Never recommend `APPLY` or `SUBMIT` while a hard gate remains unresolved.

## W9 stop contract

W9 passes only when:

- EYP/ESC and MySALTO access are verified;
- every T0/T1 is receipt-backed, objectively terminal, or waiting external evidence under an SLA;
- both YUPI calls are resolved;
- at least two receipts exist, target five, or a valid impossibility report exists;
- Telegram is 60/60 resolved or explicitly inaccessible/invalid;
- known hard-SLO violations are zero;
- Drive, GitHub and Todoist have zero material divergence;
- leases are released and a cold-start handoff succeeds.

No stop is permitted with an unowned urgent deadline, guessed receipt, unresolved wrong-country route, final AI prose under `AI_UNKNOWN`, live source backlog that may hide current deadlines, or material projection divergence.

## Post-W9 sequence

- W10: resolve the remaining T2/T3/T4 cohort.
- W11: follow-up and outcome control for every receipt.
- W12: create a real youth-work/facilitation evidence path.
- W13: steady-state discovery, deadline control, submissions and outcome learning without backlog growth.

The immediate next gate is `W9.3 ACCESS`: EU Login/MFA/ESC profile, MySALTO and TCA-Net. In parallel, agents may verify T0 calls and prepare YUPI assets, but no new architecture may displace this path.
