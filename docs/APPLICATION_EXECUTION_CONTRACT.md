# UE-Xchanges-OS — Application Execution Contract v1

Status: **MANDATORY EXECUTION POLICY**

This contract exists because UE-Xchanges-OS already has substantial architecture. The default problem is no longer “design a better system”; it is **use the existing system to produce truthful, receipt-backed applications without duplicate outreach or state inflation**.

## 1. Outcome-first law

When a legitimate live opportunity can be advanced safely with the existing machinery, advance it before creating new architecture, prompts, diagrams, control planes or recovery layers.

Architecture/refactor work outranks application execution only when at least one of these is true:

1. a demonstrated defect blocks the current application path;
2. the defect can cause duplicate/false/unsafe external side effects;
3. a current versioned contract requires the repair before execution;
4. the user explicitly asks for architecture rather than execution.

Documentation, commits, events, agent count and task count are not North-Star outcomes.

## 2. One opportunity, one outbound identity

Before any initial outbound message, resolve a deterministic identity for:

`organisation_id + call_id/edition + applicant + purpose`

Search existing Gmail threads, CRM applications/outreach records and provider evidence across aliases. A new thread does not create a new opportunity identity.

For the same identity:

- one initial candidature/contact is the default;
- a provider reply is answered in the existing relationship thread when practical;
- timeout or tool failure requires effect reconciliation before retry;
- an unknown send outcome blocks blind resend;
- duplicate eligibility/AI/process questions are forbidden when evidence already answers them.

## 3. Route resolution before outreach

Use the lowest-friction **authorised** application route:

- if the organiser explicitly accepts a complete candidature by email, use email directly instead of sending a preliminary route-query;
- if the organiser requires a form, complete the form;
- if both email and form are required, follow the stated order;
- if the route is genuinely ambiguous and blocks application, ask only the minimum unresolved question;
- an accessible form is not proof that a call is open or that a place remains.

`EMAIL_CANDIDATURE_SENT` and `FORM_SUBMITTED` are different facts.

## 3A. Source-first preflight and inbound-action law

Before organiser outreach about project facts, resolve evidence in this order:

`ORIGINAL_INFOPACK → CURRENT_CALL → CURRENT_FORM → OFFICIAL_ORGANISER_OR_PARTNER_SOURCE → EXISTING_THREAD → UNRESOLVED_MATERIAL_BLOCKER`

Questions about dates, funding, accommodation, meals, travel ceilings, participant profile, programme, route or logistics that are already answered by that chain are `REDUNDANT_SOURCE_RESOLVABLE` and must not be sent.

When a provider sends a concrete requested action, classify the inbound first:

`ACTION_REQUEST | OUTCOME | INFORMATION | TERMINAL`

For `ACTION_REQUEST`, execute the authorised requested action before a courtesy reply when it is safe and currently possible. Examples include filling a specified form, selecting a discussion slot, uploading a requested document or confirming availability. Reply only when the reply itself is necessary, the action is blocked by a material unresolved fact, or the provider explicitly requests a response.

Do not ask about AI/tool use by default when no published rule requires clarification. Preserve applicant-owned final wording under `AI_UNKNOWN` or stricter route policy instead.

## 4. External communication standard

Outbound communication must be concise, project-specific, professional and natural.

Do not expose internal implementation language such as `agent`, `RuntimeGraph`, `TinyFish`, `human gate`, `receipt reconciler`, `lease`, `semantic brain` or orchestration internals unless it is genuinely relevant to the recipient.

Do not ask organisers about internal tooling or AI by default. Resolve the published application policy first. If a provider explicitly asks about authorship/tool use, answer truthfully.

Default follow-up SLA is **5 days / 120 hours**, not 24 hours. Earlier follow-up is allowed only for a real deadline, a provider-requested action, a bounce, or another documented urgency. Replies to organiser questions are not follow-up chasing.

## 5. Signature gate

Every Erasmus+/youth-project application or substantive outreach email must carry the canonical Erasmus signature **exactly once**.

The public repository may contain the rendering contract/template, but private identity/contact payloads remain in the private evidence/configuration surface. Do not solve the signature requirement by publishing private applicant data in GitHub.

Missing or duplicated signature blocks the send.

## 6. Applicant-owned text and AI policy

Classify the route with the existing AI policy model.

- `AI_ALLOWED`: drafting assistance is permitted subject to truth/quality gates.
- `AI_ASSIST_ONLY`: applicant-owned substance/final wording is mandatory; assistance may structure or improve it within the organiser's rule.
- `AI_FINAL_TEXT_PROHIBITED`: facts/outline only; no generated final answer.
- `AI_UNKNOWN`: do not assume permission for final generated prose.

Never fabricate youth-work status, group-leader/trainer experience, language level, organisation affiliation, fewer-opportunities status, health data, availability or other eligibility facts.

## 7. Full-form capture before fill

Form execution is:

`CAPTURE_ALL_STEPS → MAP_FIELDS → VALUE_PACK → PREFILL → QA → SUBMIT → RECEIPT`

Before prefill, capture every reachable page/section, required field, option, attachment requirement, character limit, declaration and visible policy notice.

Automation must stop on unknown personal/legal/medical/sensitive fields or ambiguous organisation affiliations. It must not select the only visible option merely to progress.

A technically completed browser run is not a submitted application. `SUBMITTED` requires provider evidence/readback under the current capability contract.

## 8. Evidence-specific states

Do not collapse these facts:

`EMAIL_CANDIDATURE_SENT`
`FORM_SUBMITTED`
`SUBMITTED_CONFIRMED`
`ACKNOWLEDGED`
`WAITLIST`
`SELECTED`
`ACCEPTED_BY_USER`
`WITHDRAWN`
`TRAVEL_APPROVED`
`ATTENDED`
`CERTIFIED`

A provider email acknowledging interest may be useful evidence without being a form receipt or selection.

## 9. Media contribution

Photography, filmmaking, VFX and content creation may be offered when relevant as a concrete contribution. Any recording/publication remains subject to organiser approval, participant consent, privacy, safeguarding and local rules.

Credit/tagging for published applicant-created media may be requested or agreed, but must not be presented as a condition of participation unless separately negotiated.

## 10. Throughput metrics

Optimise for:

1. unique viable opportunities verified;
2. complete applications submitted through authorised routes;
3. strong receipts/authoritative confirmations;
4. selections/acceptances;
5. attended/certified experiences;
6. paid-role outcomes where applicable;
7. median applicant/agent time per completed application.

Do **not** optimise for raw email count, agent count, event count, documents, commits, PR count or architecture volume.

## 11. Experience/CV evidence

Completed Erasmus/ESC experience belongs in the portfolio only when tied to source evidence. Attendance does not imply trainer, facilitator or group-leader responsibility. A pending application never becomes experience.

## 12. Execution selection

After cold-start recovery and hard-gate reconciliation, choose work in this order unless a demonstrated safety blocker intervenes:

1. provider-requested action / live acceptance or selection;
2. viable application whose deadline or place is at risk;
3. complete candidature through an already-authorised route;
4. receipt/outcome reconciliation for a real prior action;
5. source verification/discovery needed to feed applications;
6. projection repair required for safe execution;
7. architecture/refactor/documentation that is not currently blocking execution.

This ordering is a **work-selection law**, not authority to bypass gates, submit without capability, fabricate facts or make payments.
