# Reply Ingestion Protocol

## Purpose

External replies from organisers, sending organisations, hosts or programme contacts are evidence events. They are not conversational suggestions and must not be paraphrased into stronger claims than the source supports.

## Mandatory pipeline

```text
REPLY_RECEIVED
 -> THREAD_READ_IN_FULL
 -> SOURCE_IDENTITY_VERIFIED
 -> EVIDENCE_NODE_CREATED
 -> EXPLICIT_FACTS_EXTRACTED
 -> FACT_CONFLICT_CHECKED
 -> CANONICAL_FACTS_UPDATED_OR_DEBT_PRESERVED
 -> GATES_RECOMPUTED
 -> ONE_NEXT_OPERATION_SELECTED
 -> CRM_DOSSIER_TODOIST_SYNCED
```

## Required evidence fields

- thread/message ID;
- sender identity and organisation;
- received timestamp;
- related opportunity/organisation/application IDs;
- exact question asked;
- explicit answer/facts;
- unresolved ambiguity;
- source authority and confidence;
- externally usable flag;
- resulting decision code.

Private emails remain in Gmail/Drive. GitHub stores only schemas, protocols, anonymised fixtures and non-private aggregate state.

## Extraction rules

1. Read the complete thread, not just the latest snippet.
2. Separate direct statements from interpretation.
3. Preserve dates, roles, conditions and exceptions exactly.
4. Do not infer acceptance, remaining places, eligibility or AI permission from friendliness or silence.
5. Do not infer a sensitive attribute from a target-profile description.
6. Do not treat a sending organisation's generic answer as overriding a host's call-specific rule unless authority is clear.
7. When facts conflict, invoke the Fact Resolution Guard; never choose by majority vote.
8. A reply may resolve one gate while leaving others `UNKNOWN`.

## Decision examples

### Positive eligibility clarification

```text
organiser explicitly confirms profile is eligible
 -> store evidence
 -> eligibility gate PASS for that criterion
 -> continue to private gates/form/policy
```

### Conditional eligibility

```text
organiser says eligible only if condition X is met
 -> create requirement X
 -> evaluate evidence
 -> PASS | FAIL | UNKNOWN
```

### AI policy response

```text
AI support allowed for research/organisation only
 -> AI_ASSIST_ONLY
 -> final wording remains human owned
```

```text
AI-written answers prohibited
 -> AI_FINAL_TEXT_PROHIBITED
 -> HUMAN_WRITE_REQUIRED
```

### No response

```text
no reply by follow-up threshold
 -> organisation response prior may update
 -> eligibility/policy remains UNKNOWN
 -> never treat as rejection or permission
```

## Sync transaction

A material reply is not fully ingested until all applicable projections agree:

- Gmail thread remains source evidence;
- Drive CRM opportunity/application/organisation rows updated;
- dossier updated with source-backed resolution;
- Todoist task receives the next action;
- GitHub goal-state/protocol changes only when routing semantics or campaign state materially change.

## Follow-up cadence

- deadline inside 72 hours: one concise follow-up when operationally useful;
- deadline beyond 72 hours: follow up after a reasonable interval;
- never spam multiple contacts with repeated identical messages;
- after deadline, route to receipt/outcome verification rather than pretending the call remains actionable.

## Quality invariants

- zero facts without provenance;
- zero invented reply content;
- zero stronger claims than the source;
- zero silent state divergence;
- exactly one mandatory next operation after each completed ingestion.
