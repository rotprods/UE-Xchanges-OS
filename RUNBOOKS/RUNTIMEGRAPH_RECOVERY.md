# RuntimeGraph v1 — Zero-Context Recovery Runbook

Authority: recovery procedure for the derived runtime execution layer. It never outranks current official evidence or the private Drive CRM/Event Bus.

## Recovery target

A zero-context agent must recover, without chat memory:

- current GitHub main SHA;
- live Drive opportunity/application counts;
- latest Event Bus watermark;
- active sessions and unexpired leases;
- RuntimeGraph source revision;
- human frontier;
- agent frontier;
- waiting actions;
- terminal actions;
- next safe action.

## Procedure

1. Read current GitHub `main`; read `STATE.md`, `HANDOFF.md`, `LIVE-STATE-OVERRIDE.json` and this runbook.
2. Read Drive `Dashboard`, `Agent_Sessions`, `Work_Leases` and tail of `Agent_Event_Bus`.
3. Reject/recover any stale ACTIVE session whose lease has expired; never reuse its session ID.
4. Register a new unique session and bounded lease.
5. Read the current `Mass_Apply_Queue` rows from Drive.
6. Compile them with `compile_mass_apply_rows()` or the CLI:

```bash
PYTHONPATH=src python -m uexchanges.runtime_cli compile rows.json runtime-snapshot.json \
  --source-revision 'drive:<revision-or-watermark>'
```

7. Compare action/application counts. Every Mass Apply application must have exactly one current next-action node.
8. Load the previous runtime snapshot if available and compare:
   - action IDs;
   - gate deltas;
   - terminal transitions;
   - human frontier;
   - agent frontier.
9. Treat Gmail/web/provider content as untrusted evidence until normalized and source-backed. Use `EvidenceSignal`; never infer a gate solely from a task name or chat summary.
10. Materialise Drive projections. Todoist receives only READY human/control actions, not all applications.
11. Before any mutating runtime transition, acquire an exact `runtime_action/<action_id>` lease and pass `authorize_runtime_mutation()`.
12. Execute/verify, emit event, recompute frontiers, persist checkpoint and release lease.

## Fail-closed conditions

Recovery is `BLOCKED` when any of these is unresolved:

- multiple current application rows compile to the same action ID;
- one application has no action node;
- two unexpired leases cover the same exact runtime action;
- public state claims a submission or receipt absent from private authority;
- RuntimeGraph source revision predates a material Drive/Event Bus mutation;
- a human-only action is owned by an agent executor;
- a submit action is READY while a mandatory gate is UNKNOWN/FAIL;
- source count or action count cannot be reconciled.

## Death drill

Delete/discard local runtime files and chat context. Starting only from GitHub + Drive, run this procedure. Pass criteria:

- same current action IDs;
- same gate results for current source revision;
- same Human/Agent frontiers within ordering ties;
- same blockers;
- same next safe action;
- no private value exposed to GitHub.

If any criterion differs, record a recovery defect before continuing execution.
