# Checkpoint — W9 baseline reconciliation and urgent queue

Date: 2026-08-29 20:35 Europe/Madrid  
State: `W9_0_RECONCILED_W9_1_COMPLETE`

## Private live baseline

The authoritative Drive CRM reported at the W9 execution cut:

- 167 opportunity rows;
- 156 application nodes;
- 156 Mass_Apply_Queue rows;
- 96 Source_Inbox nodes;
- 20 organisation nodes;
- 50 Execution_Log events after this wave's events;
- 4 outcome rows;
- 0 receipt-backed submissions;
- 60 unique Telegram posts content-unresolved.

Counts may grow as new sources arrive. This checkpoint records the W9 starting cut; Drive remains operational authority.

## W9 control plane

Two private CRM tabs were created:

- `W9_Control` — stop metrics, access gates, receipts, Telegram progress and state reconciliation;
- `W9_Urgent` — all 35 T0/T1/undated urgent rows.

All 35 urgent rows now have:

- a W9 classification;
- exactly one next action;
- an owner;
- a dated follow-up;
- an explicit gate summary.

Initial classifications:

- `TERMINAL_OBJECTIVE`: 7;
- `HUMAN_NOW`: 4;
- `WAITING_EXTERNAL`: 4;
- `VERIFY_NOW`: 20.

Todoist W9.1 was completed. W9.0 can close after this public aggregate sync merges and exact-head/main CI are observed.

## Game of Nature signal

Papaya explicitly confirmed that the applicant should apply and proposed group-leader consideration.

Public-safe routing:

- participant profile: organiser-supported PASS;
- group-leader requirements: UNKNOWN;
- follow-up sent requesting responsibilities, mandatory prior group-leader/current youth-work evidence, authorised role/form route, current Spain places/deadline and AI policy;
- participant dossier preparation proceeds in parallel;
- no official group-leader experience is claimed.

No application or receipt is claimed.

## SHIFT policy and role gate

Official SALTO source and infopack verify:

- Spain eligibility;
- Trakai, Lithuania, 15–22 October 2026;
- no participation fee;
- accommodation, food and materials covered;
- Erasmus+ distance-band travel reimbursement;
- mandatory online onboarding and evaluation;
- target profile actively working with young people and designing/implementing youth activities;
- fully AI-generated applications are rejected.

The application route is therefore `AI_ASSIST_ONLY_HUMAN_FINAL`. A precise role-eligibility clarification was sent to the organiser. MySALTO form capture and current-role evidence remain pending. No submission is permitted unless the role gate passes.

## Human access gates

Still blocking portal execution:

- functional European Youth Portal / ESC account;
- private Participant Reference Number;
- verified MySALTO login/form access.

These remain human-authenticated actions. Passwords, 2FA and identifiers never enter public GitHub.

## Current next operations

1. Human creates/verifies EYP/ESC account and stores PRN privately.
2. Human verifies MySALTO and captures SHIFT questions.
3. Agents execute the 20 `VERIFY_NOW` and monitor the four `WAITING_EXTERNAL` rows.
4. Roberto completes applicant-owned YUPI letters/videos and submits both verified routes with receipts.
5. Telegram extraction runs in parallel, with any deadline inside seven days promoted immediately.

## Integrity

- no submission without receipt;
- no `UNKNOWN` promoted to PASS;
- no wrong-country form;
- no fabricated youth-work/group-leader/trainer claim;
- no final AI-authored prose under unknown/prohibited policy;
- no sensitive attribute inferred.
