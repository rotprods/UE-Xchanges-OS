# Form Human Approval Capability Protocol

## Goal

A human approval must authorize **one exact submit operation**, not a mutable browser tab or a broad future permission.

The Form Execution Gateway therefore uses a short-lived HMAC-signed capability token bound to:

```text
application_id
form_fingerprint
submission_key
execution_plan_hash
action = submit
approved_at
expires_at
nonce
```

## Hard boundary

`human said yes once` is not a reusable submit permission.

An approval becomes invalid if any of the following changes after review:

- application identity;
- form structure/fingerprint;
- final answer or attachment payload;
- evidence/provenance or other execution-plan audit data;
- submit authority;
- plan state;
- plan expiry.

The browser actuator must verify the capability immediately before creating the durable submission attempt and before the irreversible click.

## Issue preconditions

A token may be issued only when:

1. the execution plan is not expired;
2. plan state is exactly `HUMAN_APPROVED`;
3. submit authority is exactly `AGENT_AFTER_APPROVAL`;
4. no unresolved/BLACK fields remain inside the model-visible plan;
5. a trusted approval surface supplies the human approver reference;
6. the local signing boundary has a strong secret.

Forms that contain BLACK fields requiring live human interaction remain human-takeover flows and do not receive autonomous submit capability until those fields are resolved outside the model-visible plan and a new exact plan is approved.

## Lifetime

Maximum TTL: **300 seconds**.

The token expires earlier when the underlying execution plan expires.

Expiry is strict: `now >= expires_at` is invalid.

## Secret handling

The HMAC secret:

- must contain at least 32 bytes;
- belongs to a trusted local runtime boundary;
- must never be returned to the model;
- must never be stored in GitHub, Drive, Notion, Todoist or browser page content;
- must never be logged;
- should ultimately be loaded from a local secret store such as macOS Keychain or an equivalent protected runtime secret provider.

The model may receive only verification outcomes such as:

```text
VALID
EXPIRED
INVALID_SIGNATURE
BINDING_MISMATCH
MALFORMED
```

## Browser contract

Immediately before submit:

```text
re-read form
→ recompute fingerprint
→ recompute submission key
→ recompute execution plan hash
→ verify approval token
→ duplicate guard
→ persist SubmissionAttempt
→ perform irreversible click
→ receipt protocol
```

If verification fails for any reason, the browser executor stops.

## Race protection

Changing a form field after human approval changes the submission key or plan hash and invalidates the token.

Changing only form structure changes the fingerprint and invalidates the token.

Changing evidence/provenance while leaving the final answers unchanged keeps the payload submission key stable but changes the execution-plan hash, therefore still invalidating the approval. This prevents approval of one evidence state being silently reused after a material audit change.

## Replay

A valid approval token is not, by itself, replay protection. Replay is prevented by the receipt/idempotency guard:

1. approval proves human authorization for the exact plan;
2. submission key checks prior attempts/receipts;
3. durable attempt is persisted before click;
4. matching receipt blocks subsequent submission.

Both controls are mandatory.

## Non-goals

The approval module does not:

- authenticate the user by itself;
- perform 2FA;
- expose cookies/session tokens;
- click Submit;
- solve CAPTCHA;
- execute payments;
- create canonical `SUBMITTED` state.

Those remain separate boundaries.
