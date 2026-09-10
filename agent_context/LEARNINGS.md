# UE-Xchanges-OS — Learnings ledger

Seal: `2026-09-10T14:46:00+02:00`
Authority: durable engineering lessons; not live domain state.

## Learning loop

`OBSERVE → FORM HYPOTHESIS → FALSIFY → MINIMAL PATCH → TEST → RETEST → ADVERSARIAL REVIEW → CANARY → PROMOTE → REMEMBER`

Never skip directly from “seems fixed” to “production enabled”.

## L-001 — Chat memory is not continuity

Repeated long-running sessions proved that chat context is finite and can disappear. Durable continuity must exist in repo + private control plane before a session ends.

**Rule:** every meaningful session leaves state, handoff, event/lease evidence and one explicit next transition.

## L-002 — Historical hygiene and live writer safety are different health questions

A full control-plane scan is valuable for watchdog/reconciliation, but feeding all historical stale sessions/expired rows into the critical authorization path can make a healthy new writer impossible to start.

**Resolution:** PR69 introduced bounded normal-writer health over the exact current writer and currently-unexpired leases/live owners. `historical_hygiene_evaluated=false` must remain explicit.

## L-003 — `ACTIVE_READ_ONLY` must be observable but never writable

A stale read-only session can be real lifecycle debt. Ignoring it hides incidents; promoting it to `ACTIVE` would violate authority.

**Resolution:** PR68 adds stale `ACTIVE_READ_ONLY` health visibility while preserving non-writer semantics.

## L-004 — Authorization freshness is a critical section problem

The canaries demonstrated that a valid WriterAuthorization receipt can become unusable if broad reads or other work occur between evaluation/receipt persistence and lease acquisition.

**Rule:** expensive reads first; then refresh the critical evidence; mint receipt; persist `WRITER_AUTHORIZATION_GRANTED`; acquire exact proposed lease immediately. A stale receipt is discarded, never stretched or reused.

## L-005 — Do not invent stricter thresholds than policy

A canary failed because an ad-hoc 60-second freshness rule was stricter than the repository BootstrapPolicy. Extra conservatism can become an availability bug.

**Rule:** enforce current code/policy exactly. If a tighter limit is desired, change the policy in versioned code with tests instead of smuggling a new threshold into a prompt.

## L-006 — Strong WriterAuthorization receipts need integrity, not prose

Historical EventBus payloads revealed shape drift, missing required fields and unsafe assumptions. A string such as `ALLOWED` is not enough.

**Resolution:** PR67 introduced strict payload validation, duplicate-key rejection, content-addressed `receipt_id`, decision/timestamp binding and fail-closed audit/gate behavior.

## L-007 — Scheduler liveness must be tested separately from runtime correctness

A tiny tool-free scheduled probe completed successfully. Therefore “Scheduled Tasks can dispatch” and “RG2.2 can complete its full production path” are separate propositions.

**Rule:** use tiny scheduler probes to isolate platform dispatch. Use production-path canaries to certify RuntimeGraph.

## L-008 — One activation needs a micro-budget

Full bootstrap + archaeology + multiple provider scans + projections + closure can exhaust a Scheduled Task activation before lease acquisition or before cleanup.

**Rule:** one RG2.2 activation processes at most one adapter slice, at most 5 candidates and at most 2 exact subgraphs until empirical runtime data justifies a wider budget.

## L-009 — Closure is work, not an afterthought

Several historical sessions were left nonterminal even when useful work had happened. `finally` cannot rescue a hard-killed task.

**Rule:** reserve a substantial closure budget; stop starting work when closure begins; read back; release every own lease; prove release; set terminal session; emit terminal evidence. An independent watchdog handles hard interruptions.

## L-010 — A stale textual `ACTIVE` is not a live fence

Many historical lease rows remained `ACTIVE` after TTL expiry. Treating them as perpetual locks deadlocked progress; ignoring owner/integrity would be unsafe.

**Rule:** live fence = current unexpired lease + matching owner/context/scope under current policy. Expired rows remain hygiene debt for reconciliation.

## L-011 — Control-plane repair must preserve uncertainty

A stale or interrupted session does not become `COMPLETED` because we want a clean dashboard.

**Rule:** evidence-backed RPL; narrow `CONTROL_PLANE_REPAIR` lease; target exact ID; minimum mutation; read-back; health re-evaluation. Unknown stays unknown; stale interrupted canaries were closed `FAILED`, not promoted.

## L-012 — Exact-ID mutation and read-back are mandatory

Spreadsheet row indexes are ephemeral under concurrent writers. A prior column/row drift incident demonstrated why cached indexes are dangerous.

**Rule:** resolve stable entity ID immediately before write and read the same ID after write. Ambiguous write outcome requires reconciliation before retry.

## L-013 — COS semantic retrieval is not state authority

The repo contains a COS-20D semantic/topology layer. It is useful for retrieval, graph navigation and discovery, but similarity/embeddings must never route a domain mutation.

**Rule:** COS proposes candidates/relationships; exact provider/application/opportunity IDs + authoritative evidence decide mutations.

## L-014 — RuntimeGraph is derived, not canonical

RuntimeGraph can be rebuilt. Opportunities, Applications, Human_Gates and receipts cannot be rewritten from a derived projection merely to make projections agree.

**Rule:** authoritative evidence first → canonical operational state → RuntimeGraph reduction → reconstructible projections.

## L-015 — Gmail is evidence transport, not receipt authority

An organiser email may contain useful facts, but a Gmail message cannot directly become a submission receipt without canonical strong evidence bound to submission identity.

## L-016 — No-op paths deserve canaries too

A safe scheduler must close cleanly even when there is `NO_ADMISSIBLE_DELTA`. Stability is not demonstrated only by runs that happen to find work.

**Promotion target:** ideally prove both a no-delta canary and an admissible derived-delta canary before widening production.

## L-017 — Session registry and EventBus are separate evidence surfaces

CPR14's session row was observed `COMPLETED`, while the EventBus search used during this seal exposed its events through `LEASE_RELEASED` only. The correct response is to search for later terminal evidence or register a divergence finding, not fabricate one.

## L-018 — CGEV2 and COS have different responsibilities

CGEV2 is continuity/control/provenance: sessions, leases, events, state reconstruction, checkpoints and recovery. COS is semantic topology/retrieval. RuntimeGraph is deterministic execution projection. Mixing them creates authority leaks.

## Regression obligations created by these learnings

Keep tests for:
- malformed/missing WriterAuthorizationReceipt fields;
- duplicate JSON keys;
- content-address tampering;
- authorization timestamp tampering;
- bootstrap/main/watermark/scope/lease mismatch;
- expired/prelease-stale receipt;
- duplicate session IDs;
- orphan/mismatched unexpired leases;
- stale `ACTIVE_READ_ONLY` visibility with writer denial preserved;
- historical hygiene excluded from bounded normal-writer health;
- no fuzzy/embedding mutation routing;
- cursor monotonicity + late unique handling;
- at-least-once idempotency;
- ambiguous provider write reconciliation;
- lease release/session terminal closure;
- no Agent_Next execution from RG2.2;
- no payment/auth/credential/OTP/cookie/PREFILL/Submit capability leakage.
