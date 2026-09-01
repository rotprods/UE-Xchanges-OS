# UE-Xchanges-OS — RuntimeGraph Recovery Map

> RuntimeGraph is a derived execution read model, never a second source of domain truth.

## Execution law

```text
READ AUTHORITY
→ NORMALIZE EVENT
→ REDUCE STATE
→ RECOMPUTE FRONTIERS
→ CLAIM READY ACTION UNDER LEASE
→ EXECUTE BOUNDED ACTION
→ VERIFY EVIDENCE
→ EMIT IDEMPOTENT EVENT
→ RECOMPUTE
```

## Released layers

### RG2 closed loop
Components released:
- incremental reducer;
- Evidence → Claim registry;
- Form Gateway read bridge;
- receipt reconciler;
- Human Command Center.

### RG2.1 event dispatcher
Released as commit lineage containing `6c23c9b6a70f33a7cb1eb780c54e49ebf5cf0d16`.
Capabilities:
- normalized ingress;
- explicit routing;
- at-least-once idempotency;
- monotonic source cursors;
- bounded retries;
- dead-letter isolation;
- frontier-change projection;
- strong receipt authority binding.

First live cycle ended at `EVT-20260901T234155-DSPC-008` with Human Frontier:
- STEP;
- COMPASS;
- CIVIS LAB;
- SABER.

Receipts: 0.

### RG2.2 adapters / self-heal
Status at snapshot: ACTIVE.
Session: `SES-UEX-CHATGPT-20260902T001630-27`.
Lease: `LSE-UEX-RUNTIMEGRAPH-ADAPTERS-20260902T001630-27`.

Scope:
- Gmail/Form/official-source/receipt adapters;
- value-safe `NormalizedIngress`;
- deterministic projection health;
- derived projection repair.

Exclusions:
- raw NLP authority;
- canonical application writes;
- payment/auth;
- browser Submit/PREFILL;
- secret/PII persistence.

## Runtime resources

- RuntimeGraph read model: `16QcHOWoBD1ixstPkhivftuyqmQdhtZj6`
- Machine snapshot: `1iVyNAZWmURTdK8wZyYjYxyYDh9Djik3P`
- Command Center: `1OtSLFI4VHW6aSne1YjtRykRsN4j4G4OcEGSCXVDLwbM`
- Canonical CRM/Event Bus: `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`

## Form execution bridge

RuntimeGraph decides **what action is eligible to run**.
The Form Execution Gateway decides **what browser/form capability exists and what gates it requires**.

Current Form stack:

```text
RuntimeGraph / MCP host
        ↓ stdio
Browser Stack Supervisor
        ↓
MCP Relay
        ↓ loopback bearer HTTP
Browser Worker
        ↓
Dedicated Chromium
```

Current browser capability ceiling:
- local status: yes;
- local inspect: yes;
- local validate: yes;
- local prefill: HMAC capability + explicit Worker start gate;
- external inspect: no;
- external prefill: no;
- submit: no.

The Browser Stack Supervisor PR #49 is merged on `d1d82b0d…` and its main test/browser-stack workflows passed.

## Authority boundary

RuntimeGraph may never convert these without canonical evidence:

- `ROUTE_QUERY_SENT → APPLICATION_SUBMITTED`;
- `ELIGIBLE → SELECTED`;
- `INVITED_TO_APPLY → ACCEPTED`;
- `PAYMENT_REQUIRED → CONFIRMED`;
- `SubmissionAttempt → SubmissionReceipt`.

## Frontier semantics

- HUMAN: login/MFA/CAPTCHA, identity/sensitive input, payments, applicant-owned final wording where required, irreversible Submit until separately certified.
- AGENT: reversible verification, form capture, evidence mapping, QA, safe factual preparation, projections.
- SYSTEM: deterministic reductions, cursor/idempotency/reconciliation work.

## Recovery procedure

A new RuntimeGraph agent must:
1. read current official/Drive authority;
2. inspect active leases;
3. read source cursors/dead letters;
4. ingest events after last cursor;
5. recompute frontiers;
6. never trust a stored frontier after material domain change without recomputation.

## Current coordination debt

The Browser Stack owner session is complete but its Work_Lease row was last observed ACTIVE. That is coordination-state debt, not code-state debt. Do not mutate Browser Stack paths until the lease is reconciled or objectively expired/taken over with an event.