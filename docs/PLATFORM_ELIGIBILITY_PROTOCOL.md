# Platform Eligibility Protocol

## Purpose

Some opportunity platforms impose a target-group constraint that applies before the individual call's topic fit is considered. The system must model those constraints explicitly rather than treating every listing as an open public application.

## SALTO European Training Calendar

SALTO's applicant guidance states that the European Training Calendar is intended for youth workers, youth trainers and people already involved in the youth-work context. Individual activities can define additional or related target profiles, but a strong thematic match does not remove the platform/context requirement.

Operational consequence:

`SALTO_ETC_SOURCE -> requires_youth_work_context = true`

## Tri-state private evidence

Applicant field:

`youth_work_context_verified = true | false | null`

- `true`: private evidence demonstrates actual relevant youth-work involvement or another target explicitly accepted by the call.
- `false`: verified profile evidence establishes that the required context is not met.
- `null`: insufficient evidence. This is the default when we only have adjacent professional/creative/educational experience.

The application engine maps these states to:

- true -> PASS
- false -> FAIL
- null -> UNKNOWN / `VERIFY_YOUTH_WORK_CONTEXT`

UNKNOWN is not an application-ready state.

## Evidence threshold

Do not auto-pass from:

- a CV using words such as mentor, trainer, educator or facilitator;
- course/workshop material that has never been delivered;
- professional photography/video/digital/AI work alone;
- self-description as a youth worker;
- one isolated informal interaction without evidence of youth-work context.

Useful evidence can include:

- verified affiliation/collaboration with a youth organisation/service;
- actual activity delivered with/for young people in a youth-work context;
- agenda/material/methodology + delivery evidence;
- organiser confirmation, feedback or reference;
- repeated youth-work involvement;
- stronger formal/contractual evidence where available.

The exact call may require more. Evidence must be represented at its real strength.

## Relationship to trainer progression

Passing the youth-work-context gate is **not** equivalent to being a SALTO/TOY trainer.

Credential ladder:

`L0 self-description -> L1 affiliation -> L2 delivered youth activity -> L3 external reference/repeated practice -> L4 TOY-qualifying international full-time trainer reference`

A local youth workshop can help build L2/L3 evidence but does not become a TOY reference.

## Source policy

Platform requirements are defined in `src/uexchanges/platform_policy.py` and applied after canonical opportunity normalisation. They may only tighten opportunity requirements. They never relax call-specific eligibility.

## Safety invariant

High Fit Score, deadline urgency, photography/media contribution or AI expertise can increase the priority of **verification/credential acquisition**, but they cannot override this hard gate.
