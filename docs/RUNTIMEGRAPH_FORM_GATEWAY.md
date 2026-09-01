# RuntimeGraph ↔ Form Execution Gateway

Authority: engineering integration contract. Private Drive evidence and current official form/provider state remain operational authority.

## Boundary

RuntimeGraph owns **what executable action is next**.

The Form Execution Gateway owns **how a verified application form is represented and advanced safely** through typed form states.

Neither owns opportunity truth or receipt truth by itself.

## Graph bridge

```text
Application
  ↓ HAS_ACTION
RuntimeAction: CAPTURE_FORM
  ↓ PRODUCES
FormExecutionPlan
  ↓ CONSTRAINS
FormField ownership / AI policy / auth requirement
  ↓ UNLOCKS
RuntimeAction: PREFILL | HUMAN_REVIEW | HUMAN_AUTH | SUBMIT
  ↓ PRODUCES
SubmissionAttempt
  ↓ VERIFIED_BY
SubmissionReceipt
  ↓ PROVES
Application submission transition
```

## Executor mapping

- `green_agent_factual` → AGENT may prefill from verified evidence.
- `yellow_agent_assisted_human_review` → AGENT may prepare; HUMAN reviews/owns final.
- `red_human_confirmation` → HUMAN only.
- `black_secret_or_never_model` → HUMAN only; value never enters model-visible runtime state.
- `human_login` / `human_mfa` → HUMAN action.
- final irreversible submit remains HUMAN in UE-Xchanges RuntimeGraph v1 even if a generic Form Gateway contract can represent broader future authority.

## State mapping

| Form Gateway state | RuntimeGraph consequence |
| --- | --- |
| `form_captured` | AGENT verify schema/questions |
| `form_schema_verified` | AGENT map evidence/answers |
| `answer_pack_resolved` | AGENT prefill where allowed |
| `prefill_ready` / `prefilled` | AGENT validate, then HUMAN review if needed |
| `validation_pass` | HUMAN final/review frontier |
| `human_review_required` | HUMAN action |
| `human_approved` | HUMAN submit action may become eligible when all gates pass |
| `submit_attempted` | waiting for confirmation; never `SUBMITTED` yet |
| `submission_confirmation_observed` | AGENT verify evidence |
| `receipt_captured` | receipt candidate; validate binding to application/form/attempt |
| `submitted_confirmed` | RuntimeGraph may complete submit transition with authoritative receipt evidence |
| `blocked` | Runtime action WAITING/FAILED with explicit reason |

## Invariants

1. A `SubmissionAttempt` is not a receipt.
2. A confirmation page without application/form binding is not sufficient submission authority.
3. RuntimeGraph cannot move an application to submitted without `SubmissionReceipt` or equivalent authoritative confirmation.
4. Form Gateway cannot bypass RuntimeGraph hard gates: Spain/role/deadline/policy still apply.
5. RuntimeGraph cannot expose BLACK/secret field values in GitHub, Todoist or public snapshots.
6. Duplicate submission prevention uses application identity + form fingerprint + submission key/idempotency contract.
7. If the live form fingerprint changes, the previous execution plan is stale and must be re-captured before submit.

## Recovery

A fresh agent reconstructs the RuntimeGraph first, then loads any current `FormExecutionPlan` only for the action/application it is about to execute. Cached form plans never become a second source of opportunity truth.
