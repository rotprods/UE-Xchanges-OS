from __future__ import annotations

from .models import EligibilityDecision, GateResult, ScoreCard, ScoreComponent

DEFAULT_WEIGHTS = {
    "profile_fit": 22,
    "learning_value": 10,
    "contribution_fit": 13,
    "funding_value": 10,
    "career_leverage": 10,
    "trainer_progression": 12,
    "organisation_quality": 8,
    "selection_leverage": 8,
    "calendar_fit": 4,
    "application_effort": 3,
}

DEFAULT_FIT_WEIGHTS = {
    "thematic_interest": 25,
    "contribution_fit": 20,
    "learning_value": 15,
    "career_leverage": 15,
    "funding_value": 10,
    "organisation_quality": 10,
    "calendar_fit": 5,
}

EXECUTION_PRIORITY_WEIGHTS = {
    "fit_score": 45,
    "media_value": 20,
    "trainer_leverage": 20,
    "deadline_urgency": 15,
}


def band(total: float) -> str:
    if total >= 90:
        return "A+"
    if total >= 80:
        return "A"
    if total >= 70:
        return "B"
    if total >= 55:
        return "C"
    return "D"


def _weighted_score(ratings: dict[str, float], weights: dict[str, float]) -> ScoreCard:
    components: list[ScoreComponent] = []
    total = 0.0
    for name, weight in weights.items():
        raw = max(0.0, min(1.0, float(ratings.get(name, 0.0))))
        contribution = raw * weight
        total += contribution
        components.append(ScoreComponent(name=name, score=contribution, weight=weight))
    total = round(total, 2)
    return ScoreCard(total=total, band=band(total), components=components)


def score_fit(ratings: dict[str, float], *, weights: dict[str, float] | None = None) -> ScoreCard:
    """Strategic fit only. Deliberately independent of deadline and eligibility state."""
    return _weighted_score(ratings, weights or DEFAULT_FIT_WEIGHTS)


def score_execution_priority(
    eligibility: EligibilityDecision,
    *,
    fit_score: float,
    media_value: float,
    trainer_leverage: float,
    deadline_urgency: float,
) -> ScoreCard:
    """Choose the next operation, not whether submission is allowed.

    A known eligibility FAIL always returns zero. UNKNOWN may still have high priority,
    but that priority is for verification, never for submission.
    Input dimension values use the 0..100 scale.
    """
    if eligibility.result is GateResult.FAIL:
        return ScoreCard(
            total=0.0,
            band="BLOCKED",
            components=[],
            blocked_reason="Known eligibility hard gate failed.",
        )

    ratings = {
        "fit_score": fit_score / 100.0,
        "media_value": media_value / 100.0,
        "trainer_leverage": trainer_leverage / 100.0,
        "deadline_urgency": deadline_urgency / 100.0,
    }
    card = _weighted_score(ratings, EXECUTION_PRIORITY_WEIGHTS)
    if eligibility.result is GateResult.UNKNOWN:
        card.blocked_reason = "Eligibility unresolved: execution priority routes to verification only."
    return card


def score_opportunity(
    eligibility: EligibilityDecision,
    ratings: dict[str, float],
    *,
    weights: dict[str, float] | None = None,
) -> ScoreCard:
    """Backward-compatible gated opportunity score used by v0.1 callers.

    Prefer `score_fit` + `score_execution_priority` for new code.
    """
    if eligibility.result is GateResult.FAIL:
        return ScoreCard(
            total=0.0,
            band="BLOCKED",
            components=[],
            blocked_reason="Known eligibility hard gate failed.",
        )
    card = _weighted_score(ratings, weights or DEFAULT_WEIGHTS)
    if eligibility.result is GateResult.UNKNOWN:
        card.total = min(card.total, 79.9)
        card.total = round(card.total, 2)
        card.band = band(card.total)
        card.blocked_reason = "Eligibility unresolved: legacy score capped; verify before submission."
    return card
