# UE-Xchanges-OS — HANDOFF

Checkpoint: 2026-09-01 16:36 Europe/Madrid

Purpose: allow a completely fresh agent to recover UE-Xchanges-OS without relying on chat memory.

## Cold start — mandatory order

1. Read `goal.md`.
2. Read active `LIVE-STATE-OVERRIDE.json` before using stale counts/statuses from `goal-state.json`.
3. Read `STATE.md`.
4. Read `AGENTS.md` and `docs/MULTI_AGENT_CONTROL_PLANE.md`.
5. Read the newest file in `checkpoints/`.
6. Read private Drive CRM Dashboard, `Agent_Sessions`, `Work_Leases`, and the tail of `Agent_Event_Bus`.
7. Search Gmail for organiser replies newer than the checkpoint and read complete threads.
8. Before any canonical write, confirm there is no conflicting unexpired lease and acquire a fresh narrow lease.
9. Recompute affected lifecycle states from evidence; persist canonical truth before updating Notion/Todoist/HubSpot.
10. Protect deadline-critical P0 conversion before architecture or backlog work.

## Canonical resources

- Drive CRM: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`
- Drive handoff folder: `1T8EW70y2Clfhnug3vRqRhtTtqDqvQPid`
- Private CGEV2 pack: `19tM23N37cqweaWPSoVMxEECZhfOSrEJPGj_nRJB71q4`
- Todoist project: `6hCjVwH7R6hq49G3`
- Todoist W9 control: `6hPPRQrhG6cmhh3V`
- Notion command center: `https://app.notion.com/p/3cebf3f09a2d8109b388e9b10c19ae32?pvs=204`
- GitHub repo: `rotprods/UE-Xchanges-OS`

## Hard evidence rules

- `ROUTE_QUERY_SENT != APPLICATION_SUBMITTED`
- `ELIGIBLE != SELECTED`
- `INVITED_TO_APPLY != ACCEPTED`
- `PAYMENT_REQUIRED_FOR_PLACE != CONFIRMED`
- No `APPLICATION_SUBMITTED` without evidence.
- Latest authoritative organiser reply overrides older assumptions.
- Todoist/Notion/HubSpot are projections, not submission evidence.
- Do not infer sensitive or professional credentials that are not evidenced.

## Immediate next actions

1. Fresh Gmail sweep for Step Into Paralympics, Game of Nature, I-PLAY, COMPASS/BreGal, CIVIS and other active organisers.
2. Human conversion gates:
   - COMPASS: €30 payment → receipt → final Tally.
   - CIVIS LAB: €50 payment + proof if choosing the place; no travel purchase before host approval.
   - SABER: host-authorised late form + receipt.
   - Step Into Paralympics: submit only if current direct form/cutoff remains valid; capture receipt.
3. Resolve UNICEF Rome hard gates before 3 Sep.
4. Resolve European Youth Forum Communications Officer work-right/profile/form gates.
5. Reauthorize HubSpot before any relationship writes; then dedupe and require explicit write confirmation.
6. Refresh SALTO paid trainer/facilitator calls frequently during September.
7. Continue source/detail backlog; Telegram stays blocked until source text/export/Telegram-capable access exists.
8. Fold the active public override into `goal-state.json` only after exact-head/main CI and then retire the override.

## Tool ownership

- Gmail / official portal: external evidence.
- Drive CRM + Event Bus: canonical operational truth and provenance.
- GitHub: policy/schema/code/public recovery state.
- Notion: human-readable reconstructible cockpit; one-way projection.
- Todoist: human execution queue.
- HubSpot: organisation/contact/paid-relationship graph only.
- Calendar: deadlines/interviews/travel.

## Current safe boundary

At the CGEV2 checkpoint all narrow execution/source leases up to global bootstrap have been released. A fresh agent must re-read `Work_Leases` rather than assuming this remains true.

The whole-project Definition of Done is NOT reached: W9 receipt floor remains unmet, human P0 gates remain open, Telegram remains source-blocked, HubSpot writes remain gated, and `goal-state.json` still needs eventual integration of the active runtime override.
