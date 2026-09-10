# UE-Xchanges-OS — Regression / incident history

Seal: `2026-09-10T14:46:00+02:00`
Purpose: compress the scheduler/runtime recovery history into a falsifiable timeline so a successor does not repeat dead ends.

## Incident statement

Repeated scheduled RG2.2 runs surfaced the generic ChatGPT result `There was a problem with your scheduled task`. The investigation showed this was **not one proven single bug**. Multiple independent reliability defects and coordination gaps existed.

## Historical regression timeline

### R0 — scheduled-task symptom

Observed repeated scheduled failures with insufficient scheduler-level diagnostics. Early control-plane inspection found many RG2.2 sessions with no terminal state and lease rows that still displayed `ACTIVE` after TTL expiry.

Lesson: the scheduler UI result and RuntimeGraph lifecycle must be correlated; neither proves the other.

### R1 — WriterAuthorization receipt shape/integrity drift

Audit of historical `WRITER_AUTHORIZATION_GRANTED` payloads exposed malformed/incomplete records and assumptions that textual `ALLOWED` was enough.

**PR67** hardened:
- canonical payload validation;
- duplicate JSON-key rejection;
- content-addressed `receipt_id`;
- binding to exact decision/session/context/main/lease/scope/health/prelease evidence;
- authorization evaluation timestamp integrity;
- fail-closed auditor/gate behavior.

Result: CI green before/after merge; later writers must use the real contracts, not prompt prose.

### R2 — deterministic-clock test failures

The full CI suite initially showed failures caused by tests using a deadline that had become historical while not passing their declared fixed `NOW` into the compiler.

Fix: make tests deterministic; do **not** weaken production deadline logic.

Lesson: a red regression test can be a stale fixture rather than a production regression, but must be reproduced before changing it.

### R3 — stale `ACTIVE_READ_ONLY` blind spot

Health evaluation caught stale `ACTIVE` sessions but not stale nonterminal `ACTIVE_READ_ONLY` rows.

**PR68** added explicit stale read-only lifecycle visibility while preserving `ACTIVE_READ_ONLY` as non-writer.

Lesson: observability must not be implemented by broadening authority.

### R4 — orphaned/expired lease debt

Historical stale `ACTIVE` rows caused apparent or real coordination blockers. CPR12 ran narrow evidence-backed RPL repairs.

Material outcome:
- 29 orphaned-owner lease rows reconciled to objective `EXPIRED` with stable-ID read-back;
- repair fences released;
- `lease_fencing_integrity` restored for live-writer purposes;
- historical hygiene debt deliberately remained separate.

Lesson: expired text rows are hygiene debt; currently-unexpired validated leases are live fencing state.

### R5 — ad-hoc freshness threshold

A scheduler reliability canary rejected a receipt using an invented 60-second prelease threshold although current BootstrapPolicy allowed a wider window.

Fix: use versioned policy exactly; never smuggle stricter operational law into a prompt.

### R6 — control-plane canary V3 success

`SES-UEX-AUTO-20260909T134553-CANV3-001` completed a control-plane-only lifecycle with canonical receipt, exact lease ACTIVE read-back, exact release and terminal session. No sources, RuntimeGraph projection, Todoist, domain state or Agent_Next were touched.

This proved **control-plane lifecycle**, not production source-dispatch.

### R7 — full production canaries starved before lease/source path

Production canary V3:
- fresh scheduled session created;
- bootstrap work progressed for a long period;
- remained at prelease refresh;
- no own lease/source mutation;
- later reconciled `FAILED` by CPR13.

Staged experiment:
- Stage A completed full cold bootstrap and emitted a time-bounded handoff;
- Stage B did not consume it before expiry;
- Stage-A session reconciled `FAILED` by CPR13.

Production canary V4:
- registered on superseded main `801a3c7c...`;
- no own lease/progress/source mutation;
- later reconciled `FAILED` by CPR14.

Lesson: splitting orchestration adds handoff-liveness complexity. Prefer a bounded single activation if possible.

### R8 — full historical health in normal writer critical path

The project discovered a deeper architecture issue: global historical hygiene findings could block a healthy normal writer even when there was no actually-live conflicting lease.

**PR69**, merged to current baseline `349f63f2109e40ab6cba960c7311456a5d7ae906`, added `uexchanges.bounded_writer_health.evaluate_bounded_writer_authorization_health`.

Normal DERIVED_PROJECTION authorization now evaluates:
- exact current-session stable-ID uniqueness;
- real BootstrapGuard for that current writer;
- currently-unexpired leases and exact live-owner evidence;
- the three base SLOs required by WriterAuthorization.

It explicitly sets `historical_hygiene_evaluated=false` rather than pretending the entire control plane is green.

### R9 — scheduler dispatch isolated from runtime

A tiny Scheduled Task probe completed. Therefore native task dispatch is available; the unresolved challenge is completing the full RG2.2 production path inside activation constraints.

## Current reconciled canary debt

At this seal:

- PCV3 `SES-UEX-AUTO-20260910T010530-RG22-PCV3-001` → `FAILED` via CPR13; no own lease.
- Staged A `SES-UEX-AUTO-20260910T113308-RG22-SCA-001` → `FAILED` after handoff expiry via CPR13; no WriterAuthorization/lease.
- PCV4 `SES-UEX-AUTO-20260910T115630-RG22-PCV4-001` → `FAILED` via CPR14; no own lease/source/RuntimeGraph/provider mutation.
- Recent CPR repair leases are `RELEASED` by exact read-back.
- `UEX Runtime Dispatcher` remains disabled.
- No production-path `SCHEDULER_PRODUCTION_CANARY_PASS` is claimed.

## Current code regression gates

A successor should not remove or weaken tests covering:

1. strict receipt payload shape;
2. duplicate JSON keys;
3. content-address verification;
4. decision/timestamp binding;
5. exact session/context/lease/scope/main/watermark/health binding;
6. real BootstrapPolicy freshness;
7. stale `ACTIVE_READ_ONLY` observability without writer promotion;
8. bounded normal-writer health excluding unrelated historical hygiene;
9. duplicate session-ID denial;
10. actually-unexpired lease owner/integrity checks;
11. exact-ID routing;
12. source cursor monotonicity;
13. at-least-once idempotency;
14. Dead_Letter after bounded retry/poison;
15. closure/release/terminal session;
16. absolute external side-effect prohibitions.

## Regression decision tree

```text
Scheduled Task says ERROR
        |
        +--> Did task start?  NO --> scheduler dispatch/platform/permission incident
        |                    YES
        v
Did SESSION_STARTED persist?
        |
        +--> NO --> control-plane write/bootstrap capability incident
        |    YES
        v
Did BOOTSTRAP_CONTEXT_LOADED persist?
        |
        +--> NO --> bootstrap/read budget incident
        |    YES
        v
Did bounded health PASS?
        |
        +--> NO --> exact session/bootstrap/live-lease blocker
        |    YES
        v
Did canonical receipt persist and exact lease become ACTIVE?
        |
        +--> NO --> authorization critical-section/liveness incident
        |    YES
        v
Did one source micro-batch finish safely?
        |
        +--> NO --> adapter/provider/idempotency incident
        |    YES
        v
Did projection readback + lease RELEASED + terminal session succeed?
        |
        +--> NO --> closure/coordination incident
        |    YES
        v
SCHEDULER_PRODUCTION_CANARY_PASS
```

Do not jump branches in this tree by inference.
