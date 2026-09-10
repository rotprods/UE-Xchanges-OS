# /next — UE-Xchanges-OS

Seal timestamp: `2026-09-10T14:46:00+02:00`
Baseline main observed before this handoff branch: `349f63f2109e40ab6cba960c7311456a5d7ae906`
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`
Authority: derived zero-context continuation directive only. Fresh GitHub/Drive/provider evidence always wins.

## Copy/paste directive for the next agent

```text
/next UE-Xchanges-OS — continue from the 2026-09-10 CGEV2/COS RuntimeGraph recovery seal.

DO NOT continue from chat memory. Reconstruct live truth first.

1) Read current GitHub main and record its SHA. Expected historical baseline of this seal is 349f63f2109e40ab6cba960c7311456a5d7ae906, but never trust it if main moved.
2) Read, in order: goal.md → AGENTS.md → MEMORY.md → agent_context/bootstrap_manifest.json → LIVE-STATE-OVERRIDE.json → STATE.md → HANDOFF.md → checkpoints/2026-09-10-cgev2-cos-runtimegraph-context-seal.md → agent_context/README.md → context.md → progress.md → checkpoints.md → session.md → runtimegraph.md → knowledge.md → recovery.md → CGEV2_COS.md → REGRESSION.md → LEARNINGS.md → CONSCIOUSNESS_ACT.md → NEXT.md.
3) Read private Drive authority: Context_Registry; Agent_Sessions; currently UNEXPIRED Work_Leases only; Agent_Event_Bus after the live watermark; RuntimeGraph V2 Command Center including Command_Center, Human_Now, Agent_Next, Source_Cursors and Dead_Letters.
4) Historical watermark captured by this seal: EVT-20260910T132147-CPR14-008. Treat it only as a lower bound. Read all later events.
5) Reconcile current scheduler state. At seal: UEX Runtime Dispatcher is DISABLED. Do not re-enable it merely because a simple scheduler probe works.
6) Treat these historical canary sessions as terminal and NEVER reuse them for writes:
   - SES-UEX-AUTO-20260910T010530-RG22-PCV3-001 → FAILED via CPR13.
   - SES-UEX-AUTO-20260910T113308-RG22-SCA-001 → FAILED after unconsumed Stage-A handoff expiry via CPR13.
   - SES-UEX-AUTO-20260910T115630-RG22-PCV4-001 → FAILED via CPR14; no own lease/source/projection mutation; no PASS inferred.
7) Verify the CPR14 session/event closure. Agent_Sessions showed SES-UEX-CHATGPT-20260910T131121-CPR14 as COMPLETED at 13:23:16 CEST, while the EventBus search used for this seal observed events only through CPR14-008 / LEASE_RELEASED at 13:21:47. If a later SESSION_COMPLETED event exists, consume it. If not, classify this as coordination/event projection divergence; do not rewrite history without an evidence-backed RPL.
8) Current code architecture to use: PR67 strict WriterAuthorization receipt/integrity boundary; PR68 stale ACTIVE_READ_ONLY visibility without writer promotion; PR69 bounded normal-writer health. Current main at seal includes PR69.
9) For a normal DERIVED_PROJECTION writer, historical control-plane hygiene is NOT the authorization health set. Use current exact session + BootstrapGuard + currently-unexpired leases/live owners through evaluate_bounded_writer_authorization_health. Preserve historical_hygiene_evaluated=false unless a separate full scan proved otherwise.
10) Next primary milestone: obtain one real SCHEDULER_PRODUCTION_CANARY_PASS using RUNBOOKS/RG22_SCHEDULED_CANARY.md on current main.
    - NEW unique session.
    - full manifest bootstrap.
    - exact session uniqueness.
    - currently-unexpired leases only.
    - bounded writer health required SLOs PASS.
    - canonical content-addressed WriterAuthorizationReceipt.
    - persist WRITER_AUTHORIZATION_GRANTED and immediately acquire the exact lease; no unrelated work between them.
    - exact-ID ACTIVE readback.
    - source MICRO-BATCH only: at most one adapter slice, at most 5 candidates, at most 2 exact application/opportunity subgraphs.
    - exact-ID routing only; no fuzzy/title/embedding authority.
    - deterministic idempotency + monotonic cursors + max 3 same-strategy transient retries + Dead_Letter poison/unroutable events.
    - derived self-heal only; no canonical domain repair from RG2.2.
    - release exact lease, read back RELEASED, close terminal session, emit SESSION_COMPLETED and only then SCHEDULER_PRODUCTION_CANARY_PASS.
11) Do NOT execute Agent_Next from RG2.2. Do NOT pay, authenticate, expose/use credentials/OTP/cookies, externally PREFILL, or Submit.
12) If the first production-path canary passes, run a SECOND clean one-shot canary before enabling recurrence. Prefer one no-delta/idempotent path and one admissible derived-delta path if safely available.
13) Only after two clean scheduled canaries: enable UEX Runtime Dispatcher at bounded hourly cadence; keep the same micro-batch and closure budget; observe at least 3 consecutive clean recurrent cycles before calling RG2.2 scheduled production stable.
14) Historical hygiene remains a separate CONTROL_PLANE_REPAIR/watchdog workflow. Do not make every normal RG2.2 cycle perform archaeological scans.
15) After RG2.2 stability: continue safe self-healing subset → RG2.3 reversible execution → provider-specific Form Gateway certification → receipt engine → real opportunity/application throughput.
16) Before ending your session, persist exact main SHA, EventBus watermark, own session/lease lifecycle, tests, blockers, next transition and handoff. Never use this chat as continuity.

Definition of Done for your next wave:
- no reused historical session IDs;
- no unexpired overlapping lease ignored;
- no aged/mismatched WriterAuthorization receipt used;
- no canonical domain mutation from RG2.2;
- no Agent_Next execution;
- no prohibited external side effect;
- exact readback for every coordination mutation;
- own leases released;
- own session terminal;
- current STATE/HANDOFF/NEXT updated if the promotion state changes.
```

## If the canary cannot finish inside one Scheduled Task activation

Do not weaken authority, increase scope, invent a PASS, or split a logical writer across stale handoffs by default. First record the exact phase and timings. The prior Stage-A/Stage-B experiment proved cold bootstrap can complete but also created handoff-expiry complexity. Prefer fixing execution budget/implementation over adding more orchestration layers.

## Promotion ladder

`CONTROL_PLANE_CERTIFIED → SCHEDULER_PRODUCTION_CANARY_PASS #1 → PASS #2 → HOURLY CANARY-LIKE PRODUCTION → 3 CLEAN RECURRENT CYCLES → RG2.2_SCHEDULED_PRODUCTION_STABLE → SAFE SELF-HEAL → RG2.3 → FORM PROVIDER CERTIFICATION → RECEIPT-BACKED THROUGHPUT`
