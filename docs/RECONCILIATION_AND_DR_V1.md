# UE-Xchanges-OS — Reconciliation Planner & Disaster Recovery v1

## Purpose

Turn reliability findings into reviewable repair work and make zero-context recovery measurable.

This release **does not repair anything automatically**. It produces three artifacts:

1. deterministic `ReconciliationPlan` objects;
2. a content-addressed `RecoveryManifest`;
3. a measured `RecoveryDrillReport`.

All three are diagnostics/evidence. None is opportunity/application authority.

## Reconciliation plans

`src/uexchanges/reconciliation_planner.py` maps each Control Plane Health or Recovery Verifier finding to a bounded repair plan.

Every plan includes:

- deterministic `plan_id`;
- source finding/code and exact subject ID;
- repair operation and surface;
- risk level;
- exact lease scope required before repair;
- preconditions;
- evidence requirements;
- mandatory read-back checks.

Hard invariants:

```text
auto_execute = false
canonical_domain_mutation = false
```

The planning layer therefore cannot mutate Opportunities, Applications, receipts or any other canonical domain state.

Representative mappings:

```text
expired ACTIVE lease row
→ RECONCILE_LEASE_STATUS
→ dedicated Work_Leases:<lease-id> scope

owner missing
→ RECONSTRUCT_LEASE_OWNERSHIP
→ Work_Leases + Agent_Sessions evidence

stale Context_Registry
→ REFRESH_CONTEXT_REGISTRY
→ exact context row lease

stale projection
→ REBUILD_DERIVED_PROJECTION
→ derived projection scope only

missing recovery artifact
→ RESTORE_RECOVERY_ARTIFACT
→ exact GitHub recovery path
```

A later executor may consume these plans only after its own BootstrapGuard PASS, fresh pre-lease scan and dedicated write contract.

## Recovery manifest

`src/uexchanges/recovery_manifest.py` creates a value-safe, content-addressed recovery inventory.

It records:

- current GitHub main SHA;
- latest source Event Bus watermark used for the bundle;
- bootstrap manifest version;
- RuntimeGraph Command Center ref + watermark;
- required public artifact path + SHA-256 + role;
- private control-plane source availability + non-sensitive watermark;
- `bundle_hash` over the content identity.

`generated_at` is intentionally excluded from the bundle identity. The same authority/material recovered an hour later has the same bundle hash; a changed artifact/event/main/private source state changes it.

Never put applicant answers, passwords, cookies, OTPs, health data, addresses, identity numbers or provider secrets in a recovery manifest.

## Measured recovery drill

`src/uexchanges/recovery_drill.py` records facts, not aspirations.

Inputs include:

- start/end timestamps;
- one verified Recovery Manifest;
- source Event Bus ID inventory for the drill window;
- Event Bus IDs actually reconstructed;
- required recovery-step outcomes;
- Recovery Verifier categorical result;
- explicit objectives.

Derived facts:

```text
RTO seconds = completed_at - started_at
missing_event_ids = source - recovered
event_loss_count = len(missing_event_ids)
measured_rpo_zero = event_loss_count == 0
```

The caller cannot pass `measured_rpo_zero=true`. It is derived.

A drill without a source event inventory is invalid and cannot claim RPO.

Default objectives remain targets until measured:

```text
max RTO:       300 seconds
max event loss: 0
```

Possible statuses:

- `PASS`
- `FAIL_RTO`
- `FAIL_RPO`
- `FAIL_RECOVERY`
- `FAIL_STEPS`

A `DEGRADED` Recovery Verifier result never passes the drill even if RTO/event counts happen to fit the target.

## Operational recovery drill

Professional zero-context drill:

1. record `started_at`;
2. record source Event Bus ID inventory up to the chosen watermark;
3. resolve current GitHub main;
4. load bootstrap manifest and required public artifacts;
5. restore/reach required private control-plane sources;
6. reconstruct unexpired effective leases;
7. reach/rebuild RuntimeGraph Command Center;
8. reconstruct Event Bus IDs and current execution frontier;
9. run Recovery Verifier;
10. build/verify Recovery Manifest;
11. record `completed_at`;
12. build Recovery Drill Report;
13. persist the report as evidence;
14. if failed, convert findings to Reconciliation Plans under a separate repair workflow.

## Failure handling

A failed drill does **not** authorise direct repairs.

```text
DRILL FAIL
→ findings
→ deterministic ReconciliationPlan(s)
→ review authoritative evidence
→ new bootstrapped writer session
→ dedicated repair lease
→ bounded repair
→ exact read-back
→ Event Bus repair event
→ rerun drill
```

## CLIs

Build a manifest from an offline JSON snapshot:

```bash
PYTHONPATH=src python scripts/build_recovery_manifest.py manifest-input.json --out recovery-manifest.json
```

Record a drill:

```bash
PYTHONPATH=src python scripts/run_recovery_drill.py drill-input.json --out drill-report.json --fail-on-objective
```

Both commands are offline and perform no provider/network writes.

## Separation from canonical truth

- repair plan = proposed bounded action;
- recovery manifest = inventory/checksum;
- drill report = measured recovery evidence;
- Drive/official evidence = operational/domain truth.

No score/hash/report is allowed to invent or overwrite application state.
