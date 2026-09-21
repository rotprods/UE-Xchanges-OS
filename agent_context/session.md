# UE-Xchanges-OS — Session / Lease Recovery Law

Seal: `2026-09-21T21:59:00+02:00`

> This public file does not attempt to mirror live session/lease ownership. Read private `Agent_Sessions`, currently-unexpired `Work_Leases` and EventBus on every cold start and immediately before authorization/mutation.

## Current law

```text
NEW UNIQUE SESSION
→ SESSION_STARTED
→ bootstrap_manifest current version
→ BOOTSTRAP_CONTEXT_LOADED
→ refresh main/EventBus/unexpired leases/Agent_Inbox
→ resolve complete global barrier state
→ bounded health + WriterAuthorization
→ barrier-bound receipt
→ exact narrow lease
→ bounded mutation
→ exact readback/event
→ release
→ SESSION_COMPLETED/HANDOFF_READY
```

Historical Session IDs, WAZ receipts and leases are evidence only and are never resumable write identities.

## 2026-09-21 repair note

A cross-row session metadata overwrite was detected during concurrent convergence/barrier promotion. The affected historical rows were repaired under an exact `CONTROL_PLANE_REPAIR` plan with readback. This is a durable reminder that same-sheet row indexes must never be assumed stable without exact-ID re-resolution.

## Concurrency

A lease fences its exact scope. Global barriers can still block otherwise-disjoint writes. Re-read both immediately before write/effect boundaries.
