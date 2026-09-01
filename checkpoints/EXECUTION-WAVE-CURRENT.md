# Current Execution Wave

Active product wave: `W9_CONTROLLED_SUBMISSION_BASELINE`.

Current execution engine: **RuntimeGraph v1**.

Runtime contract: `docs/RUNTIMEGRAPH_V1.md`.

Form bridge: `docs/RUNTIMEGRAPH_FORM_GATEWAY.md`.

Recovery: `RUNBOOKS/RUNTIMEGRAPH_RECOVERY.md`.

Current material checkpoint: `checkpoints/2026-09-01-runtimegraph-v1-live.md`.

Stop contract: `configs/w9_stop_contract_2026-08-29.json`.

Private live authority: Google Drive CRM `1uhxH3r27B_l5XqF2QGgX1Q__kxRVhO2Jyn7qS_GSTSU`.

Private RuntimeGraph read model: Drive `16QcHOWoBD1ixstPkhivftuyqmQdhtZj6`.

Machine snapshot: Drive `1iVyNAZWmURTdK8wZyYjYxyYDh9Djik3P`.

Canonical context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`.

Todoist W9 control: `6hPPRQrhG6cmhh3V`.

Status: `RUNTIMEGRAPH_V1_LIVE_DERIVED_PROJECTION__W9_EXECUTION_ACTIVE`.

## Execution frontier

`Agent_Frontier → evidence/gate update in Drive → RuntimeGraph recompute → Human_Frontier → human action → receipt verification → application/outcome transition`.

At materialisation:

- 164 applications;
- 177 atomic actions;
- 656 gates;
- 1,211 edges;
- Human READY 1;
- Agent READY 145;
- System READY 10;
- Waiting 8.

The application Human Frontier begins with COMPASS. Old Todoist labels/task titles do not override RuntimeGraph readiness; domain evidence must first update Drive and trigger recompilation.

## Writer rule

`REGISTER SESSION → READ EVENT CURSOR → ACQUIRE NARROW/EXACT ACTION LEASE → EXECUTE → VERIFY → EMIT IDEMPOTENT EVENT → PERSIST DOMAIN EVIDENCE → RECOMPUTE FRONTIERS → RELEASE → HANDOFF`.

No new architectural subsystem is authorised unless live execution exposes a repeatable failure that needs a deterministic invariant/test.
