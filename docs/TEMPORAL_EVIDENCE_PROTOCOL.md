# Temporal Evidence Protocol

## Problem

Applicant evidence has time semantics. A verified historical Erasmus+/youth-sector activity can be highly valuable without proving a **current** role, and a current role can exist without proving trainer responsibility.

The system must never collapse these facts into one boolean.

## Four separate dimensions

1. **Historical youth-sector experience**
   - prior Youth Exchanges, Youth Staff professional-development activities, ESC or comparable verified activities;
   - useful for programme literacy, selection context and experience claims.

2. **Current youth-work context**
   - present involvement in youth work, a youth organisation/service, youth-facing educational practice or another explicitly accepted current target;
   - this is the field used by platform/call hard gates that say the applicant must currently be involved.

3. **Delivery / facilitation responsibility**
   - actual educational/youth-facing delivery, co-facilitation, workshop responsibility, learning-design responsibility or comparable work;
   - must be evidenced separately from attendance.

4. **Trainer qualification**
   - trainer responsibility that satisfies the exact call/TOY criteria;
   - never derived from participant status, group leadership or simple attendance.

## Applicant fields

```text
youth_sector_experience_verified: bool | null
youth_sector_last_activity_date: date | null
completed_erasmus_youth_staff_mobilities: int
completed_erasmus_youth_exchanges: int
youth_work_context_verified: bool | null  # CURRENT context only
```

## Gate invariant

A call with `requires_youth_work_context = true` evaluates **only current-context evidence** for that hard gate.

Therefore:

```text
historical experience = TRUE
current context = UNKNOWN
=> eligibility remains UNKNOWN
```

Historical experience may increase fit, confidence, programme-literacy evidence or organisation relationship priors. It may never convert the current-context gate to PASS by itself.

## Evidence metadata

Where practical, evidence records should carry:

- `occurred_at`
- `verified_at`
- `role_scope`
- source/provenance
- externally usable flag
- confidence

Recommended `role_scope` values include:

`participant`, `professional_development_participant`, `group_leader`, `facilitator`, `trainer`, `organiser`.

Unknown roles remain unknown.

## Selection use

Historical verified Erasmus experience can legitimately support statements such as:

- prior Erasmus+ participant;
- prior Youth Staff professional-development participant;
- familiar with Youthpass, international-group learning and Erasmus mobility workflow;
- prior relationship with a sending organisation when documented.

It does not justify statements such as:

- current youth worker;
- active NGO volunteer in 2026;
- facilitator/trainer;
- first-time Erasmus participant;
- TOY-qualified trainer.

## Recency

Recency requirements are call-specific. Do not invent a global expiration period for youth-sector evidence.

If a call says `currently active`, current-context evidence is required regardless of how strong historical participation is.

If a call asks for `experience in`, historical verified experience may be relevant depending on its role scope and wording.

## Outcome-learning rule

A previously accepted application is a **selection prior**, not objective proof for every statement it contained. Self-reported historical answers must be separated from independently verified participation/outcome evidence.
