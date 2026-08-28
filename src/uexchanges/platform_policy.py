from __future__ import annotations

from dataclasses import dataclass

from .models import Opportunity


@dataclass(frozen=True)
class PlatformRequirements:
    requires_youth_work_context: bool = False
    decision_code: str | None = None
    rationale: str | None = None


PLATFORM_REQUIREMENTS: dict[str, PlatformRequirements] = {
    "salto_calendar": PlatformRequirements(
        requires_youth_work_context=True,
        decision_code="VERIFY_YOUTH_WORK_CONTEXT",
        rationale=(
            "SALTO European Training Calendar applicant guidance states that calls target "
            "youth workers/trainers or people already involved in the youth-work context."
        ),
    ),
}


def requirements_for_source(source_id: str) -> PlatformRequirements:
    return PLATFORM_REQUIREMENTS.get(source_id, PlatformRequirements())


def apply_platform_requirements(opportunity: Opportunity, source_id: str) -> Opportunity:
    """Apply deterministic platform requirements after canonical opportunity normalisation.

    This function only tightens requirements; it never relaxes call-specific constraints.
    """
    req = requirements_for_source(source_id)
    if req.requires_youth_work_context:
        opportunity.requires_youth_work_context = True
        opportunity.facts.setdefault("platform_eligibility_decision_code", req.decision_code)
        opportunity.facts.setdefault("platform_eligibility_rationale", req.rationale)
    return opportunity
