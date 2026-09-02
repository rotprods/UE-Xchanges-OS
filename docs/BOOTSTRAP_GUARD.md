# UE-Xchanges-OS — BootstrapGuard v1

## Purpose

`AGENTS.md` and `agent_context/bootstrap_manifest.json` define the mandatory writer bootstrap contract. `BootstrapGuard` converts that contract from prose/event convention into a reusable fail-closed decision engine.

It answers one narrow question:

> Is this exact session allowed to acquire/use this exact write lease under the current bootstrap contract?

It does **not** grant domain, payment, browser or submission authority.

## Authorization chain

```text
fresh Session ID
→ SESSION_STARTED
→ BOOTSTRAP_CONTEXT_LOADED
→ fresh current-main / lease / EventBus refresh
→ BootstrapGuard ALLOW
→ LEASE_ACQUIRED
→ bounded writer capability
```

Any missing or inconsistent link returns `DENY` with stable reason codes.

## Two freshness layers

Bootstrap and pre-lease freshness are deliberately separate.

### Bootstrap ACK

Proves the agent loaded the required context under the current manifest version:

- manifest version;
- observed main SHA at bootstrap time;
- context ID;
- public read-set proof;
- private Event Bus watermark;
- bootstrap lease-scan time;
- agent/session identity.

### Pre-lease refresh

Proves the writer re-read concurrency and current code immediately before acquiring a lease:

- current main SHA;
- fresh lease scan timestamp;
- current private Event Bus watermark.

An unrelated Git commit after bootstrap does not force a full re-read of every context document when the manifest version is unchanged. It **does** require the pre-lease current-main refresh to observe the new SHA.

A manifest version change requires a new bootstrap ACK.

## Fail-closed reason codes

Representative codes:

- `MISSING_SESSION`
- `SESSION_NOT_ACTIVE`
- `SESSION_REUSED`
- `MISSING_BOOTSTRAP_ACK`
- `ACK_BEFORE_SESSION`
- `ACK_AFTER_LEASE`
- `ACK_IDENTITY_MISMATCH`
- `ACK_CONTEXT_MISMATCH`
- `STALE_MANIFEST_VERSION`
- `ACK_READSET_TIMING_INVALID`
- `MISSING_PRELEASE_REFRESH`
- `PRELEASE_MAIN_SHA_STALE`
- `LEASE_SCAN_BEFORE_ACK`
- `LEASE_SCAN_AFTER_ACQUIRE`
- `LEASE_SCAN_STALE`
- `LEASE_OWNER_MISMATCH`
- `LEASE_CONTEXT_MISMATCH`
- `LEASE_SCOPE_EMPTY`
- `LEASE_NOT_ACTIVE`
- `LEASE_EXPIRED`

The reason-code surface is intended for audit dashboards, DLQ routing and future RuntimeGraph writer integration.

## Pure core

`src/uexchanges/bootstrap_guard.py` has no connector, browser, network or database dependency.

Inputs are typed snapshots:

- `BootstrapPolicy`
- `SessionSnapshot`
- `BootstrapAckSnapshot`
- `PreLeaseRefresh`
- `LeaseSnapshot`

Output:

```json
{
  "allowed": false,
  "codes": ["MISSING_BOOTSTRAP_ACK"]
}
```

This makes the same policy reusable by:

- RuntimeGraph Agent Executor;
- RuntimeGraph dispatcher/self-heal writer;
- Provider/Form capture writer;
- Browser capability writers;
- continuity/recovery writers;
- future lease-acquisition service.

## Compliance auditor

`scripts/audit_bootstrap_compliance.py` consumes a provider-neutral JSON snapshot.

Example shape:

```json
{
  "now": "2026-09-02T09:00:00+02:00",
  "policy": {
    "manifest_version": "1.0.0",
    "current_main_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "context_id": "CTX-UEX-GLOBAL-EXPANSION-INCOME-V1",
    "effective_at": "2026-09-02T07:11:00+02:00"
  },
  "sessions": [],
  "acks": [],
  "leases": [],
  "prelease_refreshes": {}
}
```

Run:

```bash
PYTHONPATH=src python scripts/audit_bootstrap_compliance.py snapshot.json
```

CI/watchdog mode:

```bash
PYTHONPATH=src python scripts/audit_bootstrap_compliance.py snapshot.json --fail-on-violation
```

Exit codes:

- `0`: audit completed; and in fail mode no violations;
- `2`: compliance violation in `--fail-on-violation` mode;
- `3`: malformed/unreadable snapshot.

## Historical semantics

Bootstrap v1 became mandatory at its release boundary. Closed leases acquired before that boundary are labelled `LEGACY_PRE_CONTRACT`; they are not retroactively treated as malicious writes.

The active watchdog concentrates on current sessions and active leases.

## Integration rule

Do not copy BootstrapGuard logic into each writer.

Future integration should call the shared core before a lease/action capability becomes writable. A writer denied by the guard must remain read-only and emit/route a protocol violation rather than trying to self-authorize.

## Next integration phases

1. release pure Guard + auditor;
2. wire Guard into the RG2.3 Agent Executor after refreshing its code lease;
3. wire into RG2.2 dispatcher/projection writers;
4. wire into Provider Capture/Form capability writers;
5. centralize lease issuance behind a guarded lease-acquisition service;
6. add an hourly compliance watchdog over active sessions/leases;
7. route repeat protocol violations to Dead Letters / human escalation.

## Non-authority

Bootstrap compliance never means:

- opportunity eligibility passed;
- form fields may be filled;
- external PREFILL is certified;
- Submit is authorized;
- payment is authorized;
- a receipt exists.

Those remain separate capability/evidence gates.
