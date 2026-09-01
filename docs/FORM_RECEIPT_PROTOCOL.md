# Form Submission Receipt & Idempotency Protocol

## Purpose

A browser click is an irreversible side effect, but it is **not** proof that an application was received. This protocol defines the evidence boundary between a browser executor and UE-Xchanges-OS canonical submission state.

## Core invariants

```text
CLICK_SUBMIT != SUBMITTED
FORM_NAVIGATED != SUBMITTED
THANK_YOU_URL_ALONE != RECEIPT
APPLICANT_INTENT != SUBMISSION
TODOIST_DONE != SUBMISSION
```

`SUBMITTED_CONFIRMED` requires a durable `SubmissionReceipt` compatible with the exact execution plan and submission attempt.

## Submission key

Each materially distinct payload has one deterministic idempotency key:

```text
answer_pack_hash = SHA256(ordered field_key + final answer values + attachment refs)
submission_key   = SHA256(application_id | form_fingerprint | answer_pack_hash)
```

The submission key deliberately ignores plan generation timestamps, evidence metadata and UI-only state. Changing any final answer, attachment or form fingerprint creates a new key.

`execution_plan_hash` is separate. It hashes the full model-visible execution/audit plan, including provenance/evidence IDs, policy/auth settings and timestamps. A payload can therefore retain the same submission key while its audit plan changes; the receipt must reconcile against the exact attempt plan hash.

## Required pre-click sequence

1. Re-read canonical application state and current form fingerprint.
2. Verify plan is not expired and all hard/policy/human-review gates pass.
3. Compute `submission_key`.
4. Query confirmed receipts for that key.
5. Query prior attempts for that key.
6. Run duplicate guard.
7. Create and durably persist a `SubmissionAttempt` **before** the irreversible click.
8. Only then may an authorised browser actuator perform Submit.

## Duplicate guard

Precedence:

1. Matching receipt exists → `BLOCK_CONFIRMED_DUPLICATE`.
2. Matching non-failed attempt exists without reconciled receipt → `RECONCILE_UNVERIFIED_ATTEMPT`.
3. Only failed/no matching attempts exist → `SAFE_TO_ATTEMPT`.

An unresolved attempt is never automatically retried. The system must inspect confirmation state, provider portal and/or email receipt first.

A failed attempt may be retried only when the failure proves that submission did not become ambiguous. Browser adapters should use narrow error codes such as `network_before_submit` rather than declaring `FAILED` after an uncertain post-click timeout.

## Receipt evidence

A `SubmissionReceipt` requires one of:

- authoritative provider/submission reference;
- authoritative receipt email reference; or
- captured confirmation text hash **plus** screenshot reference.

A final/confirmation URL without supporting evidence is insufficient.

Receipt reconciliation requires exact equality for:

- `application_id`;
- `submission_key`;
- `form_fingerprint`;
- `execution_plan_hash`.

The receipt timestamp may not precede the attempt timestamp.

## Browser boundary

The browser executor may emit:

```text
SUBMISSION_ATTEMPT_STARTED
SUBMIT_CLICKED
CONFIRMATION_OBSERVED
```

but may **not** emit canonical `SUBMITTED_CONFIRMED` directly.

Only the receipt verifier + canonical execution state resolver may promote the application after evidence reconciliation.

## Ambiguous failure examples

These remain `UNVERIFIED` and block automatic retry:

- timeout immediately after click;
- browser crash after click;
- redirect occurs but confirmation cannot be parsed;
- success UI appears but no evidence bundle is persisted;
- provider returns an unknown status;
- confirmation page is observed but audit plan/fingerprint cannot be matched.

## Secret handling

Submission keys and receipts contain no passwords, cookies, session tokens, OTPs or other BLACK-field values. Authentication remains inside the browser/session boundary.

## Persistence

Private receipt bundles should eventually persist under the application dossier with:

```text
receipt.json
confirmation screenshot
form fingerprint/schema
execution plan
final answer payload
```

The public GitHub projection may record aggregate receipt/submission status only; applicant answers and private evidence stay in Drive.
