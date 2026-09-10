# UE-Xchanges-OS — Knowledge / Evidence Map

Seal: `2026-09-10T14:46:00+02:00`

> Public, non-sensitive recovery map. Private applicant values/answers remain in Drive and authorised sources.

## Evidence classes

### A — authoritative external evidence
Official call/page, authorised form, organiser confirmation, contract, payment/submission receipt, provider confirmation.

### B — canonical private operational evidence
Drive CRM + EventBus + exact entity/application rows + receipts + sessions + leases.

### C — versioned public system knowledge
GitHub code, policies, schemas, tests, runbooks and recovery projections.

### D — derived navigation/execution knowledge
RuntimeGraph, COS semantic graph, Command Center, Todoist/Notion/other projections.

D never overrides A/B. COS similarity never establishes a domain transition.

## Known current infrastructure facts at seal

- Baseline main: `349f63f2109e40ab6cba960c7311456a5d7ae906`.
- PR67 receipt/integrity hardening is in lineage.
- PR68 stale `ACTIVE_READ_ONLY` visibility is in lineage.
- PR69 bounded current-writer health is current baseline.
- Tiny native scheduler probe completed successfully.
- Control-plane scheduler canary V3 completed successfully for receipt/lease/release lifecycle only.
- Full RG2.2 scheduled production path has no proven PASS.
- `UEX Runtime Dispatcher` is disabled.
- PCV3, staged-A and PCV4 were reconciled FAILED and must not be reused.
- CPR12/13/14 repair fences observed in the current recovery chain are released.

## Known uncertainty / verification debt

The following must be read live; do not recover from old snapshots:

- current opportunity/application counts;
- current Human Frontier membership;
- current strong receipt count;
- current source cursors and continuation boundaries;
- current Dead_Letters;
- current organiser replies;
- current official deadlines/form-open state;
- current Form Gateway/provider capability ceiling;
- exact Todoist `runtime_action_id → task_id` bindings;
- whether CPR14 has a terminal EventBus event after `EVT-20260910T132147-CPR14-008`.

## Historical domain knowledge

Older domain snapshots contained facts for COMPASS, Step Into Paralympics, CIVIS LAB, SABER, I-PLAY, Game of Nature and other opportunities. **Those are historical hints only at this seal.** Re-read current private Drive + organiser/official evidence before acting on any of them.

## Current high-confidence architecture rules

- `UNKNOWN` is verification debt.
- `SubmissionAttempt != SubmissionReceipt`.
- Gmail raw prose/absence is not receipt authority.
- Exact IDs are required for state-changing routing.
- Source cursors are ingestion high-watermarks, not source authority.
- At-least-once + deterministic idempotency is the delivery model.
- Historical stale rows belong to reconciliation; they do not automatically block a healthy normal writer.
- A normal writer's bounded health is not a claim of global historical hygiene.
- `ACTIVE_READ_ONLY` remains non-writer.
- WriterAuthorizationReceipt grants no domain/external capability.
- RG2.2 does not execute Agent_Next.
- COS/embeddings/fuzzy similarity never authorize mutation.

## Forbidden inference

Never infer from absence, similarity, UI status or stale summaries:
- application submission;
- receipt confirmation;
- eligibility/acceptance;
- payment completion;
- youth-worker/trainer status;
- education/CEFR/work rights;
- health/disability/safeguarding facts;
- external PREFILL/Submit capability;
- writer authority.

## Knowledge update protocol

Every material fact should carry source/evidence ref, observation timestamp, exact entity ID, previous/new state, authority class, next gate and event/idempotency evidence.

If it changes domain truth, canonical evidence/Drive is updated first; RuntimeGraph/COS/projections follow.
