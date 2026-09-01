# UE-Xchanges-OS — CHANGELOG

## 2026-09-02 — RuntimeGraph V2.1 dispatch-cycle recovery seal

- Promoted RuntimeGraph V2.1, release `6c23c9b6a70f33a7cb1eb780c54e49ebf5cf0d16`, to the current versioned recovery surface; legacy RuntimeGraph v1 frontier counts are now explicitly historical.
- Persisted completed dispatcher cycle `SES-UEX-AUTO-20260901T233539-28` / `EVT-20260901T234155-DSPC-008`.
- Recorded material Human Frontier transition **3 → 4** after the official Step Into Paralympics form was reverified live at `2026-09-01T23:35:39+02:00` on the organiser-confirmed extension date.
- Preserved strict Step facts: exact closing time unknown; stale `18/08/2026` deadline text and stale 2025 transport dates remain in the form; application action is Human READY; travel purchase remains blocked pending written 2026 transport-date clarification; no submission or receipt claimed.
- Persisted current Human Frontier: Step Into Paralympics, COMPASS, CIVIS LAB and SABER.
- Persisted Source Cursors: Gmail last item `1a05eb5b1861284d`; official-source last item `step-form-live-20260901`; Receipt Reconciler/Form Gateway still at bootstrap/none.
- Confirmed current-wave authoritative receipts **0** and Dead Letters **0**.
- Recorded projection repair event `EVT-20260901T233800-DSPC-004`; the Step Applications column-offset incident was corrected immediately and changed no payment/submission/receipt state.
- Preserved dispatcher guarantees: at-least-once + deterministic idempotency, monotonic cursors, same-strategy retry budget 3, dead-letter isolation, exact-ID routing only.
- Preserved hard boundaries: no payment, auth, credentials/OTP/cookies, external PREFILL certification or irreversible agent Submit.
- Added `checkpoints/2026-09-02-runtimegraph-v2-1-dispatch-cycle-close.md` and refreshed `STATE.md`, `HANDOFF.md` and `LIVE-STATE-OVERRIDE.json` without modifying canonical domain/application rows or active RuntimeGraph V2.2 adapter projections.
- Retained the newer **176-opportunity** aggregate state and CONVIVIAL FOODSCAPES P1 hard gates from the immediately preceding continuity seal.

## 2026-09-02 — CONVIVIAL FOODSCAPES P1 continuity seal

- Verified `non_salto-convivial-foodscapes-2026` is already canonical in Drive `Opportunities` row 178 and appears in `Decision_Queue` as P1.
- Canonical opportunity count advanced to **176**; `Mass_Apply_Queue` remains **164** because CONVIVIAL is intentionally not enqueued while hard gates are unresolved.
- Preserved `POLICY_GATE_PENDING` with `AI_POLICY_UNKNOWN` and `FULL_NOVEMBER_AVAILABILITY_UNCONFIRMED`; required gate is `VERIFY_AI_POLICY_AND_NOVEMBER_AVAILABILITY_THEN_PREPARE`.
- Persisted official-call funding and creative-fit facts, application package, deadline 2026-09-15 and Branca/Portugal residency dates 2026-11-01 through 2026-11-30.
- Updated private zero-context recovery pack, `STATE.md`, `HANDOFF.md`, `LIVE-STATE-OVERRIDE.json` and created `checkpoints/2026-09-02-convivial-foodscapes-p1-handoff.md`.
- Recorded continuity correlation `CORR-20260902-CONVIVIAL-HANDOFF` and canonical verification event `EVT-20260902T002200-HOFF-002`.
- SALTO paid trainer watch remains unchanged: no newly verified open trajectory-changing paid call; announced September 2-plenary + 5-co-creation-lab facilitator wave remains watch-only until actual call/fee/eligibility evidence exists.

## 2026-09-01 — CGEV2 zero-context survival checkpoint

- Reconciled Gmail organiser replies and P0 states.
- Added COMPASS as canonical opportunity/application/outcome and recovered its historical candidature provenance as `submitted_at/receipt UNRECOVERED` rather than guessed.
- Confirmed COMPASS selection after waitlist and sent explicit place acceptance; payment/Tally remain human-only.
- Reconciled Step Into Paralympics participant eligibility and same-day extension; cutoff/form-validity follow-up sent.
- Reconciled CIVIS LAB payment-to-participant-list route and refund/travel sequence.
- Reconciled Oriel 53967 as deadline-passed/submission-unverified rather than falsely not-submitted.
- Ingested I-PLAY after Ticket2Europe directly confirmed open places; route/details follow-up sent.
- Completed W9.35 one-way Drive → Notion full read-model backfill and later propagated new global opportunities, bringing projection target to 175 opportunities / 164 applications / 30 organisations.
- Audited HubSpot relationship architecture; writes remain reauthorization-gated.
- Refreshed SALTO paid trainer/facilitator watch; no new open trajectory-changing call found as of 15:35 Europe/Madrid.
- Attempted Telegram 60-post source burn-down; current tooling cannot retrieve target post bodies, so 60/60 remain explicitly unresolved/access-blocked.
- Bootstrapped global source waves and promoted current high-value P1 lanes: European Youth Forum Communications Officer, UNICEF Valencia Project Associate, UNICEF Rome Communication Associate, Camp Leaders 2027 media activity specialist, Camp America 2027 media counselor.
- PR #26 merged a bounded public `LIVE-STATE-OVERRIDE.json` and reconciliation checkpoint; main CI green. Subsequent global ingests require CGEV2 refresh of that override.
- Created private Drive CGEV2 recovery pack and public `STATE.md`/`HANDOFF.md` to eliminate chat-memory dependency.

## 2026-08-31 — CP7 email reconciliation

- Recovered stale V2 release assumptions against live Drive/Gmail evidence.
- Ingested material organiser replies and preserved strict receipt discipline.
- Main checkpoint commit `419452755e33503ce20959e3267e91411bfc2e46` reached green CI.

## 2026-08-30 — Strive Greece + architecture recovery work

- Ingested T4DT2B Greece as gated opportunity and merged new Step Into Paralympics call-version evidence.
- Persisted candidate V2/context-pack work but later invalidated any unmerged V2 release claim as current authority.

## 2026-08-29 — Apply-everything + multi-agent control plane

- Expanded policy to `APPLY EVERYTHING VIABLE` for all compatible current opportunities.
- Added multi-agent sessions, leases, event bus, source coverage, economics and profile intake controls.
- Established evidence precedence and receipt-backed submission discipline.
