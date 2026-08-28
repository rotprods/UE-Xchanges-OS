# Execution-State Precedence

During deadline-critical waves, operational facts can change faster than a full release-state consolidation.

Read order for current execution state:

1. canonical original source / organiser confirmation / submission receipt;
2. `LIVE-STATE-OVERRIDE.json` when present and active;
3. private Drive CRM/application dossier;
4. `goal-state.json` release snapshot;
5. Todoist execution projection.

An active override must be small, explicit, timestamped and list every revoked stale field. It may not silently alter code/policy semantics.

When the next coherent release state is prepared:

- integrate all surviving override facts into `goal-state.json`;
- record terminal/ambiguous outcomes explicitly;
- delete the override;
- run exact-head CI;
- refresh git.local.

Todoist or a cached search result never overrides an original source or receipt.
