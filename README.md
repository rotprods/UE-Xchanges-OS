# UE-Xchanges-OS

Evidence-first global mobility, application-execution and trainer-progression operating system for Erasmus+ Youth, European Solidarity Corps, Eurodesk, SALTO, non-SALTO calls, paid trainer/facilitator work, professional mobility, humanitarian routes and paid monitor/activity roles.

## Current operating mode

**APPLY EVERYTHING VIABLE.**

Every legitimate Spain-compatible opportunity enters the CRM and preparation factory. Priority orders execution; it never bypasses a hard gate or removes a viable route. Selection between accepted options happens after acceptance.

## Strategic objective

Expand globally beyond Murcia while preserving online-work continuity.

Execution is ordered toward:

1. paid trainer/facilitator/expert work;
2. paid monitor/camp/activity/project roles;
3. paid communication/media/digital opportunities;
4. extra-European and humanitarian funded routes;
5. rare/unusual funded experiences;
6. all remaining viable calls.

Primary economics metric:

```text
verified net cash / verified work hour
```

Travel, accommodation, meals and training remain non-cash funded value.

## Multi-agent control plane

Canonical writers coordinate through the private CRM tabs:

```text
Context_Registry
Agent_Sessions
Agent_Event_Bus
Work_Leases
Agent_Inbox
Opportunity_Economics
Source_Coverage
Profile_Interview
```

Before writing, every chat/agent must register a unique session, refresh the context cursor and events, acquire a narrow lease and then emit an idempotent event. Unregistered sessions are read-only.

The current system is near-real-time through shared read-before-write state; it is not a push subscription between already-running chats.

## North stars

```text
valid receipt-backed applications / live Spain-compatible opportunities
verified net cash / verified work hour
paid trainer/facilitator credential progression
```

All are subject to zero known eligibility false-passes, duplicates, fabricated claims, AI-policy violations, sensitive-attribute invention, receipt guesses, conflicting lease writes and projection divergence.

## Canonical pipeline

```text
DISCOVERED → INGESTED → DEDUPED → SOURCE_VERIFIED
→ SPAIN_ROUTE_VERIFIED → DEADLINE_VERIFIED → ROLE_PROFILE_EXTRACTED
→ INFOPACK_CAPTURED → INFOPACK_ANALYSED → FORM_CAPTURED
→ APPLICATION_POLICY_RESOLVED → EVIDENCE_MAPPED → ANSWER_DRAFTED
→ HUMAN_OWNED_FINAL_TEXT → QA → SUBMITTED → RECEIPT_STORED
→ OUTCOME_RECORDED → ACCEPTANCE_DECISION
```

## Current W9 baseline

- 167 opportunity rows;
- 156 application/dossier and mass-apply rows;
- 96 source-inbox nodes;
- 22 organisation nodes;
- 52 execution-log events;
- 35 urgent rows classified;
- 60 unique Telegram posts unresolved;
- 0 submission receipts;
- 0 verified TOY-qualifying references.

## Truth topology

1. Current official source, original infopack, authorised form, organiser confirmation, contract and receipt.
2. Private Drive CRM event bus and evidence graph.
3. GitHub code, schemas, policies and aggregate state.
4. Portable release snapshot.
5. Todoist projections.

## Integrity locks

- `UNKNOWN` is verification debt.
- Historical participation never proves current youth-work or trainer responsibility.
- AI policy controls final prose.
- No `SUBMITTED` state without authorised route and evidence.
- Cash and non-cash funded value are never conflated.
- An active lease blocks a conflicting writer.
- Public GitHub contains no private applicant values.

## Repository map

- `goal.md` — portfolio objective and policy.
- `goal-state.json` — machine-readable public checkpoint.
- `AGENTS.md` — mandatory cross-session contract.
- `docs/MULTI_AGENT_CONTROL_PLANE.md` — sessions, events, leases and handoffs.
- `docs/GLOBAL_MOBILITY_AND_INCOME_STRATEGY.md` — economics/global priority.
- `docs/MASS_APPLY_POLICY.md` — apply-everything rules.
- `docs/GRAPH_OPERATING_PROTOCOL.md` — domain transitions.
- `configs/` — control-plane, priority and source-coverage configs.
- `src/uexchanges/` — deterministic core.
- `schemas/` — data contracts.
- `tests/` — regressions.

## Quality gate

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Exact-head GitHub Actions is mandatory before merge. Read `goal-state.json`, `AGENTS.md`, active leases and the event cursor before continuing.
