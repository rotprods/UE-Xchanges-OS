# Fenced outbound email provider boundary — Wave 1B

Status: candidate implementation for issue #84. This layer establishes an at-most-once **effect coordination contract** around one outbound email provider call. It is not a Gmail credential store, not an external capability issuer, and not canonical application-state authority.

## Safety model

One exact effect identity is derived from:

`organization_id | call_id | application_id | intent | authoritative_source_version`

A writer may invoke the provider only after all of these independently pass:

1. a prepared packet passed the application/outreach preflight;
2. current main still equals the head observed by the writer fence;
3. WriterAuthorization/lease authenticity is verified by an authoritative control-plane adapter;
4. a **separate external email-send capability** is valid for the same session/action and verified by its provider/connector authority;
5. the outbox atomically reserves the exact effect key and fencing lease;
6. exactly one provider invocation is made for that reservation generation.

WriterAuthorization coordinates writers. It does **not** grant Gmail/send capability.

## Effect states

`NOT_SENT → RESERVED → SEND_IN_PROGRESS → SEND_CONFIRMED | OUTCOME_UNKNOWN | DELIVERY_FAILED`

`OUTCOME_UNKNOWN` is deliberately sticky. Timeout, exception, missing provider IDs, or delivered-MIME uncertainty never permits a blind retry. A second reservation is possible only after authoritative reconciliation proves that no message was sent and records the evidence reference.

`DELIVERY_FAILED` is also sticky until reconciled, because a local/provider error classification alone must not create an unbounded retry loop.

## Atomicity and fencing

`InMemoryOutbox` is a reference implementation used for deterministic tests. Production must provide the same `Outbox` contract using a durable atomic/CAS or transactional store. The lease ID is the fencing token for the reserved generation.

Two concurrent writers for the same effect identity must yield at most one successful reservation/provider invocation, even when they arrived through different agent sessions or Gmail threads after those aliases were canonicalised upstream.

## Provider result and evidence

A provider response saying "confirmed" is insufficient by itself. Confirmation requires:

- provider message ID;
- provider thread ID;
- delivered MIME readback;
- exact From/To/Subject and no unexpected Cc/Bcc;
- exactly one rendered Erasmus signature marker in HTML;
- non-empty `text/plain` fallback;
- exact attachment filename → SHA-256 manifest, with no duplicate attachment names.

Any mismatch becomes `OUTCOME_UNKNOWN`, preserving the provider IDs for reconciliation without promoting a false `SEND_CONFIRMED` state.

A confirmed email send is evidence of `EMAIL_CANDIDATURE_SENT`; it is not selection, form submission, acceptance, payment, or travel approval.

## Privacy

Public GitHub may contain code and a placeholder signature template only. Applicant identity/contact payload, private CV/evidence files, emergency/health data, provider credentials, connector tokens and message bodies remain in private runtime/Drive/provider systems. The gateway accepts digests/expected metadata; it does not publish private payloads.

## Production integration gate

Before a real sender is wired to this module, require a separately authorised sandbox/self-send proving:

- authoritative writer-fence verifier;
- authoritative external email-capability verifier;
- durable production outbox/CAS semantics;
- one real provider call;
- delivered MIME readback;
- typed evidence persisted with provider IDs;
- retry reconciliation after an induced/observed unknown outcome.

The unit tests intentionally use injected fake verifiers/provider functions and have no network side effects.
