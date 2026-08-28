from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OutcomeType(str, Enum):
    ACCEPTED_COMPLETED = "accepted_completed"
    ACCEPTED = "accepted"
    WAITLIST_PRIORITY = "waitlist_priority"
    REJECTED_WITH_FEEDBACK = "rejected_with_feedback"
    REJECTED_HIGH_COMPETITION = "rejected_high_competition"
    REJECTED_NO_REASON = "rejected_no_reason"
    NO_RESPONSE = "no_response"
    WITHDRAWN = "withdrawn"


class CausalStrength(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH_SPECIFIC = "high_specific"


@dataclass(frozen=True)
class OutcomeRecord:
    outcome_type: OutcomeType
    waitlist_rank: int | None = None
    competition_pool: int | None = None
    explicit_feedback: bool = False

    def __post_init__(self) -> None:
        if self.waitlist_rank is not None and self.waitlist_rank < 1:
            raise ValueError("waitlist_rank must be >= 1")
        if self.competition_pool is not None and self.competition_pool < 1:
            raise ValueError("competition_pool must be >= 1")
        if self.outcome_type is OutcomeType.WAITLIST_PRIORITY and self.waitlist_rank is None:
            raise ValueError("WAITLIST_PRIORITY requires waitlist_rank")


@dataclass(frozen=True)
class LearningPolicy:
    selection_signal: str
    causal_strength: CausalStrength
    update_positive_selection_prior: bool
    update_negative_selection_prior: bool
    update_competition_prior: bool
    update_criterion_heuristics: bool
    update_organisation_relationship_prior: bool
    update_organisation_response_prior: bool
    near_accept: bool
    forbidden_inferences: tuple[str, ...]
    reason: str


_COMMON_FORBIDDEN = (
    "infer_unstated_rejection_reason",
    "infer_skill_failure_without_feedback",
    "treat_historical_application_claim_as_verified_evidence",
)


def learning_policy(record: OutcomeRecord) -> LearningPolicy:
    """Return the *allowed* learning from one observed selection outcome.

    This deliberately does not estimate acceptance probability. With sparse outcomes,
    the safe operation is to control which priors/heuristics may be updated and which
    causal inferences are forbidden.
    """
    t = record.outcome_type

    if t is OutcomeType.ACCEPTED_COMPLETED:
        return LearningPolicy(
            selection_signal="positive_completed",
            causal_strength=CausalStrength.MEDIUM,
            update_positive_selection_prior=True,
            update_negative_selection_prior=False,
            update_competition_prior=False,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=True,
            update_organisation_response_prior=True,
            near_accept=False,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "infer_every_application_component_caused_acceptance",
            ),
            reason="Verified acceptance/completion supports a positive selection and organisation-relationship prior, not causal attribution to every application component.",
        )

    if t is OutcomeType.ACCEPTED:
        return LearningPolicy(
            selection_signal="positive",
            causal_strength=CausalStrength.MEDIUM,
            update_positive_selection_prior=True,
            update_negative_selection_prior=False,
            update_competition_prior=False,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=True,
            update_organisation_response_prior=True,
            near_accept=False,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "infer_every_application_component_caused_acceptance",
            ),
            reason="Acceptance is a positive selection signal but does not reveal which application component caused selection.",
        )

    if t is OutcomeType.WAITLIST_PRIORITY:
        rank = record.waitlist_rank or 1
        return LearningPolicy(
            selection_signal=f"near_accept_waitlist_{rank}",
            causal_strength=CausalStrength.LOW,
            update_positive_selection_prior=rank <= 3,
            update_negative_selection_prior=False,
            update_competition_prior=False,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=True,
            update_organisation_response_prior=True,
            near_accept=True,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "train_negative_application_penalty_from_waitlist",
            ),
            reason="A priority waitlist is evidence the application was competitive; it must never be treated as an ordinary rejection without explicit feedback.",
        )

    if t is OutcomeType.REJECTED_WITH_FEEDBACK:
        if not record.explicit_feedback:
            raise ValueError("REJECTED_WITH_FEEDBACK requires explicit_feedback=True")
        return LearningPolicy(
            selection_signal="negative_specific_feedback",
            causal_strength=CausalStrength.HIGH_SPECIFIC,
            update_positive_selection_prior=False,
            update_negative_selection_prior=True,
            update_competition_prior=record.competition_pool is not None,
            update_criterion_heuristics=True,
            update_organisation_relationship_prior=False,
            update_organisation_response_prior=True,
            near_accept=False,
            forbidden_inferences=(
                "generalise_specific_feedback_beyond_supported_criterion",
                "treat_feedback_as_universal_rule",
                "treat_historical_application_claim_as_verified_evidence",
            ),
            reason="Explicit organiser feedback may update the named criterion/heuristic, but remains call-specific evidence rather than a universal rule.",
        )

    if t is OutcomeType.REJECTED_HIGH_COMPETITION:
        return LearningPolicy(
            selection_signal="negative_low_causality_high_competition",
            causal_strength=CausalStrength.NONE,
            update_positive_selection_prior=False,
            update_negative_selection_prior=False,
            update_competition_prior=True,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=False,
            update_organisation_response_prior=True,
            near_accept=False,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "penalise_application_quality_from_high_competition_rejection",
            ),
            reason="A rejection in a large applicant pool without individual feedback informs competition/base rate only, not application-quality causes.",
        )

    if t is OutcomeType.REJECTED_NO_REASON:
        return LearningPolicy(
            selection_signal="negative_unknown_cause",
            causal_strength=CausalStrength.NONE,
            update_positive_selection_prior=False,
            update_negative_selection_prior=False,
            update_competition_prior=record.competition_pool is not None,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=False,
            update_organisation_response_prior=True,
            near_accept=False,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "penalise_application_quality_without_reason",
            ),
            reason="A rejection with no reason is an observed outcome but has insufficient causal evidence to alter application-quality heuristics.",
        )

    if t is OutcomeType.NO_RESPONSE:
        return LearningPolicy(
            selection_signal="unknown_selection_no_response",
            causal_strength=CausalStrength.NONE,
            update_positive_selection_prior=False,
            update_negative_selection_prior=False,
            update_competition_prior=False,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=False,
            update_organisation_response_prior=True,
            near_accept=False,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "treat_no_response_as_rejection",
            ),
            reason="No response informs organisation response behaviour only; it is not a verified selection rejection.",
        )

    if t is OutcomeType.WITHDRAWN:
        return LearningPolicy(
            selection_signal="no_selection_signal_withdrawn",
            causal_strength=CausalStrength.NONE,
            update_positive_selection_prior=False,
            update_negative_selection_prior=False,
            update_competition_prior=False,
            update_criterion_heuristics=False,
            update_organisation_relationship_prior=False,
            update_organisation_response_prior=False,
            near_accept=False,
            forbidden_inferences=_COMMON_FORBIDDEN + (
                "learn_selection_quality_from_withdrawn_application",
            ),
            reason="A withdrawn application has no usable selection-quality signal unless separate organiser feedback exists.",
        )

    raise ValueError(f"Unsupported outcome type: {t}")
