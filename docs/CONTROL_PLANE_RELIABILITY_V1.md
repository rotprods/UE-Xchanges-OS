# UE-Xchanges-OS — Control Plane Reliability v1

## Purpose

Make coordination/recovery defects observable and machine-checkable without creating a second source of domain truth.

This layer is **observation-only**. It never rewrites sessions, leases, opportunities, applications, receipts, RuntimeGraph projections or provider/browser state. Repair is a separately leased action after evidence review.

## Authority

Reliability findings diagnose system state; they do not establish opportunity/application truth.

```text
Official/organiser/receipt evidence
→ private Drive CRM + Event Bus
→ current GitHub contracts/code
→ RuntimeGraph derived state
→ health/recovery diagnostics
→ UI projections/chat
```

## Modules

### `src/uexchanges/control_plane_health.py`

Deterministically evaluates:

- duplicate/reused Session IDs;
- active-session heartbeat staleness;
- effective lease state;
- expired rows still labelled `ACTIVE`;
- active lease whose owner session is missing/closed;
- lease agent/context/scope integrity;
- active-lease heartbeat age;
- `Context_Registry` freshness;
- derived projection freshness;
- bootstrap non-compliance count;
- dead-letter count.

An `ACTIVE` string is **not** treated as an eternal lock. Effective state is computed from row status + owner session + expiry:

```text
ACTIVE + live owner + before expiry  → ACTIVE
ACTIVE + expired                     → EXPIRED_STALE_ROW
ACTIVE + missing owner               → ORPHANED_OWNER_MISSING
ACTIVE + closed owner                → ORPHANED_OWNER_CLOSED
non-ACTIVE row                       → RELEASED
```

The auditor never silently changes the row.

## SLOs

Default SLOs:

| SLO | Target |
|---|---|
| bootstrap compliance | 0 non-compliant active writers |
| session identity uniqueness | 0 reused Session IDs |
| lease fencing integrity | 0 orphaned/mismatched active leases |
| lease-row hygiene | 0 expired rows still marked ACTIVE |
| context freshness | 0 ACTIVE Context_Registry rows older than 24h |
| projection freshness | 0 monitored projections older than 30m |
| dead-letter budget | 0 unresolved dead letters |

Thresholds are configurable through `HealthPolicy`; changing them is a versioned policy decision, not an ad-hoc runtime tweak.

### Overall status

```text
CRITICAL/ERROR finding → RED
WARNING only           → AMBER
no findings            → GREEN
```

## Disaster recovery verification

`src/uexchanges/recovery_verifier.py` validates whether a zero-context successor can reconstruct the system without chat memory.

It checks:

1. current GitHub main exists and is a valid SHA;
2. an Event Bus watermark exists;
3. every required public bootstrap/recovery artifact exists;
4. bootstrap manifest read-set contains the required artifacts;
5. private control-plane sources are reachable;
6. RuntimeGraph Command Center is available/rebuildable;
7. watermarked snapshots are not being mistaken for current state;
8. stable documents do not embed volatile state.

### Recovery state

```text
RECOVERABLE      no warning/error/critical findings
DEGRADED         only INFO/WARNING/ERROR findings; authority is still reconstructible
NOT_RECOVERABLE  one or more CRITICAL recovery prerequisites missing
```

The numerical score is diagnostic only. It never overrides the categorical status or authority hierarchy.

## Stable-document rule

`MEMORY.md`, `goal.md`, `AGENTS.md` and architecture contracts should contain invariants, not current counts/frontiers.

Current counts/status belong in watermarked artifacts/private authority:

- Drive CRM/Event Bus;
- `STATE.md` / `HANDOFF.md` / current checkpoint;
- active `LIVE-STATE-OVERRIDE.json`;
- RuntimeGraph Command Center;
- `agent_context/**` snapshots, explicitly marked derived.

This release removes the historic `Current canonical scale` block from `goal.md` and replaces it with a live-state pointer.

## CLI

The audit command consumes an exported JSON snapshot and performs no provider/network writes.

```bash
python scripts/audit_control_plane_health.py health snapshot.json
python scripts/audit_control_plane_health.py recovery recovery.json
```

Use `--fail-on-degraded` in CI/recovery drills when a non-green/non-recoverable report should fail the job.

## Expected current classes of finding

This evaluator is specifically designed to expose patterns already observed in UE-Xchanges-OS:

- old leases left textually `ACTIVE` after expiry/takeover;
- owner session already `COMPLETED` while the old lease row is not reconciled;
- `Context_Registry` watermark older than current runtime releases;
- Command Center/recovery Markdown snapshots lagging newer Event Bus/main;
- volatile numeric state copied into stable contracts.

These are coordination/recovery defects, not automatic evidence that application state is wrong.

## Repair protocol

For each finding:

```text
DETECT
→ identify authoritative evidence
→ acquire a dedicated repair lease
→ append repair/reconciliation event
→ mutate only the affected projection/control row
→ read back
→ rerun audit
```

No auto-remediation in v1.

## Disaster recovery drill

A professional drill should periodically test:

1. start with no chat context;
2. resolve current `main`;
3. load bootstrap manifest + required public artifacts;
4. reach Drive Context Registry / Sessions / Leases / Event Bus;
5. reach or deterministically rebuild RuntimeGraph Command Center;
6. establish latest event watermark;
7. compute effective active leases;
8. reconstruct current Human/Agent frontiers from authority;
9. run `recovery` audit;
10. record measured RTO and last authoritative event recovered.

Suggested target:

```text
RPO: 0 acknowledged material Event Bus events lost
RTO: <= 5 minutes for zero-context control-plane reconstruction
```

These targets must be measured during a real drill before they are claimed as achieved.

## Next integrations

After v1 is green:

1. feed health findings into the observation-only Bootstrap Compliance Watchdog;
2. expose health summary in RuntimeGraph Command Center without making it authority;
3. require `lease_fencing_integrity` PASS before generic writer lease brokers grant claims;
4. run a scheduled recovery drill/audit;
5. only then consider bounded auto-reconciliation for stale *derived* rows, never canonical domain truth.
