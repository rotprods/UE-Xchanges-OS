from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from itertools import combinations


class PortfolioState(str, Enum):
    CANDIDATE = "candidate"
    APPLIED = "applied"
    ACCEPTED = "accepted"
    COMMITTED = "committed"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"
    EXPIRED = "expired"


ACTIVE_CONFLICT_STATES = {
    PortfolioState.CANDIDATE,
    PortfolioState.APPLIED,
    PortfolioState.ACCEPTED,
    PortfolioState.COMMITTED,
}

COMMITMENT_CONFLICT_STATES = {
    PortfolioState.ACCEPTED,
    PortfolioState.COMMITTED,
}


@dataclass(frozen=True)
class OpportunityWindow:
    opportunity_id: str
    start_date: date
    end_date: date
    state: PortfolioState = PortfolioState.CANDIDATE

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")


@dataclass(frozen=True)
class ConflictEdge:
    left_id: str
    right_id: str
    edge_type: str = "MUTUALLY_EXCLUSIVE_IF_ACCEPTED"


@dataclass(frozen=True)
class CommitmentDecision:
    allowed: bool
    action: str
    decision_code: str
    conflicting_ids: tuple[str, ...]
    reason: str


def intervals_overlap(left: OpportunityWindow, right: OpportunityWindow) -> bool:
    """Inclusive date overlap: end 16 / start 16 conflicts; end 16 / start 17 does not."""
    return left.start_date <= right.end_date and right.start_date <= left.end_date


def build_conflict_edges(windows: list[OpportunityWindow]) -> list[ConflictEdge]:
    """Create deterministic pairwise conflict edges without blocking applications."""
    active = [window for window in windows if window.state in ACTIVE_CONFLICT_STATES]
    edges: list[ConflictEdge] = []
    for left, right in combinations(sorted(active, key=lambda item: item.opportunity_id), 2):
        if intervals_overlap(left, right):
            edges.append(ConflictEdge(left.opportunity_id, right.opportunity_id))
    return edges


def evaluate_commitment(target_id: str, windows: list[OpportunityWindow]) -> CommitmentDecision:
    """Guard the ACCEPTED -> COMMITTED transition.

    Applying to or receiving acceptance from overlapping opportunities is allowed so the
    applicant keeps option value. A commitment is blocked until every overlapping
    ACCEPTED/COMMITTED alternative is explicitly resolved.
    """
    by_id = {window.opportunity_id: window for window in windows}
    if target_id not in by_id:
        raise KeyError(f"Unknown opportunity_id: {target_id}")

    target = by_id[target_id]
    conflicts = sorted(
        other.opportunity_id
        for other in windows
        if other.opportunity_id != target_id
        and other.state in COMMITMENT_CONFLICT_STATES
        and intervals_overlap(target, other)
    )
    if conflicts:
        return CommitmentDecision(
            allowed=False,
            action="PORTFOLIO_RESOLUTION",
            decision_code="RESOLVE_MUTUALLY_EXCLUSIVE_ACCEPTANCE",
            conflicting_ids=tuple(conflicts),
            reason="An overlapping accepted/committed mobility must be resolved before commitment.",
        )
    return CommitmentDecision(
        allowed=True,
        action="COMMIT",
        decision_code="COMMIT_NO_ACTIVE_PORTFOLIO_CONFLICT",
        conflicting_ids=(),
        reason="No overlapping accepted/committed mobility blocks commitment.",
    )
