# UE-Xchanges-OS — RuntimeGraph Recovery Map

Seal: `2026-09-10T14:46:00+02:00`
Baseline main: `349f63f2109e40ab6cba960c7311456a5d7ae906`

> RuntimeGraph is a derived execution read model, never canonical domain truth.

## Current execution split

```text
CGEV2 control/provenance
    |
    +--> RG2.2 = source observation + deterministic derived reconciliation
    |
    +--> RG2.3 = reversible Agent_Next action execution
    |
    +--> Human = irreversible/sensitive actions
    |
    +--> COS = semantic retrieval/topology only
```

RG2.2 must never execute Agent_Next.

## Current reliability stack

### Writer authorization
PR67 established strict canonical WriterAuthorizationReceipt validation/integrity. A receipt is coordination evidence only.

### Lifecycle health
PR68 detects stale `ACTIVE_READ_ONLY` sessions without granting writer authority.

### Bounded normal-writer health
PR69 added `evaluate_bounded_writer_authorization_health`.

For normal `DERIVED_PROJECTION` authorization, use:
- exact stable-ID rows for the new current session;
- real BootstrapGuard for that session/ACK/proposed lease/prelease evidence;
- currently-unexpired leases only;
- exact owner-session + bootstrap evidence for any actually-live ACTIVE leases.

Do not feed unrelated historical hygiene into the writer critical path and do not claim historical hygiene is green.

## Scheduled production runbook

Canonical runbook: `RUNBOOKS/RG22_SCHEDULED_CANARY.md`.

Production canary hard path:

```text
NEW SESSION
→ full bootstrap
→ exact session uniqueness
→ current main/EventBus/unexpired leases
→ bounded health
→ real WriterAuthorization
→ content-addressed receipt
→ persist WRITER_AUTHORIZATION_GRANTED
→ immediately acquire exact lease
→ exact-ID ACTIVE readback
→ select ONE due adapter slice
→ <=5 candidates
→ <=2 exact subgraphs
→ deterministic derived reconciliation
→ readback
→ exact lease RELEASED
→ terminal session
→ SESSION_COMPLETED
→ SCHEDULER_PRODUCTION_CANARY_PASS
```

## Current scheduler state

- Tiny native Scheduled Tasks probe: PASS.
- Scheduler control-plane canary V3: PASS for receipt/lease/release lifecycle only.
- Production-path canary PASS: NOT PROVEN.
- Recurring `UEX Runtime Dispatcher`: DISABLED.

PCV3, staged-A and PCV4 are terminal `FAILED` after separate control-plane repairs. Do not resume them.

## Source adapter law

During canary/initial production:

1. select at most one adapter slice per activation;
2. canonical strong-receipt inbox first if nonempty; otherwise oldest/most-overdue due cursor among Gmail organiser replies, Form Gateway safe evidence and authoritative official source;
3. inspect <=5 candidates;
4. route <=2 exact application/opportunity subgraphs;
5. do not scan a second adapter;
6. preserve continuation boundary; never advance cursor past unprocessed evidence.

State-changing facts require explicit adapter-contract evidence + exact `application_id`/`opportunity_id`.

Never use:
- fuzzy title match;
- embeddings/COS similarity;
- absence of email;
- raw provider prose alone;
- open form alone;
- transient browser state alone.

## Receipt law

Gmail cannot directly become a receipt. Strong receipt confirmation requires canonical evidence bound to exact submission identity.

`SubmissionAttempt != SubmissionReceipt`.

## Derived self-heal allowlist

RG2.2 may self-heal actual mismatches only on:
- Command_Center;
- Human_Now;
- Agent_Next projection only;
- Claim_Registry;
- Dispatcher_State;
- Source_Cursors;
- Dead_Letters;
- Todoist runtime projection only with exact persisted `runtime_action_id → task_id` binding.

Never self-heal canonical Opportunities, Applications, Mass_Apply_Queue, Execution_Log, Agent_Event_Bus, Agent_Sessions, Work_Leases, Autofill_Profile or Human_Gates as a RuntimeGraph projection repair.

## Closure law

Reserve final activation budget for closure. Once closure begins, start no new source/provider/projection operation.

Success requires exact read-back, own lease release, `RELEASED` verification, terminal session and terminal event evidence.

## Immediate next milestone

`SCHEDULER_PRODUCTION_CANARY_PASS #1` on current main.

Then second independent clean canary → bounded hourly dispatcher → at least 3 clean recurrent cycles → `RG2.2_SCHEDULED_PRODUCTION_STABLE`.
