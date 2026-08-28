from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FactClaim:
    fact_key: str
    value: Any
    source_id: str
    authority_rank: int
    observed_at: datetime
    live_current: bool = False


@dataclass(frozen=True)
class FactResolution:
    resolved: bool
    value: Any | None
    decision_code: str
    winning_source_id: str | None
    conflicting_source_ids: tuple[str, ...]
    reason: str


def resolve_fact_claims(claims: list[FactClaim]) -> FactResolution:
    """Resolve one fact using explicit authority/freshness dominance only.

    Rules:
    - Empty input is unresolved.
    - Claims must refer to exactly one fact key.
    - Equal values are resolved to the highest-authority/newest source.
    - Conflicting values may auto-resolve only when one live-current claim has the
      highest authority and is strictly newer than every conflicting claim at that
      authority level.
    - Otherwise preserve verification debt.
    """
    if not claims:
        return FactResolution(False, None, "VERIFY_MISSING_FACT", None, (), "No source claim exists.")
    fact_keys = {claim.fact_key for claim in claims}
    if len(fact_keys) != 1:
        raise ValueError("All claims must refer to the same fact_key")

    values = {repr(claim.value) for claim in claims}
    ranked = sorted(claims, key=lambda claim: (claim.authority_rank, claim.observed_at), reverse=True)
    if len(values) == 1:
        winner = ranked[0]
        return FactResolution(
            True,
            winner.value,
            "RESOLVE_CONSISTENT_FACT",
            winner.source_id,
            (),
            "All available source claims agree.",
        )

    highest_authority = max(claim.authority_rank for claim in claims)
    top = [claim for claim in claims if claim.authority_rank == highest_authority]
    top_live = [claim for claim in top if claim.live_current]
    if len(top_live) == 1:
        winner = top_live[0]
        conflicting_top = [claim for claim in top if repr(claim.value) != repr(winner.value)]
        if all(winner.observed_at > claim.observed_at for claim in conflicting_top):
            conflicts = tuple(sorted(claim.source_id for claim in claims if repr(claim.value) != repr(winner.value)))
            return FactResolution(
                True,
                winner.value,
                "LIVE_SOURCE_SUPERSEDES_STALE_ARTIFACT",
                winner.source_id,
                conflicts,
                "A unique live-current highest-authority claim is strictly newer than conflicting peer claims.",
            )

    return FactResolution(
        False,
        None,
        "VERIFY_CONFLICTING_FACT",
        None,
        tuple(sorted(claim.source_id for claim in claims)),
        "Conflicting claims lack a safe authority/freshness dominance rule.",
    )
