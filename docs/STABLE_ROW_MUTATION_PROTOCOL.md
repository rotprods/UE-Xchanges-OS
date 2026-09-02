# UE-Xchanges-OS — Stable Row Mutation Protocol v1

## Purpose

Eliminate an entire class of control-plane corruption caused by treating cached spreadsheet row/column positions as identity.

The protocol is provider-agnostic and **plan-only**. It does not call Google Sheets or mutate any table itself.

## Identity law

```text
ROW NUMBER != IDENTITY
COLUMN LETTER != FIELD IDENTITY

identity = table + stable_id_header + exact stable_id
field     = exact header name
```

Examples:

```text
Agent_Sessions + "Session ID" + SES-...
Work_Leases    + "Lease ID"   + LSE-...
Agent_Inbox    + "Message ID" + MSG-...
```

A cached statement such as `row 81` or `K:O` is only an observation from one read. It is never a durable write target by itself.

## Two-read optimistic protocol

Every critical row mutation follows:

```text
READ #1 full bounded table/header set
→ resolve exact stable ID uniquely
→ fingerprint canonical header→value map
→ refresh main/leases/events as required by writer contract
→ READ #2 same bounded table/header set
→ resolve exact stable ID uniquely again
→ compare full row fingerprint
→ remap target columns by current header names
→ verify expected old values
→ emit StableRowMutationPlan
→ provider performs only listed cell mutations
→ READ #3
→ resolve stable ID again
→ verify exact after-row fingerprint
→ append Event Bus evidence
```

If the physical row moved between reads but the canonical row map is unchanged, the plan follows the stable ID to the new row.

If columns reorder but the header set and values are unchanged, the plan recalculates physical columns from the second header layout.

If row content changes between reads, the plan aborts with `CONCURRENT_ROW_CHANGE`.

## Hard failures

The resolver is fail-closed for:

- table mismatch;
- duplicate or empty headers;
- missing stable-ID header;
- stable ID not found;
- duplicate stable ID;
- unknown update header;
- attempt to mutate the stable ID itself;
- changed full-row fingerprint between reads;
- caller expected-fingerprint mismatch;
- expected-old-value mismatch;
- read-back fingerprint mismatch;
- unsupported/non-deterministic cell values.

Duplicate IDs are never resolved by “first row wins”.

## Fingerprints

### Row fingerprint

SHA-256 over canonical JSON of the full `header → value` map with sorted keys.

This intentionally ignores physical column order while detecting actual value changes.

### Header-set fingerprint

SHA-256 over sorted header names.

A changed header set blocks the plan and requires schema re-read/reconciliation.

### Header-layout fingerprint

SHA-256 over headers in physical order.

A layout change is recorded but does not block if the header set and row values remain identical.

### Mutation key

```text
SRM-SHA256(
  stable row identity
  + before row fingerprint
  + canonical requested updates
)
```

The key supports deterministic retry/audit. It is not a lease or credential.

## Expected-old-values

For high-risk control-plane updates, callers should bind fields they expect to change from a known state.

Example:

```text
stable ID: LSE-X
expected:
  Status = ACTIVE
  Last Event ID = EVT-ACQUIRE
updates:
  Status = RELEASED
  Last Event ID = EVT-RELEASE
```

If either expected value changed, abort and re-evaluate authority instead of overwriting a concurrent writer.

## Stable ID immutability

The stable-ID field cannot be updated by this protocol.

Changing an entity identity is a migration operation requiring a separate versioned contract.

## Read-back law

A provider response such as “batch update succeeded” is insufficient.

The mutation is verified only when a new snapshot resolves the same stable ID and its full canonical row fingerprint equals the planned `after_row_fingerprint`.

The row may move again before read-back; stable-ID resolution must follow it.

## Provider adapter responsibilities

A future Google Sheets adapter must:

1. fetch headers + bounded table rows;
2. construct `TableSnapshot`;
3. perform two independent reads;
4. call `prepare_stable_row_mutation`;
5. translate only `CellMutation.a1/new_value` to provider requests;
6. avoid any extra cells;
7. fetch a new snapshot;
8. call `verify_stable_row_readback`;
9. append mutation/readback events.

The core module never receives Google credentials and never executes provider writes.

## Required adoption targets

Priority order:

1. `Agent_Sessions`;
2. `Work_Leases`;
3. `Agent_Inbox`;
4. `Context_Registry`;
5. RuntimeGraph derived projection rows with stable action/application IDs;
6. canonical domain tables only after dedicated review and stronger authority binding.

## Incident that motivated the invariant

During the 2026-09-02 reliability wave, a closure operation used cached row indexes. Concurrent appends shifted physical rows and caused:

- one released session/lease to remain textually ACTIVE;
- an unrelated active Semantic Runtime Bridge lease to receive false release metadata.

Both were recovered from stable IDs + Event Bus + GitHub evidence under dedicated repair leases.

The durable lesson is stronger than “be careful with indexes”:

> **Cached physical coordinates are forbidden as identity for critical control-plane mutation.**

## Capability boundary

Stable Row Mutation Protocol v1:

```text
resolve identity      YES
plan exact cells      YES
optimistic conflict   YES
read-back verify      YES
provider write        NO
lease acquisition     NO
domain authority      NO
external side effect  NO
```

WriterAuthorization/BootstrapGuard still decide coordination eligibility. Reconciliation Planner still decides what repair is proposed. Provider-specific code performs a write only under its own lease and authority.
