# Checkpoint — RuntimeGraph v1 live derived projection

Date: 2026-09-01 18:11 Europe/Madrid  
State: `RUNTIMEGRAPH_V1_LIVE_DERIVED_PROJECTION`

## Purpose

Replace chat-driven execution with a deterministic human-agent action frontier derived from the authoritative private Mass_Apply_Queue.

## Release evidence

### RG-01–06 core

- PR: #28
- exact-head CI: `33528141133` — success
- merge/main: `a54191f976d065ec52d4f0e8f5b76b7a1c7da1e9`
- main CI: `33528349976` — success

### RG-07–12 adapters/fencing/recovery

- PR: #30
- exact-head CI: `33529263327` — success
- merge/main: `ab003474616a4669f961af7b33cc0fa8dffdbbc8`
- main CI: `33529366802` — success

### Atomic-action + temporal compiler

- PR: #33
- exact-head CI: `33530169498` — success
- merge/main: `80d31479d2bb8572623d9b4a385e457d49761c11`
- main CI: `33530272909` — success

## Live compile

Source: private Drive `Mass_Apply_Queue`, 164 application rows, exported after the above domain reconciliation.

Derived RuntimeGraph:

- applications: **164**
- atomic actions: **177**
- gates: **656**
- edges: **1,211**
- Human READY: **1**
- Agent READY: **145**
- System READY: **10**
- WAITING: **8**
- current-wave receipt-backed submissions: **0**

The single application Human READY action at materialisation time is COMPASS: human identity/payment/receipt/Tally completion. This is a derived frontier, not confirmation of payment or project confirmation.

## Private artifacts

- Runtime read model: Drive file `16QcHOWoBD1ixstPkhivftuyqmQdhtZj6`
- machine snapshot: Drive file `1iVyNAZWmURTdK8wZyYjYxyYDh9Djik3P`
- canonical CRM remains `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`

The runtime read model is a projection. Official/organiser evidence and the private CRM/Event Bus remain authoritative.

## Defects found by the gauntlet

1. **UNKNOWN self-deadlock** — an agent verification action originally required the same UNKNOWN gate it was meant to resolve. Fixed: reversible agent verification/preparation may run through UNKNOWN; submit stays fail-closed.
2. **mixed macroaction executor** — historical `Next Action` values combine AGENT and HUMAN work. Fixed: atomic action decomposition with `PRECEDES` edges.
3. **stale urgency buckets** — T0/T1 labels can outlive their actual calendar deadline. Fixed: temporal `Deadline Gate`; expired irreversible paths become `VERIFY_DEADLINE_EXTENSION_OR_ARCHIVE` unless authoritative late/open/selected evidence exists.
4. **generic AUTH false-positive** — `WORK_AUTH` verification was misclassified as human authentication. Fixed by explicit human-auth token matching.

Each failure family now has regression tests.

## Human/agent law

Human only:

- authentication/MFA/CAPTCHA;
- identity/sensitive values;
- payment;
- applicant-owned final wording where required;
- personal video recording;
- irreversible submit.

Agent:

- discovery/source/form/infopack verification;
- evidence normalization;
- gate recomputation;
- factual prefill/answer-pack preparation within policy;
- QA;
- receipt verification;
- projections and recovery.

## Form Gateway bridge

`docs/RUNTIMEGRAPH_FORM_GATEWAY.md` defines the integration with the existing typed Form Execution Gateway. RuntimeGraph chooses the next action; Form Gateway represents form fields, ownership, attempts and receipts. Neither may bypass hard gates or invent submission authority.

## Recovery

`RUNBOOKS/RUNTIMEGRAPH_RECOVERY.md` reconstructs frontiers from GitHub + Drive without chat context. Runtime mutations require the existing Session/Lease/EventBus discipline and exact runtime-action lease authorization.

## Todoist

Todoist is not populated with 164 duplicate application tasks. The currently READY human application action is attached to the existing COMPASS human task with the RuntimeGraph read-model link. Cross-cutting control-plane human tasks may remain outside the application graph.

## Exit / next action

RuntimeGraph implementation is accepted when this checkpoint/state PR passes exact-head CI and is merged. Thereafter the execution loop is:

`Agent_Frontier → evidence/gate updates → recompute → Human_Frontier → receipt → outcome`.

The whole W9 program is not complete until its receipt and cohort stop contract passes.
