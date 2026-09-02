# Writer Authorization Receipt v1

## Objective

Make writer authorization **auditable per lease**.

Bootstrap v1 proves a writer loaded the required context. `WriterAuthorizationDecision`
proves the coordination broker evaluated bootstrap, health/SLO evidence, intent and
lease overlap. The missing link was durable proof that **one exact lease acquisition**
was the lease that received the positive decision.

Writer Authorization Receipt v1 adds that link without granting any new operational
capability.

```text
SESSION_STARTED
→ BOOTSTRAP_CONTEXT_LOADED
→ refresh current main + EventBus + unexpired leases + health
→ authorize_writer(...)
→ WriterAuthorizationDecision(ALLOWED)
→ WRITER_AUTHORIZATION_GRANTED(receipt)
→ LEASE_ACQUIRED(receipt_id + decision_digest)
→ bounded write
```

After rollout, a post-contract write lease without exactly one valid receipt is a
coordination defect.

## Authority boundary

A receipt means only:

> the coordination broker allowed this exact proposed write lease at acquisition time.

It does **not** mean:

- domain truth may change;
- an application may be submitted;
- a payment may be executed;
- credentials may be entered;
- a browser/provider capability exists;
- a lease was actually acquired.

The receipt always serializes:

```text
coordination_allowed = true
domain_authority      = false
external_capability   = false
```

Browser/Form capability tokens remain separate. Domain/application authorization
remains governed by the domain/runtime contracts and evidence gates.

## Exact binding

One receipt binds:

- `session_id`
- `agent_id`
- `context_id`
- bootstrap `manifest_version`
- current `observed_main_sha`
- `WriteIntent`
- exact `proposed_lease_id`
- SHA-256 of the **exact scope string**
- `WriterAuthorizationDecision.decision_digest`
- authorization evaluation timestamp
- SHA-256 of the exact `ControlPlaneHealthReport`
- health generation timestamp
- pre-lease EventBus watermark
- pre-lease lease-scan timestamp
- explicit overlap inventory
- repair-plan ID when applicable
- issue and expiry timestamps

Changing any bound identity/scope/current-main/health/decision evidence requires a
new receipt.

## Why no HMAC/signing key?

This receipt is an audit object, not an invocation capability. It is intended to be
persisted inside the already controlled append-only Event Bus and tied to the
broker's deterministic decision digest.

Introducing a secret signing key here would create a key-distribution/rotation
problem without increasing the authority of the receipt. Security-sensitive
browser/Form operations retain their independent HMAC capability layer.

If the Event Bus later becomes cryptographically hash-chained, these receipts gain
that tamper-evidence automatically without changing their contract.

## Receipt lifetime

Default authorization TTL: **120 seconds**.
Maximum supported TTL: **300 seconds**.

TTL controls the window in which the proposed lease may be acquired. Once the lease
has been legitimately acquired within the window, later historical audit does not
invalidate that acquisition merely because the receipt is now old.

Therefore audit checks:

```text
receipt.issued_at <= lease.acquired_at <= receipt.expires_at
```

not `now <= receipt.expires_at`.

## EventBus contract

Before the provider/connector writes the lease row, append:

```text
Event Type:  WRITER_AUTHORIZATION_GRANTED
Entity Type: writer_authorization_receipt
Entity ID:   <WAZ-...>
State Before: AUTHORIZATION_EVALUATED
State After:  AUTHORIZED_FOR_EXACT_LEASE_ACQUISITION
Payload JSON: receipt.as_dict()
```

The subsequent `LEASE_ACQUIRED` event should carry at minimum:

```text
authorization_receipt_id
authorization_decision_digest
writer_authorization_contract = 1.0.0
```

This relationship is deliberately one receipt → one proposed lease.

## Verification modes

### Full verification

`verify_writer_authorization_receipt(...)` receives:

- receipt;
- original `WriterAuthorizationDecision`;
- session;
- lease;
- pre-lease refresh;
- health report;
- manifest version;
- observed main SHA.

It fails closed on identity, intent, scope, main, health, watermark, scan time,
repair-plan, overlap inventory, decision digest or acquisition-window mismatch.

### Structural historical audit

`audit_lease_receipt_bindings(...)` requires only lease snapshots + persisted receipt
objects. It detects:

- post-contract lease with no receipt;
- duplicate receipts for one lease;
- session/agent/context mismatch;
- scope mismatch;
- receipt issued after acquisition;
- receipt expired before acquisition.

It does not pretend to reconstruct a historical health report/decision that was not
provided. Full verification remains the stronger check.

The CLI:

```bash
python scripts/audit_writer_authorization_receipts.py snapshot.json --fail-on-findings
```

is offline/read-only.

## Rollout strategy

Do not retroactively condemn leases created before the receipt contract existed.
Every structural audit receives an explicit `effective_at`.

Recommended rollout:

1. release the receipt core/schema/auditor;
2. integrate receipt issuance into RG2.2 dispatcher lease acquisition;
3. integrate provider/form writers;
4. integrate RuntimeGraph action writers and projection writers;
5. integrate canonical-domain writers;
6. make Control Plane Health report `LEASE_WITHOUT_WRITER_AUTHORIZATION` for all
   post-effective leases;
7. only then consider CI/runtime hard requirements for every writer family.

`EXTERNAL_SIDE_EFFECT` remains denied by generic WriterAuthorization and cannot be
made valid merely by producing a receipt.

## Non-claims

This v1 core:

- does not acquire a lease;
- does not modify RuntimeGraph;
- does not mutate Drive/provider data;
- does not submit forms;
- does not activate external PREFILL;
- does not pay or authenticate;
- does not auto-remediate missing receipts.

It closes one coordination-proof gap only: **allowed decision → exact lease**.
