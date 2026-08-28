# Addendum — Sensitive-Attribute Eligibility

Real Step Into Paralympics source data exposed a new state-machine requirement: one source used a general open eligibility checklist while a partner summary mentioned disabled aspiring youth workers.

The system preserved the conflict rather than inferring disability, excluding the applicant prematurely or ignoring a possible priority/mandatory group.

New protocol: `docs/SENSITIVE_ATTRIBUTE_ELIGIBILITY_PROTOCOL.md`.

Decision code: `VERIFY_SENSITIVE_TARGET_PROFILE` / `CONFLICTING_TARGET_PROFILE`.

Hard rule: sensitive attributes may affect eligibility only when explicitly source-backed and intentionally disclosed; they are never generic competitiveness features.
