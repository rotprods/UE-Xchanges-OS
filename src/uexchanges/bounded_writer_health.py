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

from .bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
    authorize_lease,
)
from .control_plane_health import (
    ControlPlaneHealthReport,
    LeaseHealthRecord,
    SessionHealthRecord,
    evaluate_control_plane_health,
)

BOUNDED_WRITER_HEALTH_SCOPE = "CURRENT_WRITER_AND_UNEXPIRED_LEASES"


@dataclass(frozen=True)
class LiveWriterBootstrapEvidence:
    """Exact bootstrap evidence for one already-live ACTIVE lease."""

    session: SessionSnapshot
    ack: BootstrapAckSnapshot | None
    lease: LeaseSnapshot
    prelease: PreLeaseRefresh | None


@dataclass(frozen=True)
class BoundedWriterHealthEvidence:
    """Scoped evidence plus the report consumed by WriterAuthorization."""

    report: ControlPlaneHealthReport
    bootstrap_codes: tuple[str, ...]
    bootstrap_noncompliant_session_ids: tuple[str, ...]
    scope: str = BOUNDED_WRITER_HEALTH_SCOPE
    historical_hygiene_evaluated: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "historical_hygiene_evaluated": self.historical_hygiene_evaluated,
            "bootstrap_codes": list(self.bootstrap_codes),
            "bootstrap_noncompliant_session_ids": list(
                self.bootstrap_noncompliant_session_ids
            ),
            "report": self.report.as_dict(),
        }


def _assert_same_live_lease(
    health: LeaseHealthRecord,
    bootstrap: LeaseSnapshot,
) -> None:
    comparable = (
        "lease_id",
        "owner_session_id",
        "owner_agent_id",
        "context_id",
        "scope",
        "acquired_at",
        "expires_at",
        "status",
    )
    if any(getattr(health, field) != getattr(bootstrap, field) for field in comparable):
        raise ValueError("live lease bootstrap evidence disagrees with health lease")


def evaluate_bounded_writer_authorization_health(
    *,
    now: datetime,
    current_session_id: str,
    current_session_rows: Sequence[SessionHealthRecord],
    bootstrap_policy: BootstrapPolicy,
    bootstrap_session: SessionSnapshot,
    bootstrap_ack: BootstrapAckSnapshot | None,
    proposed_lease: LeaseSnapshot,
    prelease: PreLeaseRefresh | None,
    currently_unexpired_leases: Sequence[LeaseHealthRecord],
    live_owner_session_rows: Sequence[SessionHealthRecord] = (),
    live_writer_bootstrap_evidence: Sequence[LiveWriterBootstrapEvidence] = (),
) -> BoundedWriterHealthEvidence:
    """Build fail-closed health evidence for one proposed normal writer.

    ``current_session_rows`` must contain every exact stable-ID match for the
    newly generated session ID. Passing two rows deliberately makes the global
    evaluator's ``session_identity_uniqueness`` SLO fail. Passing zero rows is
    rejected because absence must never be interpreted as uniqueness.

    Bootstrap compliance is not accepted as a caller-provided boolean or
    precomputed decision. This function invokes the canonical ``authorize_lease``
    BootstrapGuard for the proposed writer and for every already-live ACTIVE
    lease. The live evidence set must match the ACTIVE/unexpired lease IDs exactly;
    missing, extra, duplicate, or identity-drifted evidence is rejected.

    ``currently_unexpired_leases`` is a provider-side bounded read contract. A
    caller that supplies an already-expired lease has violated that contract and
    is rejected rather than silently filtering it away. Exact owner rows for
    live leases are included so orphan/mismatch fencing failures remain visible.

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
    if bootstrap_session.session_id != current_session_id:
        raise ValueError("bootstrap_session does not match current_session_id")
    if any(
        row.agent_id != bootstrap_session.agent_id
        or row.context_id != bootstrap_session.context_id
        for row in current_session_rows
    ):
        raise ValueError("current-session registry identity disagrees with bootstrap session")
    if any(lease.expires_at <= now for lease in currently_unexpired_leases):
        raise ValueError("currently_unexpired_leases contains an expired lease")

    current_bootstrap = authorize_lease(
        policy=bootstrap_policy,
        session=bootstrap_session,
        ack=bootstrap_ack,
        lease=proposed_lease,
        now=now,
        prelease=prelease,
    )

    active_health_by_id = {
        lease.lease_id: lease
        for lease in currently_unexpired_leases
        if lease.status == "ACTIVE"
    }
    evidence_by_id: dict[str, LiveWriterBootstrapEvidence] = {}
    for item in live_writer_bootstrap_evidence:
        lease_id = item.lease.lease_id
        if lease_id in evidence_by_id:
            raise ValueError("duplicate live writer bootstrap evidence")
        evidence_by_id[lease_id] = item

    if set(evidence_by_id) != set(active_health_by_id):
        raise ValueError("live writer bootstrap evidence must match ACTIVE lease IDs exactly")

    noncompliant_sessions: set[str] = set()
    if not current_bootstrap.allowed:
        noncompliant_sessions.add(bootstrap_session.session_id)

    for lease_id, item in evidence_by_id.items():
        health_lease = active_health_by_id[lease_id]
        _assert_same_live_lease(health_lease, item.lease)
        if item.session.session_id != health_lease.owner_session_id:
            raise ValueError("live bootstrap session does not own health lease")
        decision = authorize_lease(
            policy=bootstrap_policy,
            session=item.session,
            ack=item.ack,
            lease=item.lease,
            now=now,
            prelease=item.prelease,
        )
        if not decision.allowed:
            noncompliant_sessions.add(item.session.session_id)

    # Preserve duplicate current-session rows so the deterministic health
    # evaluator can fail session_identity_uniqueness. Dedupe only byte-for-byte
    # equivalent owner observations to avoid manufacturing duplicates when the
    # same exact owner row is requested for more than one live lease.
    sessions = list(current_session_rows)
    for owner in live_owner_session_rows:
        if owner not in sessions:
            sessions.append(owner)

    report = evaluate_control_plane_health(
        now=now,
        sessions=tuple(sessions),
        leases=tuple(currently_unexpired_leases),
        bootstrap_noncompliant_count=len(noncompliant_sessions),
    )
    return BoundedWriterHealthEvidence(
        report=report,
        bootstrap_codes=tuple(code.value for code in current_bootstrap.codes),
        bootstrap_noncompliant_session_ids=tuple(sorted(noncompliant_sessions)),
    )
