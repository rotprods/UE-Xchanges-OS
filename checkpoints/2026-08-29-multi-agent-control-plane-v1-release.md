# Release — Multi-Agent Control Plane v1

Date: 2026-08-29  
Status: `MERGED_MAIN_CI_GREEN`

## Release evidence

- Pull request: `#21`
- Exact PR head: `72e381dd0287ce28599c3ed70dbe63ff9d63e744`
- Exact-head CI: `33270228648` — success
- Squash merge: `d05bea2f5f50872197901b6b002879052430327f`
- Main push CI: `33270343102` — success
- Focused local tests: `24/24` — success

## Released capabilities

- canonical Context Registry;
- unique Agent Session registry;
- append-only Agent Event Bus;
- exclusive Work Leases;
- cross-agent inbox/handoff projection;
- deterministic idempotency and mutation guards;
- evidence-safe opportunity economics;
- measurable global source coverage;
- ask-once profile interview;
- paid-first, global, rare-destination and remote-work-aware scheduling;
- strict separation between cash income and funded non-cash benefits.

## Current consistency boundary

The Drive-backed control plane provides shared read-before-write coordination. It does not push updates into an already-running chat. Every writer must refresh the context cursor, events and leases before each material mutation.

## Baseline preserved

The release does not claim any new application receipt and does not replace current official source or private CRM opportunity truth.

## Next transition

`REGISTER ALL NEW SESSIONS → LEASE WORK NODES → EXECUTE PAID/GLOBAL SOURCE LANES → COMPLETE PROFILE/ACCOUNT GATES → SUBMIT WITH RECEIPTS`.
