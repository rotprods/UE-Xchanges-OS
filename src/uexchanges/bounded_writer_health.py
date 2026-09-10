"""Bounded health evidence for normal writer authorization.

The global control-plane health evaluator intentionally reports historical hygiene
findings. A normal writer, however, only needs fresh evidence for the SLOs that
WriterAuthorization requires for its intent. This module builds that bounded
view from the exact current session and currently-unexpired lease set without
claiming that historical hygiene was evaluated or is green.

It is observation-only. It never acquires a lease or mutates control-plane,
RuntimeGraph, provider, or domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from .bootstrap_guard import GuardCode, GuardDecision
from .control_plane_health import (
    ControlPlaneHealthReport,
    LeaseHealthRecord,
    SessionHealthRecord,
    evaluate_control_plane_health,
)

BOUNDED_WRITER_HEALTH_SCOPE = "CURRENT_WRITER_AND_UNEXPIRED_LEASES"


@dataclass(frozen=True)
class BoundedWriterHealthEvidence:
    """Scoped evidence plus the report consumed by WriterAuthorization."""

    report: ControlPlaneHealthReport
    bootstrap_codes: tuple[str, ...]
    scope: str = BOUNDED_WRITER_HEALTH_SCOPE
    historical_hygiene_evaluated: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "historical_hygiene_evaluated": self.historical_hygiene_evaluated,
            "bootstrap_codes": list(self.bootstrap_codes),
            "report": self.report.as_dict(),
        }


def evaluate_bounded_writer_authorization_health(
    *,
    now: datetime,
    current_session_id: str,
    current_session_rows: Sequence[SessionHealthRecord],
    bootstrap_decision: GuardDecision,
    currently_unexpired_leases: Sequence[LeaseHealthRecord],
    live_owner_session_rows: Sequence[SessionHealthRecord] = (),
) -> BoundedWriterHealthEvidence:
    """Build fail-closed health evidence for one proposed normal writer.

    ``current_session_rows`` must contain every exact stable-ID match for the
    newly generated session ID. Passing two rows deliberately makes the global
    evaluator's ``session_identity_uniqueness`` SLO fail. Passing zero rows is
    rejected because absence must never be interpreted as uniqueness.

    ``bootstrap_decision`` must be the real BootstrapGuard result for the exact
    current session/ACK/proposed lease/prelease evidence. A caller cannot replace
    it with a bare boolean. Only the canonical ``COMPLIANT`` decision counts as
    bootstrap-compliant for this bounded report.

    ``currently_unexpired_leases`` is a provider-side bounded read contract. A
    caller that supplies an already-expired lease has violated that contract and
    is rejected rather than silently filtering it away. Exact owner rows for
    active leases are included so orphan/mismatch fencing failures remain visible.

    The result is *not* a statement that historical session/lease hygiene,
    context freshness, projection freshness, or dead-letter budget is globally
    green. Callers must persist ``scope`` and ``historical_hygiene_evaluated``
    whenever they expose this report as authorization evidence.
    """

    if not current_session_id:
        raise ValueError("current_session_id is required")
    if not current_session_rows:
        raise ValueError("exact current-session lookup returned no rows")
    if any(row.session_id != current_session_id for row in current_session_rows):
        raise ValueError("current_session_rows contains a different session_id")
    if not isinstance(bootstrap_decision, GuardDecision):
        raise TypeError("bootstrap_decision must be a GuardDecision")
    if any(lease.expires_at <= now for lease in currently_unexpired_leases):
        raise ValueError("currently_unexpired_leases contains an expired lease")

    # Preserve duplicate current-session rows so the underlying deterministic
    # evaluator can fail session_identity_uniqueness. Dedupe only byte-for-byte
    # equivalent owner observations to avoid manufacturing duplicates when the
    # same exact owner row is requested for more than one live lease.
    sessions = list(current_session_rows)
    for owner in live_owner_session_rows:
        if owner not in sessions:
            sessions.append(owner)

    bootstrap_compliant = (
        bootstrap_decision.allowed
        and bootstrap_decision.codes == (GuardCode.COMPLIANT,)
    )
    report = evaluate_control_plane_health(
        now=now,
        sessions=tuple(sessions),
        leases=tuple(currently_unexpired_leases),
        bootstrap_noncompliant_count=0 if bootstrap_compliant else 1,
    )
    return BoundedWriterHealthEvidence(
        report=report,
        bootstrap_codes=tuple(code.value for code in bootstrap_decision.codes),
    )
