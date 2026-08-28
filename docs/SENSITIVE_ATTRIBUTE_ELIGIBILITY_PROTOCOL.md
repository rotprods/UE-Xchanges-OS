# Sensitive-Attribute Eligibility Protocol

## Purpose

Some mobility calls prioritise or restrict participation using sensitive personal attributes such as disability, health/access needs, fewer-opportunities status, socioeconomic barriers or protected identity characteristics.

The system must protect the applicant from two opposite failures:

1. fabricating or inferring a sensitive attribute to gain eligibility;
2. unnecessarily excluding the applicant when an attribute is preferred but not mandatory.

## Hard rules

1. Never infer a sensitive attribute from profession, behaviour, media, name, location, prior applications or adjacent evidence.
2. Never ask for sensitive data unless the exact call makes it materially relevant to an eligibility or accessibility decision.
3. The user controls voluntary disclosure. Private evidence stays in private storage.
4. Public GitHub stores only protocol/schema semantics, never the user's sensitive value.
5. A preference, priority group and mandatory eligibility condition are different states.
6. Conflicting public descriptions create `VERIFY_SENSITIVE_TARGET_PROFILE`; agents may not choose the more permissive or restrictive interpretation by intuition.
7. A high Fit Score or urgent deadline never bypasses this gate.
8. Application copy must not exploit, exaggerate or medicalise personal circumstances.

## Requirement states

`NOT_RELEVANT`

The call has no sensitive-attribute requirement.

`OPTIONAL_SELF_DISCLOSURE`

Disclosure may support accessibility arrangements or contextual understanding but is not required for eligibility.

`PREFERENCE_ONLY`

The call prioritises a group, but applicants outside it may still be eligible.

`MANDATORY_PRIVATE_GATE`

The attribute is an explicit eligibility condition. Evaluation remains private and requires intentional user-provided evidence.

`CONFLICTING_TARGET_PROFILE`

Authoritative/near-authoritative sources disagree or use ambiguous wording. Direct organiser/partner clarification is required.

`USER_DECLINES_DISCLOSURE`

No inference is permitted. If disclosure is mandatory, application is blocked; if optional, the route continues without it.

## Safe graph route

```text
SENSITIVE_REQUIREMENT_DETECTED
 -> CLASSIFY_MANDATORY_PREFERENCE_OPTIONAL
 -> SOURCE_CONSISTENCY_CHECK
 -> CONFLICT? VERIFY_WITH_ORGANISER
 -> PRIVATE_USER_DECISION/EVIDENCE_IF_NEEDED
 -> PASS | FAIL | UNKNOWN | CONTINUE_WITHOUT_DISCLOSURE
```

## Example: Step Into Paralympics

The original infopack's explicit checklist states partner-country residence, age 18–30, some English and full commitment. A partner website summary mentions disabled aspiring youth workers.

Correct handling:

`CONFLICTING_TARGET_PROFILE -> organiser clarification`

Incorrect handling:

- infer the applicant has/does not have a disability;
- assume the partner summary is a project-wide mandatory rule;
- ignore it because the infopack is more permissive;
- ask the applicant to disclose medical information before establishing relevance.

## Scoring

Sensitive attributes are not generic competitiveness boosters. They may affect eligibility or call-specific priority only where explicitly supported by the call and intentionally disclosed.

Never encode a universal score bonus/penalty for disability, fewer-opportunities status, health, ethnicity, religion, sexuality or other protected/sensitive characteristics.

## Media and safeguarding

When projects involve disabled people, minors, health, trauma or vulnerable groups, photo/video contribution remains secondary and requires explicit organiser approval, informed consent, privacy and safeguarding. Never use lived experience as visual content without proper agency and permission.
