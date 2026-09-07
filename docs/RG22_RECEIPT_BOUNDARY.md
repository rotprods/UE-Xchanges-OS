# RG2.2 receipt boundary: strict payload + real broker integration

Status: review candidate, not scheduler activation or production certification.

## Scope

`writer_receipt_payload.py` rejects noncanonical payload shapes without coercing
identity fields or silently repairing aliases. The offline receipt auditor uses it
and rejects duplicate JSON keys at every depth. Extra metadata inside a receipt is
rejected; metadata belongs in the EventBus envelope.

`writer_receipt_integrity.py` adds content-integrity checks that the original v1
structural verifier did not enforce directly:

- recompute the content-addressed `receipt_id` from every canonical receipt claim;
- when the issuing `WriterAuthorizationDecision` is available, bind
  `authorization_evaluated_at` to the exact original decision timestamp.

`writer_receipt_gate.py` composes the existing BootstrapGuard, health/SLO broker,
receipt issuer, strict shape guard, content-integrity guard and full verifier. It
does not accept an external `ALLOWED` flag as a substitute for evaluating the
broker.

Neither module reads providers, acquires a lock, writes a spreadsheet, submits an
application, executes Agent_Next, or grants domain/external capability.

## Integration for a separately authorized writer

1. Complete the current bootstrap manifest and register a fresh session.
2. Read current main, EventBus and all currently unexpired leases. Resolve exact
   overlapping resource IDs; an empty inventory must be explicit, never assumed.
3. Evaluate health from captured authoritative records. Preserve diagnostics; do
   not manufacture green SLOs or silently convert `ACTIVE_READ_ONLY` to `ACTIVE`.
4. Call `prepare_writer_authorization(...)` with the real captured objects.
5. Append `prepared.authorization_event_payload()` as the entire canonical
   `WRITER_AUTHORIZATION_GRANTED` payload. Do not insert arbitrary metadata.
6. Immediately before acquisition, refresh concurrency/current-main evidence.
   Reconcile events after the bound watermark: the writer's own exact receipt
   append is expected, not permission to ignore unrelated relevant events.
7. Call `verify_prepared_acquisition(...)` with the original bound refresh/health
   evidence, actual acquisition timestamp and refreshed overlap inventory. Any
   change to receipt-bound evidence requires a fresh preparation.
8. The fresh broker evaluation at acquisition proves the writer is still eligible;
   receipt verification remains bound to the **original issuing decision**. A later
   evaluation timestamp must never silently replace `authorization_evaluated_at`.
9. Acquire the exact lease via a separately verified concurrency-safe adapter.
   Only after verified acquisition emit `prepared.acquisition_event_refs()`.
10. Perform only the authorized bounded operation; exact read-back, close events,
    own-lease release and own-session completion remain required.

An ACTIVE lifecycle row is not permission. The canonical guard currently rejects
`ACTIVE_READ_ONLY` as a proposed writer. Any lifecycle transition must be explicit,
versioned, evidence-backed and made by the appropriate owner; never reinterpret an
old row for convenience.

## Content-address law

The issuer computes:

```text
receipt_id = "WAZ-" + SHA256(canonical claims excluding receipt_id)[0:24]
```

The operational gate and offline auditor now recompute that identity. A receipt
whose JSON shape is valid but whose content-address does not match is rejected.

Changing `authorization_evaluated_at` and then recomputing a self-consistent
`receipt_id` is also insufficient when the original decision is available: the
exact issuing evaluation timestamp must still match.

## Non-claims and release gates

- Shape validation is not broker authorization or a cryptographic signature.
- Content-address verification is tamper detection for canonical claims; it is not
  a secret-key signature or external capability.
- A positive preparation is not an acquired lease or an atomic compare-and-set.
- Read-then-write still has a TOCTOU race unless the provider adapter prevents it.
- This change does not route the native scheduled agent through these functions.
- A real scheduler adapter integration and scheduled canary remain release gates.
- No historical sessions/leases/receipts are repaired by this code.
- No source cursor or canonical application semantics are changed.
- A process killed before closure still requires independent detection and an
  authorized reconciliation plan; a `finally` block is not a durability guarantee.

## Tests

Run the repository suite, not just a helper or copied function body:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

Tests cover exact payloads, duplicate JSON fields, real broker/issuer/auditor
round-trips, actual CLI subprocesses, denied external intent, read-only sessions,
invalid health, overlap, changed scope/main/watermark, expired receipt/lease,
future acquisition, tampered content-addresses, and altered authorization
evaluation timestamps with recomputed IDs. Synthetic fixtures contain no private
source snapshots.

Before deployment require exact PR-head/merge-ref CI, independent code review,
provider atomicity and hard-stop tests, adapter wiring, rollback and a scheduled
canary. A green unit suite alone does not certify production or explain a scheduler
error.
