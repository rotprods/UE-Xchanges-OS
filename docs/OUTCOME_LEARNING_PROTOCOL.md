# Outcome Learning Protocol

## Objective

Learn from real application outcomes without inventing causality or training the scoring system on noise.

The system currently has sparse outcome data. It must therefore control **which updates are permitted**, not pretend to estimate a statistically meaningful acceptance probability.

## Canonical outcome types

- `ACCEPTED_COMPLETED`
- `ACCEPTED`
- `WAITLIST_PRIORITY`
- `REJECTED_WITH_FEEDBACK`
- `REJECTED_HIGH_COMPETITION`
- `REJECTED_NO_REASON`
- `NO_RESPONSE`
- `WITHDRAWN`

## Learning dimensions

An outcome may update one or more of these independent priors:

1. positive selection prior;
2. negative selection prior;
3. competition/base-rate prior;
4. call-specific criterion heuristics;
5. organisation relationship prior;
6. organisation response-behaviour prior.

No single scalar 'acceptance score' is updated from sparse evidence.

## Causal-strength rules

### ACCEPTED / ACCEPTED_COMPLETED
Positive selection signal. May update organisation relationship and a weak/medium positive selection prior.

Forbidden: concluding that every application component caused selection or treating historical self-reported application answers as verified evidence.

### WAITLIST_PRIORITY
A high-priority waitlist is a **near-accept** signal.

Rank 1–3 may create a weak positive selection prior. It never creates a negative application-quality penalty without explicit feedback.

### REJECTED_WITH_FEEDBACK
Only this class allows call-specific negative criterion/answer heuristic updates, and only when explicit organiser feedback exists.

Feedback must remain scoped to the supported criterion/call. Never globalise one organiser's feedback into a universal rule.

### REJECTED_HIGH_COMPETITION
When an organiser reports a very large applicant pool but gives no individual reason, update competition/base-rate information only.

Forbidden: penalising motivation, skill, fit, copy quality or evidence quality without source-backed feedback.

### REJECTED_NO_REASON
Record the outcome but do not update application-quality heuristics. Competition prior may update only if pool size is known.

### NO_RESPONSE
Update organisation response-behaviour prior only. No response is not a verified rejection.

### WITHDRAWN
No selection-quality learning unless independent organiser feedback exists.

## Current private fixtures

Private CRM currently includes:

- accepted/completed historical mobility with Ticket2Europe;
- first-place waitlist / near-accept with BreGal;
- high-competition rejection with 430+ applications and no individual reason.

These are operational fixtures, not public test data containing personal/private content.

## Implementation

`src/uexchanges/outcomes.py` returns an explicit `LearningPolicy` containing:

- selection signal;
- causal strength;
- allowed prior/heuristic updates;
- near-accept state;
- forbidden inferences;
- reason.

This module deliberately performs no probabilistic forecasting.

## Future statistical threshold

Only consider empirical acceptance-probability calibration after enough independent outcomes exist across multiple organisations/programmes/call types. Until then, use component-level scoring + causal-strength policies + transparent priors.
