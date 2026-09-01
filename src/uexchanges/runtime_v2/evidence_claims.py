from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import ClaimRecord, ClaimStatus, EvidenceRecord, TemporalScope


@dataclass(frozen=True)
class ClaimDecision:
    status: ClaimStatus
    reason: str
    evidence_ids: tuple[str, ...]


class EvidenceClaimRegistry:
    """Fail-closed registry for external claims used in applications.

    The registry never infers a stronger temporal or role claim from weaker evidence.
    Evidence may be contextual without being sufficient to verify the claim.
    """

    def __init__(self) -> None:
        self.evidence: dict[str, EvidenceRecord] = {}
        self.claims: dict[str, ClaimRecord] = {}
        self.decisions: dict[str, ClaimDecision] = {}

    def add_evidence(self, evidence: EvidenceRecord) -> None:
        existing = self.evidence.get(evidence.evidence_id)
        if existing is not None and existing != evidence:
            raise ValueError(f"evidence_id collision: {evidence.evidence_id}")
        self.evidence[evidence.evidence_id] = evidence

    def evaluate_claim(self, claim: ClaimRecord, *, now: datetime | None = None) -> ClaimDecision:
        missing = tuple(eid for eid in claim.evidence_ids if eid not in self.evidence)
        if missing:
            return ClaimDecision(
                ClaimStatus.UNVERIFIED,
                f"Missing evidence: {', '.join(missing)}",
                claim.evidence_ids,
            )

        items = tuple(self.evidence[eid] for eid in claim.evidence_ids)
        wrong_application = tuple(
            item.evidence_id for item in items if item.application_id != claim.application_id
        )
        if wrong_application:
            return ClaimDecision(
                ClaimStatus.BLOCKED,
                "Evidence belongs to a different application.",
                wrong_application,
            )

        if now is not None:
            if now.tzinfo is None or now.utcoffset() is None:
                raise ValueError("now must be timezone-aware")
            if claim.valid_until is not None and now > claim.valid_until:
                return ClaimDecision(
                    ClaimStatus.SUPERSEDED,
                    "The claim validity window has expired.",
                    claim.evidence_ids,
                )
            if claim.valid_from is not None and now < claim.valid_from:
                return ClaimDecision(
                    ClaimStatus.UNVERIFIED,
                    "The claim is not yet valid.",
                    claim.evidence_ids,
                )

        prohibited = tuple(
            item.evidence_id
            for item in items
            if claim.claim_key in set(item.cannot_prove)
        )
        if prohibited:
            return ClaimDecision(
                ClaimStatus.BLOCKED,
                "One or more evidence items explicitly cannot prove this claim.",
                prohibited,
            )

        if claim.temporal_scope is TemporalScope.CURRENT and all(
            item.temporal_scope is TemporalScope.HISTORICAL for item in items
        ):
            return ClaimDecision(
                ClaimStatus.BLOCKED,
                "Historical evidence cannot prove a current-state claim.",
                claim.evidence_ids,
            )

        if claim.required_role != "*" and not any(
            claim.required_role in item.role_scopes or "*" in item.role_scopes
            for item in items
        ):
            return ClaimDecision(
                ClaimStatus.BLOCKED,
                f"No evidence is scoped to role {claim.required_role}.",
                claim.evidence_ids,
            )

        supporting = tuple(
            item.evidence_id
            for item in items
            if claim.claim_key in set(item.supports_claim_keys)
        )
        if not supporting:
            return ClaimDecision(
                ClaimStatus.UNVERIFIED,
                "Evidence exists but none explicitly supports this claim key.",
                claim.evidence_ids,
            )

        return ClaimDecision(
            ClaimStatus.VERIFIED,
            "Claim is supported within its temporal and role scope.",
            supporting,
        )

    def add_claim(self, claim: ClaimRecord, *, now: datetime | None = None) -> ClaimDecision:
        existing = self.claims.get(claim.claim_id)
        if existing is not None and existing != claim:
            raise ValueError(f"claim_id collision: {claim.claim_id}")
        decision = self.evaluate_claim(claim, now=now)
        self.claims[claim.claim_id] = claim
        self.decisions[claim.claim_id] = decision
        return decision

    def verified_claims(self, application_id: str) -> tuple[ClaimRecord, ...]:
        return tuple(
            claim
            for claim_id, claim in self.claims.items()
            if claim.application_id == application_id
            and self.decisions.get(claim_id, ClaimDecision(ClaimStatus.UNVERIFIED, "", ())).status
            is ClaimStatus.VERIFIED
        )
