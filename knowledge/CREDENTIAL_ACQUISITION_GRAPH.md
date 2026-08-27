# Credential Acquisition Graph — Participant → Youth Worker → Facilitator → Paid Trainer

## Purpose

Close verified evidence gaps that currently block high-fit Erasmus+ training opportunities. The objective is not to relabel existing professional experience; it is to create a defensible chain of real youth-work / NFE activity and references.

## Current evidence position — 2026-08-27

Strong evidence exists for professional photography/video, digital communication, AI/automation/software, curriculum design and educational-content design.

Current verified gaps:
- no mapped youth-work / NFE delivery history;
- no verified full-time international trainer activities;
- no externally validated trainer/youth-work references;
- delivered-training outcomes/testimonials are not yet mapped.

Therefore: `BUILD, NOT CLAIM`.

## Graph

```text
PROFESSIONAL_MEDIA_AI_EVIDENCE
  -> EDUCATIONAL_DESIGN_EVIDENCE
  -> YOUTH_WORK_ELIGIBILITY_CONFIRMED_BY_ORGANISER
  -> PARTICIPATE_IN_KA153 / YOUTH EXCHANGE
  -> CONTRIBUTE_TO_SESSION / DISSEMINATION
  -> LOCAL_FOLLOW_UP_ACTIVITY
  -> ORGANISER_REFERENCE
  -> ASSISTANT_FACILITATION
  -> FULL_TIME_INTERNATIONAL_TRAINER_ACTIVITY_1
  -> ACTIVITY_2
  -> ACTIVITY_3
  -> TOY_ELIGIBLE
  -> PAID_CALLS_FOR_TRAINERS
```

## Fastest legitimate bridge for current P0 calls

For calls such as `Unleashing Creativity` and `CTRL+REAL`, where subject-matter fit is exceptional but the profile requires youth workers / educators / NFE actors:

1. Never assert youth-worker status from unrelated creative work.
2. Map all actually delivered teaching/mentoring/workshops and identify audience/context.
3. Ask the organiser/sending partner whether an educator/creative technologist with relevant curriculum experience who is transitioning into youth work fits the participant profile.
4. Record organiser answer as an Evidence/Eligibility event.
5. If accepted, participate fully and create a real follow-up NFE activity after mobility.
6. Ask for a truthful reference describing role and contribution.

## Evidence levels

### L0 — Self-description
CV/bio claim only. Supports internal discovery, weak externally.

### L1 — Artifact
Curriculum, workshop deck, lesson plan, published educational material. Proves design/creation, not delivery.

### L2 — Delivery proof
Calendar/event page, participant communication, invoice/contract, recording, attendance record or organiser confirmation showing actual delivery.

### L3 — Outcome/reference
Participant feedback, organiser testimonial/reference, evidence of follow-up output.

### L4 — TOY-qualifying trainer reference
International youth-work training, at least three days, full-time trainer responsibility for educational goals, NFE methodology, validatable reference, subject to current SALTO criteria.

## Current mapping

- EV-006 mentoring curriculum: L1 unless delivery evidence is added.
- EV-007 agent-graph masterclass: L1 unless live-delivery evidence is added.
- Professional photo/video/AI work: strong subject-matter evidence but not youth-work evidence.

## Organisation relationship nodes

Track separately:
- sending/partner organisation;
- contact person;
- first contact;
- application decisions;
- selection outcome;
- project participation;
- contribution offered/delivered;
- follow-up activity;
- reference requested/received;
- future facilitator/trainer invitation.

Relationship strength must be event-derived, never manually inflated.

## Media-to-youth-work bridge

Photo/video should be used to create real youth-work value:
- teach participatory visual storytelling rather than only filming participants;
- support youth-led content creation;
- Photovoice / visual advocacy / media-literacy workshops;
- ethical media and consent practices;
- documentation/dissemination assets only with organiser approval.

This turns existing professional capability into educational contribution while preserving safeguarding and role boundaries.

## Trainer reference strategy

Do not chase the label `trainer` first. Chase educational responsibility that can later be verified:
1. co-design a session;
2. co-facilitate;
3. own a learning block with defined objectives;
4. join the full trainer team on an international activity;
5. secure a reference specifying duration, trainer role, NFE and educational responsibility.

Only qualifying activities enter the TOY counter.

## Decision rule

When a high-fit opportunity is blocked by role evidence:

`subject_fit >= 85 AND role_evidence = UNKNOWN -> ORGANISER_ELIGIBILITY_QUERY`

not:

`subject_fit >= 85 -> CLAIM_ROLE`.
