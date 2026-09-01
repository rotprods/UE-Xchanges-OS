# RuntimeGraph V2 — Closed Loop

Status: IMPLEMENTATION CONTRACT
Authority: public engineering contract only; private Drive CRM/Event Bus remains operational authority.
Owner: RuntimeGraph V2 runtime
Source revision: session `SES-UEX-CHATGPT-20260901T221200-25`

## Objective

Turn RuntimeGraph v1 from a periodically rebuilt execution read-model into an incremental closed loop:

`SOURCE EVENT → NORMALIZED EVIDENCE → AFFECTED APPLICATION SUBGRAPH → FRONTIER → HUMAN/AGENT ACTION → EVIDENCE → TRANSITION`.

## Five components

1. **Incremental reducer** — one event mutates only one application subgraph; duplicate source versions are idempotent no-ops.
2. **Evidence→Claim registry** — external claims require explicit supporting evidence with compatible temporal and role scope.
3. **Form Gateway bridge** — value-free FormExecutionPlan metadata resolves form/policy gates; AI_UNKNOWN remains UNKNOWN.
4. **Receipt reconciler** — only authoritative confirmation with submission identity can produce a receipt event; raw email prose never does.
5. **Human Command Center** — exposes at most five immediately executable HUMAN actions; graph/debug complexity stays internal.

## Authority boundary

RuntimeGraph V2 is derived. It never outranks:

1. current official source / organiser confirmation / submission receipt;
2. private Drive CRM + Event Bus;
3. GitHub contracts and code;
4. RuntimeGraph projections / Todoist / Notion.

## Human-only boundary

Human remains mandatory for credentials, MFA/CAPTCHA, legally meaningful declarations, personal final wording where required, video delivery, payment and irreversible submit. RuntimeGraph may prepare and validate those transitions but cannot fabricate their completion.

## Receipt invariant

`CLICK_SUBMIT != SUBMITTED_CONFIRMED`.

A receipt event requires an authoritative provider/email confirmation, or a confirmation-text hash plus screenshot reference, bound to the matching application/submission identity.

## Claim invariant

Historical evidence cannot prove a current claim. Participant evidence cannot silently prove trainer/facilitator role. Evidence may be contextual without authorising a claim.

## Incremental reducer invariant

A domain event must carry an explicit `application_id`. Raw NLP extraction is upstream. The reducer does not guess which application or gate an email modifies.

## Projection policy

Todoist receives only `READY HUMAN` actions. It must never mirror all CRM/application rows. The Human Command Center defaults to five cards.

## Recovery

A cold-start agent reads current main + Drive Event Bus/leases, reconstructs the latest RuntimeGraph snapshot, replays normalized events after its watermark, recomputes frontiers and acquires a fresh narrow lease before any mutation.
