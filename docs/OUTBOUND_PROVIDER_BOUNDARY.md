# Fenced outbound email provider boundary — Wave 1B

Status: phase A is on `main` from PR #91. Phase B adds a durable SQLite outbox and stable effect identity under issue #84. This boundary coordinates at-most-once email effects; it is not a Gmail credential store, not an external capability issuer, and not canonical application-state authority.

## Safety model

There are deliberately **two different hashes**:

1. **Stable effect identity**
   `organization_id | call_id | application_id | intent`
2. **Versioned packet digest**
   includes the authoritative source version plus sender/recipient/subject/body/attachments/preflight metadata.

A source or infopack revision may require rebuilding the packet, but must never create permission for a second initial email for the same exact application effect. `SqliteOutbox` therefore reserves by the stable effect identity while storing the current source version and packet digest for audit.

A writer may invoke the provider only after all of these independently pass:

1. a prepared packet passed the application/outreach preflight;
2. current main still equals the head observed by the writer fence;
3. WriterAuthorization/lease authenticity is verified by an authoritative control-plane adapter;
4. a **separate external email-send capability** is valid for the same session/action and verified by its provider/connector authority;
5. the durable outbox atomically reserves the exact effect identity and fencing lease;
6. exactly one provider invocation is made for that reservation generation.

WriterAuthorization coordinates writers. It does **not** grant Gmail/send capability.

## Effect states

`NOT_SENT → RESERVED → SEND_IN_PROGRESS → SEND_CONFIRMED | OUTCOME_UNKNOWN | DELIVERY_FAILED`

`OUTCOME_UNKNOWN` is deliberately sticky. Timeout, exception, missing provider IDs, delivered-MIME uncertainty, or crash recovery never permits a blind retry. A second reservation is possible only after authoritative reconciliation proves that no message was sent and records the evidence reference.

`DELIVERY_FAILED` is also sticky until reconciled, because a local/provider error classification alone must not create an unbounded retry loop.

A process crash while `SEND_IN_PROGRESS` may be recovered only to `OUTCOME_UNKNOWN`; it can never be reset directly to `NOT_SENT`.

## Atomicity, persistence and fencing

`InMemoryOutbox` from phase A remains a deterministic unit-test/reference helper. It is **not** the production durability boundary.

`SqliteOutbox` is the first durable implementation of the `Outbox` contract:

- filesystem-backed SQLite database;
- WAL mode;
- transactional `BEGIN IMMEDIATE` reservation/state transitions;
- stable effect identity independent of source revision;
- compare-state transitions for reserve/begin/finish/reconciliation;
- lease ID retained as the fencing token;
- generation increments only after authoritative reconciliation returns an unknown/failed effect to `NOT_SENT`;
- state survives object/process restart.

Two concurrent writers using separate SQLite connections for the same effect identity must yield exactly one reservation/provider invocation. A source revision cannot bypass a prior confirmed/unknown/in-progress effect.

For a single host/shared filesystem this provides durable transactional semantics. A future multi-host deployment may replace SQLite with a remote transactional/CAS store, but must preserve the same transition contract and tests.

## Provider result and evidence

A provider response saying "confirmed" is insufficient by itself. Confirmation requires:

- provider message ID;
- provider thread ID;
- delivered MIME readback;
- exact From/To/Subject and no unexpected Cc/Bcc;
- exactly one rendered Erasmus signature marker in HTML;
- non-empty `text/plain` fallback;
- exact attachment filename → SHA-256 manifest, with no duplicate attachment names.

Any mismatch becomes `OUTCOME_UNKNOWN`, preserving provider IDs for reconciliation without promoting a false `SEND_CONFIRMED` state.

A confirmed email send is evidence of `EMAIL_CANDIDATURE_SENT`; it is not selection, form submission, acceptance, payment, or travel approval.

## Privacy

Public GitHub may contain code and structural/example metadata only. Applicant identity/contact payload, private CV/evidence files, emergency/health data, provider credentials, connector tokens and real message bodies remain in private runtime/Drive/provider systems. The gateway accepts digests/expected metadata; it does not publish private payloads.

## Production integration gate

Before real organiser traffic is wired to this module, require a separately authorised sandbox/self-send proving:

- authoritative writer-fence verifier;
- authoritative external email-capability verifier;
- a durable outbox path/storage lifecycle appropriate to the runtime;
- one real provider call;
- delivered MIME/provider-ID readback at the capability actually exposed by the provider;
- typed evidence persisted with provider IDs;
- retry reconciliation after an induced/observed unknown outcome.

If the connected provider cannot expose raw delivered MIME, record that capability limitation explicitly and do **not** claim strong MIME verification; use the strongest available structured readback and keep the stronger gate unresolved.

Unit tests use injected fake verifiers/provider functions and temporary SQLite files. They have no network/provider/domain side effects.
