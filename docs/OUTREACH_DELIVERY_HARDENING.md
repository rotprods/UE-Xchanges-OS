# Outbound delivery hardening — Wave 1

Status: candidate implementation for #75. This layer prepares and validates outbound application packets; it does **not** send email, acquire WriterAuthorization, reserve a distributed outbox effect, or mutate provider/domain state.

## Purpose

Reduce duplicate/out-of-context outreach while keeping the North Star focused on complete applications to distinct viable calls.

The preparation contract fails closed on:

- missing exact organisation/call/application identity;
- stale or incomplete cross-thread organisation history;
- duplicate initial candidature for the same call/application;
- prior `RESERVED`/`OUTCOME_UNKNOWN` effect that has not been reconciled;
- invalid or form-required route being replaced by email;
- missing/tampered canonical signature;
- missing/tampered CV for an initial candidature;
- private/audit attachments or unapproved attachment roots;
- stale source evidence or a passed deadline without explicit late permission;
- `NO_CONTACT`, terminal/waiting states, exhausted follow-up budget and same-organisation 24h anti-spam cooldown;
- requested replies that are not bound to the exact unresolved inbound message;
- unsolicited internal tooling/RuntimeGraph/AI-policy prose.

## Canonical signature

`docs/application-assets/email-signature.html` is pinned to Git blob `0a7a4ea118770f605896ad500eb7fe41e6b84fb8` and the extracted sendable fragment is pinned by SHA-256. The display-page toolbar/script is never part of the rendered email body.

## Provider boundary

A successful `prepare_packet(...)` result always has `send_authorized=False`.

The real send boundary must still perform, in order:

1. fresh authoritative facts + cross-thread history;
2. WriterAuthorization decision/receipt and an exact unexpired work lease;
3. atomic outbox/effect reservation with fencing;
4. a second file/hash/history check at provider invocation;
5. one provider call;
6. provider-result reconciliation before any retry;
7. typed evidence capture and canonical state transition;
8. projections and lease/session closure.

A timeout is `OUTCOME_UNKNOWN`, never permission to send again.

## Follow-up policy

Initial candidature and follow-up are separate intents. One follow-up is allowed only after five business days from a proven initial send and only if the project state still permits contact. Replies explicitly requested by an organiser are bound to the exact inbound message and do not consume the generic follow-up budget, but cannot override `NO_CONTACT`.

## Forms

`form_preflight` is a small deterministic guard, not a browser executor. It blocks false sending-organisation choices, unknown required fields and runs exceeding the default 40-step / 3-no-progress budget. Form execution remains governed by the existing form stack and issue #79.

## Tests

Tests are provider-free and do not send or mutate anything. Promotion requires repository CI on the exact PR head plus a separately authorised delivered-MIME test before a real provider adapter can rely on this layer.
