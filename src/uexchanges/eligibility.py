from __future__ import annotations
from datetime import datetime, timezone
from .models import ApplicantProfile, EligibilityDecision, GateDecision, GateResult, Opportunity

def _combine(gates: list[GateDecision]) -> GateResult:
    if any(g.result is GateResult.FAIL for g in gates): return GateResult.FAIL
    if any(g.result is GateResult.UNKNOWN for g in gates): return GateResult.UNKNOWN
    return GateResult.PASS

def evaluate_eligibility(profile: ApplicantProfile, opportunity: Opportunity, *, now: datetime | None = None) -> EligibilityDecision:
    now = now or datetime.now(timezone.utc)
    gates: list[GateDecision] = []
    if opportunity.deadline is None:
        gates.append(GateDecision("deadline", GateResult.UNKNOWN, "No confirmed application deadline."))
    else:
        deadline = opportunity.deadline if opportunity.deadline.tzinfo else opportunity.deadline.replace(tzinfo=timezone.utc)
        gates.append(GateDecision("deadline", GateResult.FAIL if deadline <= now else GateResult.PASS, "Application deadline has elapsed." if deadline <= now else "Deadline is still open."))
    if opportunity.eligible_countries is None:
        gates.append(GateDecision("residence_country", GateResult.UNKNOWN, "Eligible residence countries are unknown."))
    elif profile.residence_country is None:
        gates.append(GateDecision("residence_country", GateResult.UNKNOWN, "Applicant residence country is unknown."))
    elif profile.residence_country.upper() in {c.upper() for c in opportunity.eligible_countries}:
        gates.append(GateDecision("residence_country", GateResult.PASS, "Applicant residence is eligible."))
    else:
        gates.append(GateDecision("residence_country", GateResult.FAIL, "Applicant residence is not in the eligible set."))
    if opportunity.age_min is None and opportunity.age_max is None:
        gates.append(GateDecision("age", GateResult.UNKNOWN, "No age rule extracted."))
    elif profile.age is None:
        gates.append(GateDecision("age", GateResult.UNKNOWN, "Applicant age is unknown."))
    else:
        fail = (opportunity.age_min is not None and profile.age < opportunity.age_min) or (opportunity.age_max is not None and profile.age > opportunity.age_max)
        gates.append(GateDecision("age", GateResult.FAIL if fail else GateResult.PASS, "Applicant age is outside the confirmed range." if fail else "Applicant age satisfies the confirmed range."))
    if opportunity.start_date and opportunity.end_date and profile.available_from and profile.available_to:
        ok = profile.available_from <= opportunity.start_date and profile.available_to >= opportunity.end_date
        gates.append(GateDecision("availability", GateResult.PASS if ok else GateResult.FAIL, "Confirmed availability covers activity dates." if ok else "Confirmed availability does not cover activity dates."))
    else:
        gates.append(GateDecision("availability", GateResult.UNKNOWN, "Availability or activity dates are incomplete."))
    if not opportunity.required_languages:
        gates.append(GateDecision("language", GateResult.PASS, "No mandatory language requirement extracted."))
    elif not profile.languages:
        gates.append(GateDecision("language", GateResult.UNKNOWN, "Applicant language evidence is incomplete."))
    elif opportunity.required_languages.issubset(profile.languages):
        gates.append(GateDecision("language", GateResult.PASS, "Mandatory language requirements are satisfied."))
    else:
        gates.append(GateDecision("language", GateResult.FAIL, "A mandatory language requirement is not satisfied."))
    return EligibilityDecision(result=_combine(gates), gates=gates)
