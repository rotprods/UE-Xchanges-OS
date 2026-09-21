# UE-Xchanges-OS — MEMORY.md

> **Durable semantic memory, not live state.**
>
> This file stores only slow-changing lessons, invariants and recurring failure patterns. It must stay compact enough that every cold-start agent actually uses it.

## Authority

When memory conflicts with newer evidence, newer authority wins:

1. current official/provider/form/organiser/contract/receipt evidence;
2. private Drive CRM + evidence graph + `Agent_Event_Bus`;
3. current GitHub policy/code/schemas/recovery state;
4. RuntimeGraph and other derived projections;
5. `agent_context/**`, Todoist/Notion/interface projections;
6. chat memory.

`MEMORY.md` never overrides a receipt, organiser reply, live lease, current form or newer checkpoint.

## Durable mission memory

- Project: `UE-Xchanges-OS`.
- Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`.
- Core policy: **APPLY EVERYTHING VIABLE**; priority orders work but does not silently exclude viable routes.
- North-star application metric: truthful receipt/evidence-backed applications converted into real selections, attendance/certification and paid outcomes where applicable.
- Documentation, commits, PRs, prompts, events, agent count and task count are not business outcomes.

## Durable execution-first memory

- The system already has enough architecture to execute many opportunities. **Safe live execution outranks non-blocking architecture.**
- Before adding a new control plane/prompt/graph, identify the concrete failing enforcement point. If current machinery can safely advance an application, use it.
- One opportunity/call identity gets one initial candidature/contact by default, even when aliases or separate email threads exist.
- Unknown prior-send outcome means reconcile Gmail/provider evidence before retry; never blind-resend after a timeout/tool error.
- Use the lowest-friction authorised route: email when complete email candidature is accepted; form when required; both only in provider-stated order.
- Do not send preliminary route-query emails when a complete authorised candidature can already be sent.
- Ordinary silence is not urgency. Default no-reply follow-up is 5 days / 120 hours, except real deadline/bounce/provider-requested action.
- Do not repeatedly ask organisers questions already answered in correspondence, infopack or authoritative source.
- **INFOPACK-FIRST** is durable: read original infopack → current call → current form → official organiser/partner source → existing thread before turning any logistics/funding/profile/route question into organiser outreach.
- **INBOUND_ACTION_FIRST** is durable: when a provider asks for a concrete authorised action, execute/classify that action before sending a courtesy reply; an inbound action request is not automatically an email-response task.
- External communication stays project-specific, concise, professional and natural. Internal tooling/orchestration language is not recipient-facing content.
- Every substantive Erasmus+/youth-project email carries the canonical Erasmus signature exactly once; private identity payload stays private.
- Photography, filmmaking, VFX and content creation are legitimate optional contributions when relevant, subject to consent/privacy/safeguarding; credit/tagging may be agreed without becoming a participation condition.
- Canonical execution details live in `docs/APPLICATION_EXECUTION_CONTRACT.md` and are mandatory cold-start context.

## Durable truth rules

- `UNKNOWN` is verification debt, never permission.
- `ROUTE_QUERY_SENT != APPLICATION_SUBMITTED`.
- `EMAIL_CANDIDATURE_SENT != FORM_SUBMITTED`.
- `FORM_SUBMITTED != SELECTED`.
- `ELIGIBLE != SELECTED`.
- `INVITED_TO_APPLY != ACCEPTED`.
- `SELECTED != ACCEPTED_BY_USER`.
- `PAYMENT_REQUIRED_FOR_PLACE != CONFIRMED`.
- `SubmissionAttempt != SubmissionReceipt`.
- Drafts, open forms, Todoist completion, organiser encouragement, browser completion and agent statements are not submission receipts.
- Preserve conflicts; never majority-vote them or let semantic similarity resolve them.

## Durable profile/evidence memory

- Historical programme participation does not prove current youth-worker, trainer, facilitator or group-leader status.
- Attendance never implies delivery responsibility.
- Pending applications do not belong in completed-experience CV sections.
- Never infer degree, CEFR, safeguarding/first aid, disability/fewer-opportunities status, current affiliation, work rights, emergency/health facts, availability or experience duration.
- Search `Autofill_Profile` and `Profile_Interview` before asking Roberto for already persisted facts.
- Completed experience should be represented by an evidence ledger: title/programme/location/dates/role/host/sending organisation/certificate or source reference.
- Private applicant values, answers and identity evidence never belong in public GitHub.

## Durable AI/application memory

Application policy is per route, not a universal assumption:

- `AI_ALLOWED`: assistance may draft subject to truth/quality review.
- `AI_ASSIST_ONLY`: applicant-owned substance/final wording is required; assistance may improve/structure within the organiser's rule.
- `AI_FINAL_TEXT_PROHIBITED`: facts/outline only.
- `AI_UNKNOWN`: do not assume generated final prose permission; independently applicant-owned wording can proceed unless another gate genuinely requires clarification.

Do not ask every organiser about AI/tool use. Resolve published/explicit policy first. If directly asked about authorship/tool use, answer truthfully.

## Durable form-execution memory

Use:

`CAPTURE_ALL_STEPS → MAP_FIELDS → VALUE_PACK → PREFILL → QA → SUBMIT → RECEIPT`

- Capture the complete reachable form before filling, not merely the first page.
- Unknown personal/legal/medical/sensitive fields cause STOP; never guess.
- Ambiguous organisation affiliation causes STOP; never select the only visible option merely to progress.
- Authentication != PREFILL permission; PREFILL != Submit permission.
- Generic WriterAuthorization never implies browser credentials, email-send permission, irreversible Submit, payment or OTP/MFA/CAPTCHA authority.
- Clicking Submit or a technically “completed” browser run is not evidence; capture provider confirmation/receipt.

## Durable multi-agent memory

- Chat memory is never the continuity system.
- Every writer uses a fresh Session ID, reads current main + manifest + private events + **currently unexpired** leases and emits `BOOTSTRAP_CONTEXT_LOADED` before a write lease.
- WriterAuthorization is a short-lived coordination receipt bound to exact main/scope/lease; it is not domain authority or external capability.
- A lease fences exact scope, not the whole project.
- Expired/released textual `ACTIVE` rows do not remain locks.
- Every material mutation needs append-only event evidence and exact readback.
- Unknown side-effect outcome blocks blind replay.
- GitHub is authoritative for GitHub/PR/CI facts; never claim a merge or green CI before GitHub proves it.

## Durable RuntimeGraph / projection memory

- RuntimeGraph is derived, never a second opportunity/application authority.
- Projection existence != projection freshness. Compare generation/watermark with current Event Bus/provider evidence.
- Execution law: `READ → READY FRONTIER → CLAIM UNDER LEASE → EXECUTE → VERIFY → EMIT EVENT → RECOMPUTE`.
- Never edit canonical domain truth merely to make a stale dashboard agree.
- Todoist/Notion/interface state is reconstructible projection, not evidence of external outcome.

## Durable semantic-brain memory

- **Service is ephemeral; brain is reconstructible.** Daemon/container/VM liveness is not the persistence boundary.
- Restore and validate checksummed semantic artifacts before regenerating expensive embeddings.
- Semantic/vector/fuzzy similarity may retrieve candidates but never grants mutation authority.
- Historical vector partitions remain historical until source SHA/freshness is reconciled.
- Private live-evidence overlays stay private.
- Detailed semantic recovery architecture lives in `docs/SEMANTIC_BRAIN_DURABILITY.md`; do not duplicate its benchmarks/binary inventory here.

## Durable source/economics memory

- T3 social/aggregator sources discover; current original/provider sources authorise when available.
- Source freshness needs evidence: last attempt, last success, cursor, processed items and errors. A blocked scraper is not “complete”.
- Funded value is not salary. Accommodation, food, travel reimbursement, insurance, training and pocket money remain distinct from cash compensation.
- Paid-role economics require verified amount, hours/preparation, compulsory costs, payer/payment certainty and legal/tax/visa constraints before net/hour claims.

## Recurring failure patterns

1. **Architecture replaces execution** — activity increases while real applications do not.
2. **Duplicate outreach across threads/agents** — same call gets repeated initial emails or eligibility questions.
3. **Prepared != submitted** — drafts/forms/tasks are promoted without provider evidence.
4. **Email candidature != form receipt** — different evidence types are collapsed into one state.
5. **Missing/duplicated signature** — email body bypasses the canonical renderer.
6. **Partial form inspection** — first page is mistaken for complete form capture.
7. **Unknown send outcome replay** — timeout triggers duplicate send instead of reconciliation.
8. **Stale projection/dashboard** — old aggregate is treated as live canonical truth.
9. **Stale lease flag** — textual ACTIVE is trusted after expiry/release.
10. **Premature GitHub claim** — merge/CI is recorded without GitHub evidence.
11. **Provider session != agent authority** — login is mistaken for PREFILL/Submit capability.
12. **Volatile facts in stable docs** — counts/frontiers rot and redirect new agents into historical work.
13. **Semantic architecture dominates work selection** — durable recovery work becomes a default frontier even when live application work is safely executable.
14. **Infopack bypass** — organisers are asked to restate published dates/funding/logistics/profile facts instead of the system reading authoritative material first.
15. **Inbound-action inversion** — a courtesy reply is drafted while the provider-requested form/slot/upload remains undone.

## Memory write policy

Add to `MEMORY.md` only when the lesson is long-lived, non-sensitive, not a live count/deadline/frontier and not better represented in a specialised authoritative document.

Do **not** store live counts, current opportunity states, current lease ownership, receipt IDs or transient deadlines here.

Prefer links to specialised contracts over copying large architecture/runbook sections into memory.

## Mandatory bootstrap pointer

The machine-readable cold-start contract is `agent_context/bootstrap_manifest.json`. Every compliant writer must follow it and emit `BOOTSTRAP_CONTEXT_LOADED` before acquiring a write lease.
