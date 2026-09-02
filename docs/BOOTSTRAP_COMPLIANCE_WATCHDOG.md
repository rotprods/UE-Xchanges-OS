# UE-Xchanges-OS — Bootstrap Compliance Watchdog v1

## Objective

Continuously turn BootstrapGuard findings into stable, deduplicated operational alerts without giving the detector authority to mutate sessions, leases, RuntimeGraph or domain truth.

```text
Agent_Sessions + BOOTSTRAP_CONTEXT_LOADED + pre-lease refresh + Work_Leases
                                ↓
                         BootstrapGuard
                                ↓
                     Compliance findings
                                ↓
                    Bootstrap Watchdog
                                ↓
             NEW / UPDATED / PERSISTING / RESOLVED
```

## Separation of powers

The watchdog is **observation-only**.

It may:
- classify a finding;
- assign severity;
- derive a deterministic subject/fingerprint;
- suppress repeat notifications;
- report resolution;
- recommend a remediation action.

It may not:
- alter `Agent_Sessions`;
- release/expire/take over a lease;
- grant a lease;
- execute RuntimeGraph actions;
- change opportunities/applications;
- use browser/form/payment/Submit capabilities.

Auto-remediation, if ever added, is a separate capability and separate review surface.

## Severity model

### CRITICAL
Active authority is structurally unsafe, for example:
- missing bootstrap ACK;
- session ID reuse;
- ACK after lease acquisition;
- missing pre-lease refresh;
- owner/context identity mismatch;
- lease scope empty;
- concurrency scan happened after acquisition.

Recommended response: stop writes and reconstruct authority before continuing.

### HIGH
Authority may be stale or incomplete:
- stale manifest version;
- current-main mismatch in pre-lease refresh;
- missing read-set/watermark proof;
- stale pre-lease scan.

Recommended response: remain read-only and refresh/rebootstrap/acquire a new fence as applicable.

### WARNING
Usually coordination debt rather than active authority:
- lease row not ACTIVE;
- expired lease still appearing as ACTIVE in a snapshot.

### INFO
- compliant state;
- historical `LEGACY_PRE_CONTRACT` archaeology.

INFO/legacy findings do not open watchdog alerts.

## Alert identity

Each current violation is grouped by stable subject key:

```text
<subject_type>:<subject_id>
```

Its fingerprint is:

```text
SHA256(subject_type | subject_id | session_id | sorted(reason_codes))
```

This produces transitions:

- `NEW` — subject was not alerting previously;
- `UPDATED` — same subject, changed reason fingerprint/severity;
- `PERSISTING` — unchanged violation; no repeat notification;
- `RESOLVED` — previous alert is absent from current violations.

By default only NEW/UPDATED HIGH+ and resolved HIGH+ alerts notify.

## Pipeline

The current provider-neutral pipeline is intentionally split:

```bash
PYTHONPATH=src python scripts/audit_bootstrap_compliance.py control-plane.json \
  > bootstrap-audit.json

PYTHONPATH=src python scripts/run_bootstrap_watchdog.py bootstrap-audit.json \
  --state .runtime/bootstrap-watchdog-state.json \
  --write-state .runtime/bootstrap-watchdog-state.json \
  --fail-on-high
```

The first stage decides compliance. The second stage decides operational alert transition/severity. Neither reads network state directly.

A future Drive adapter may construct `control-plane.json`, but it must not reimplement authorization logic.

## Watchdog state

Only current open-alert state needs persistence:

```json
{
  "lease:LSE-...": {
    "fingerprint": "<sha256>",
    "severity": "CRITICAL"
  }
}
```

No cookies, tokens, applicant values, form answers or other secrets belong in watchdog state.

## Recommended actions

Examples:

- session reuse → `STOP_WRITES_CREATE_FRESH_SESSION_AND_RECONCILE_DUPLICATE_SESSION_ID`
- identity/fencing mismatch → `STOP_WRITES_RECONCILE_IDENTITY_AND_FENCING`
- bootstrap failure → `REMAIN_READ_ONLY_REPEAT_MANIFEST_BOOTSTRAP_AND_EMIT_ACK`
- stale/missing prelease refresh → `DO_NOT_USE_LEASE_REFRESH_MAIN_LEASES_EVENT_TAIL_AND_ACQUIRE_NEW_FENCE`
- expired/stale lease → `RECONCILE_STALE_LEASE_ROW_DO_NOT_TREAT_AS_LIVE_AUTHORITY`

Recommendations are not self-executing permissions.

## Deployment sequence

1. release watchdog pure core + CLI;
2. create live Drive snapshot adapter under a separate lease;
3. project current alerts into a dedicated control-plane/watchdog surface;
4. run on each dispatcher/control-plane cycle;
5. notify only on NEW/UPDATED/RESOLVED HIGH+;
6. route unresolved repeated CRITICAL findings to Dead Letters/human review;
7. add central guarded lease service so many violations become technically impossible.

## Acceptance

- deterministic output;
- same violation does not notify repeatedly;
- changed violation produces UPDATED;
- high/critical resolution is surfaced once;
- legacy history is not treated as current incident;
- detector has zero remediation side effects.
