# UE-Xchanges-OS — Writer Authorization & Reliability Watchdog v1

## Purpose

Make coordination authorization fail-closed across writer types and convert raw reliability findings into deduplicated, plan-linked alerts.

Neither component is domain authority.

## Writer Authorization Broker

`src/uexchanges/writer_authorization.py` composes:

```text
BootstrapGuard
× fresh ControlPlaneHealthReport
× intent-specific SLOs
× exact subject health findings
× explicit unexpired-overlap inventory
→ coordination decision
```

The broker does **not** call Drive, acquire a lease, send an email, touch a form or mutate a domain entity. It only decides whether the coordination prerequisites are sufficient to attempt the separately controlled lease acquisition.

### Intent classes

- `VERSIONED_CODE`
- `CONTROL_PLANE_REPAIR`
- `DERIVED_PROJECTION`
- `CANONICAL_DOMAIN`
- `EXTERNAL_SIDE_EFFECT`

`EXTERNAL_SIDE_EFFECT` is always denied by this broker. Authentication/PREFILL/Submit/payment require their own explicit capability contracts.

### Repair rule

`CONTROL_PLANE_REPAIR` requires a deterministic `RPL-<16hex>` plan from Reconciliation Planner v1. A free-form request such as “fix stale rows” is not sufficient.

### Required SLOs

Normal versioned-code / derived-projection writes require:

- bootstrap compliance;
- Session ID uniqueness;
- lease fencing integrity.

Canonical-domain writes additionally require context freshness.

Repairs intentionally may target a currently unhealthy control-plane condition, so they do not require the global health SLO set. They still require:

- BootstrapGuard PASS;
- current/fresh health report;
- no overlapping unexpired repair lease;
- valid reconciliation plan ID;
- no target-session/lease blocker that invalidates the repair writer itself.

### Scope conflicts

The broker does not parse arbitrary human scope strings heuristically. Its caller must provide `overlapping_unexpired_lease_ids` from a stable-ID/scope resolver. Non-empty overlap inventory denies the decision.

This avoids treating brittle substring matching as lock semantics.

### Output law

A positive decision states only:

```text
coordination_allowed = true
```

It explicitly returns:

```text
domain_authority = false
external_capability = false
```

Its `decision_digest` is an audit fingerprint, not a credential or lease token.

## Reliability Watchdog

`src/uexchanges/reliability_watchdog.py` consumes Control Plane Health and optional Recovery Verifier findings.

Each active finding becomes a stable alert key:

```text
RAL-SHA256(source_kind | code | subject)[0:20]
```

and is linked to its deterministic Reconciliation Plan.

### Alert phases

- `NEW` — finding appears for first time / was previously resolved;
- `UPDATED` — same alert identity, changed severity/detail/repair fingerprint;
- `PERSISTING` — identical finding remains active; occurrence counter increments;
- `RESOLVED` — prior active finding absent from current scan.

The watchdog therefore suppresses notification spam while preserving persistence and material changes.

### Safety

```text
auto_remediation = false
```

A watchdog alert may generate/point to a repair plan, but cannot execute it.

## Recommended operational chain

```text
bootstrap watchdog
→ control-plane health/recovery scan
→ reliability watchdog
→ reconciliation plans
→ human/system review
→ writer authorization broker
→ dedicated lease acquisition
→ bounded repair/execution
→ exact read-back
→ Event Bus
→ next scan
```

## Current integration strategy

V1 is intentionally introduced as pure code first. Existing RuntimeGraph/dispatcher/provider workers can adopt it incrementally without silently changing their capability ceilings.

Suggested adoption order:

1. control-plane/recovery writers;
2. projection writers;
3. generic GitHub/versioned-code writers;
4. canonical-domain writers;
5. keep external side effects on their separate Form/Browser/Human capability system.

## Incident learned during implementation

A live closure accidentally wrote status columns by assumed spreadsheet row index, which produced:

- a stale `ACTIVE` session/lease after a successful release;
- a false release on an unrelated Semantic Runtime Bridge lease.

The incident was reconciled from stable IDs + Event Bus + GitHub evidence under dedicated repair fences.

This reinforces two laws:

```text
stable-ID row resolution before mutation
exact-ID read-back after mutation
```

Generic writer integrations should never use a cached row number as identity.
