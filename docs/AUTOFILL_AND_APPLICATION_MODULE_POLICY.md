# Autofill & Application Module Policy

## Purpose

Scale application preparation across every viable Spain-compatible opportunity without copying private applicant data into the public repository, fabricating experience, or producing generic mass-application prose.

## Private/public boundary

The canonical reusable applicant profile lives in the private Drive CRM tab `Autofill_Profile` and the private Applicant Evidence Bank.

GitHub stores only:

- field semantics;
- verification states;
- allowed-use rules;
- composition logic;
- safety invariants;
- aggregate operational state.

GitHub must never contain phone numbers, dates of birth, identity-document numbers, emergency contacts, health/accessibility data, private addresses or final application answers.

## Field contract

Every reusable field has:

1. `field_id`;
2. canonical value in private storage;
3. verification strength;
4. external-use rule;
5. next gate when incomplete.

Blank means unknown. Unknown is never inferred.

Examples of verification classes:

- `OFFICIAL_EVIDENCE_VERIFIED`
- `DOCUMENTED_PRIVATE`
- `USER_CONFIRMED`
- `USER_CONFIRMED_PARTIAL`
- `EVIDENCE_GAP`
- `HUMAN_REQUIRED`

## Application composition

Reusable modules live in private CRM tab `Application_Modules`. A final answer is composed as:

`call criterion -> verified evidence -> project-specific contribution -> credible learning goal -> proportionate multiplier`

Modules may cover participant motivation, audiovisual contribution, AI/digital competence, operations, rural/manual work, inclusion, wellbeing, entrepreneurship, prior Erasmus experience, learning, dissemination and role-specific positioning.

A module is not final copy. It must be adapted to the exact project, question, character limit, target group and application policy.

## Audiovisual contribution

Professional photography/video/content creation may be offered as a project-specific value-add when useful:

- organiser approval first;
- informed consent and privacy;
- safeguarding for minors or vulnerable/sensitive contexts;
- local law and explicit permission for drone use;
- core programme participation remains primary;
- no fixed deliverable quantities before agreement.

The media contribution never substitutes eligibility or a project's actual role requirements.

## Automation boundary

The system may automate:

- discovery and dedupe;
- source/infopack/form extraction;
- factual prefill packets;
- evidence retrieval;
- criteria-to-evidence mapping;
- structured drafts where the call permits assistance;
- QA, contradiction and policy checks;
- operational clarification emails;
- CRM/Todoist/receipt tracking.

Current connectors do not provide general-purpose interaction with arbitrary authenticated forms, login challenges, CAPTCHA or legally meaningful declarations. The human owner completes authentication, any required applicant-owned wording, final declarations, submission and receipt capture.

## AI-policy invariant

- `AI_ALLOWED`: assistance may extend to a complete draft, still fact-checked and human-reviewed.
- `AI_ASSIST_ONLY`: evidence, structure, QA and optional draft support are allowed; the applicant owns/reviews the final wording according to organiser guidance.
- `AI_FINAL_TEXT_PROHIBITED`: no final-answer drafting or rewriting; provide facts and an outline only.
- `AI_UNKNOWN`: continue research and evidence mapping; final text remains blocked until resolved or written independently by the applicant.

A request for maximum volume never overrides an explicit call policy.

## Apply-everything semantics

`APPLY_EVERYTHING_VIABLE` means every open, legitimate, Spain-compatible opportunity enters preparation regardless of fit score, destination prestige, duration or overlap.

It does not mean:

- apply when Spain is objectively ineligible;
- claim a missing role or credential;
- submit after deadline;
- duplicate an application;
- invent motivation or experience;
- bypass an AI-writing restriction;
- commit to mutually incompatible accepted opportunities.

Overlaps remain options until acceptance, then the Portfolio Guard requires one explicit commitment decision.
