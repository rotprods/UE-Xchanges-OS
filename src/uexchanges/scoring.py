from __future__ import annotations
from .models import EligibilityDecision, GateResult, ScoreCard, ScoreComponent

DEFAULT_WEIGHTS = {"profile_fit":22,"learning_value":10,"contribution_fit":13,"funding_value":10,"career_leverage":10,"trainer_progression":12,"organisation_quality":8,"selection_leverage":8,"calendar_fit":4,"application_effort":3}

def band(total: float) -> str:
    if total >= 90: return "A+"
    if total >= 80: return "A"
    if total >= 70: return "B"
    if total >= 55: return "C"
    return "D"

def score_opportunity(eligibility: EligibilityDecision, ratings: dict[str,float], *, weights: dict[str,float] | None = None) -> ScoreCard:
    if eligibility.result is GateResult.FAIL:
        return ScoreCard(total=0.0, band="BLOCKED", components=[], blocked_reason="Known eligibility hard gate failed.")
    weights = weights or DEFAULT_WEIGHTS
    components=[]; total=0.0
    for name, weight in weights.items():
        raw=max(0.0,min(1.0,float(ratings.get(name,0.0))))
        contribution=raw*weight; total+=contribution
        components.append(ScoreComponent(name=name,score=contribution,weight=weight))
    if eligibility.result is GateResult.UNKNOWN: total=min(total,79.9)
    total=round(total,2)
    return ScoreCard(total=total,band=band(total),components=components)
