# UE-Xchanges RuntimeGraph v1

Authority: versioned engineering contract.  
Operational truth remains: official source / organiser evidence / receipt → private Drive CRM + Event Bus → public GitHub aggregate state → projections.

## Purpose

RuntimeGraph converts the existing mass-apply queue into a deterministic human-agent execution frontier:

```text
Opportunity → Application → Gate → Action → Executor → Evidence → Transition
```

The chat is not the scheduler. The graph is.

## Minimal ontology

- `Opportunity` — call/opportunity identity.
- `Application` — one candidature for one opportunity/role.
- `GateNode` — `PASS | FAIL | UNKNOWN`, evidence-backed.
- `ActionNode` — one bounded executable operation.
- `Evidence` — source, email, form, infopack, human confirmation or receipt.
- `RuntimeEvent` — append-only action transition.
- `HumanFrontier` — currently ready actions requiring authentication, personal authorship, payment, video or irreversible submit.
- `AgentFrontier` — currently ready reversible research/verification/preparation actions.

## Runtime law

```text
READ GRAPH
→ FIND READY NODES
→ SORT BY DEADLINE/PRIORITY
→ CLAIM UNDER LEASE
→ EXECUTE
→ VERIFY OUTPUT
→ EMIT EVENT
→ RECOMPUTE
→ UNLOCK NEXT FRONTIER
```

`UNKNOWN` never silently becomes `PASS`.

A `FAIL` hard gate prevents downstream submission actions for that call but preserves historical evidence.

## Human/agent boundary

Human-only actions include:

- login / authentication / CAPTCHA / 2FA;
- identity and sensitive personal fields;
- payment or bank transfer;
- applicant-owned final wording when required;
- personal video recording;
- irreversible final submission.

Agents may perform reversible and evidence-backed discovery, source verification, form capture, infopack extraction, evidence mapping, draft structure, QA, receipt verification and projection updates.

The kernel enforces executor ownership: an `AGENT` cannot claim a `HUMAN` action.

## Current compiler input

`compile_mass_apply_row()` accepts one canonical `Mass_Apply_Queue` mapping and creates:

- Spain gate;
- role/profile gate;
- form/infopack/AI-policy gate;
- one deterministic next-action node;
- executor classification;
- deadline priority;
- stable idempotency key.

This is intentionally a migration compiler, not a new source of opportunity truth.

## States

Action state:

```text
BLOCKED | READY | RUNNING | WAITING | DONE | FAILED
```

Action transitions are append-only events. Completion is idempotent by stable key.

## Projection model

Private Drive remains authoritative for live opportunity/application evidence. RuntimeGraph projections may be materialised to:

- `Runtime_Actions`;
- `Runtime_Nodes`;
- `Runtime_Edges`;
- `Human_Frontier`;
- `Agent_Frontier`.

Todoist receives only human/control-plane actions. It is not submission evidence and does not duplicate every atomic application row.

## Invariants

1. No submission state without authoritative evidence.
2. No action executes with unsatisfied hard prerequisites.
3. Human-only action cannot be claimed by agent executor.
4. Duplicate completion is idempotent.
5. Duplicate action IDs fail closed.
6. Deadlines must be timezone-aware internally.
7. Terminal/hard-fail rows never compile into a human submit action.
8. Runtime projections never override official/Drive evidence.
9. Private applicant values never enter public GitHub.
10. Runtime mutation requires the existing Session → Claim/Lease → Event discipline.

## Engineering decision

RuntimeGraph extends the existing Python deterministic kernel (`execution.py`, `coordination.py`, `models.py`, `graph.py`). It does not introduce a second service, database, queue, Redis, Kafka or microservice layer. Infrastructure expansion remains deferred until measured concurrency/replay/latency thresholds justify it.

## Acceptance

Core acceptance requires:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

and exact-head GitHub Actions success before merge.

The live migration is accepted only when every current application has a compiled action node and the Human/Agent frontiers can be reconstructed from durable authority without chat context.
