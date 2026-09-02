"""Deterministic health/SLO evaluation for the UE-Xchanges control plane.

This module is intentionally observation-only.  It classifies effective session/
lease health, freshness and control-plane SLOs from already captured snapshots.
It never mutates Drive, GitHub, RuntimeGraph, provider sessions or domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Sequence


class HealthSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OverallHealth(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class EffectiveLeaseState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED_STALE_ROW = "EXPIRED_STALE_ROW"
    ORPHANED_OWNER_MISSING = "ORPHANED_OWNER_MISSING"
    ORPHANED_OWNER_CLOSED = "ORPHANED_OWNER_CLOSED"


class HealthCode(str, Enum):
    SESSION_ID_REUSED = "SESSION_ID_REUSED"
    SESSION_HEARTBEAT_STALE = "SESSION_HEARTBEAT_STALE"
    ACTIVE_LEASE_EXPIRED_STALE_ROW = "ACTIVE_LEASE_EXPIRED_STALE_ROW"
    ACTIVE_LEASE_OWNER_MISSING = "ACTIVE_LEASE_OWNER_MISSING"
    ACTIVE_LEASE_OWNER_CLOSED = "ACTIVE_LEASE_OWNER_CLOSED"
    LEASE_AGENT_MISMATCH = "LEASE_AGENT_MISMATCH"
    LEASE_CONTEXT_MISMATCH = "LEASE_CONTEXT_MISMATCH"
    LEASE_SCOPE_EMPTY = "LEASE_SCOPE_EMPTY"
    LEASE_HEARTBEAT_STALE = "LEASE_HEARTBEAT_STALE"
    CONTEXT_REGISTRY_STALE = "CONTEXT_REGISTRY_STALE"
    PROJECTION_STALE = "PROJECTION_STALE"
    BOOTSTRAP_NONCOMPLIANT = "BOOTSTRAP_NONCOMPLIANT"
    DEAD_LETTER_PRESENT = "DEAD_LETTER_PRESENT"


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


@dataclass(frozen=True)
class SessionHealthRecord:
    session_id: str
    agent_id: str
    context_id: str
    started_at: datetime
    last_heartbeat: datetime
    status: str

    def __post_init__(self) -> None:
        if not self.session_id or not self.agent_id or not self.context_id:
            raise ValueError("session identity fields are required")
        _aware(self.started_at, "started_at")
        _aware(self.last_heartbeat, "last_heartbeat")
        if self.last_heartbeat < self.started_at:
            raise ValueError("last_heartbeat cannot precede started_at")

    @property
    def active(self) -> bool:
        return self.status == "ACTIVE"


@dataclass(frozen=True)
class LeaseHealthRecord:
    lease_id: str
    owner_session_id: str
    owner_agent_id: str
    context_id: str
    scope: str
    acquired_at: datetime
    expires_at: datetime
    last_heartbeat: datetime
    status: str

    def __post_init__(self) -> None:
        if not self.lease_id or not self.owner_session_id or not self.owner_agent_id:
            raise ValueError("lease identity fields are required")
        if not self.context_id:
            raise ValueError("lease context_id is required")
        _aware(self.acquired_at, "acquired_at")
        _aware(self.expires_at, "expires_at")
        _aware(self.last_heartbeat, "last_heartbeat")
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be after acquired_at")
        if self.last_heartbeat < self.acquired_at:
            raise ValueError("last_heartbeat cannot precede acquired_at")


@dataclass(frozen=True)
class ContextHealthRecord:
    context_id: str
    updated_at: datetime
    status: str
    last_event_id: str = ""

    def __post_init__(self) -> None:
        if not self.context_id:
            raise ValueError("context_id is required")
        _aware(self.updated_at, "updated_at")


@dataclass(frozen=True)
class ProjectionHealthRecord:
    name: str
    generated_at: datetime
    watermark: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("projection name is required")
        _aware(self.generated_at, "generated_at")


@dataclass(frozen=True)
class HealthPolicy:
    session_heartbeat_max_age_seconds: int = 30 * 60
    lease_heartbeat_max_age_seconds: int = 20 * 60
    context_max_age_seconds: int = 24 * 60 * 60
    projection_max_age_seconds: int = 30 * 60

    def __post_init__(self) -> None:
        for field_name in (
            "session_heartbeat_max_age_seconds",
            "lease_heartbeat_max_age_seconds",
            "context_max_age_seconds",
            "projection_max_age_seconds",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be positive")

    @property
    def session_heartbeat_max_age(self) -> timedelta:
        return timedelta(seconds=self.session_heartbeat_max_age_seconds)

    @property
    def lease_heartbeat_max_age(self) -> timedelta:
        return timedelta(seconds=self.lease_heartbeat_max_age_seconds)

    @property
    def context_max_age(self) -> timedelta:
        return timedelta(seconds=self.context_max_age_seconds)

    @property
    def projection_max_age(self) -> timedelta:
        return timedelta(seconds=self.projection_max_age_seconds)


@dataclass(frozen=True)
class HealthFinding:
    code: HealthCode
    severity: HealthSeverity
    subject_type: str
    subject_id: str
    detail: str
    repair_action: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "detail": self.detail,
            "repair_action": self.repair_action,
        }


@dataclass(frozen=True)
class SloResult:
    name: str
    passed: bool
    observed: int | float
    target: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "observed": self.observed,
            "target": self.target,
        }


@dataclass(frozen=True)
class ControlPlaneHealthReport:
    generated_at: datetime
    overall: OverallHealth
    findings: tuple[HealthFinding, ...]
    metrics: dict[str, int]
    slos: tuple[SloResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "report_type": "control_plane_health_v1",
            "generated_at": self.generated_at.isoformat(),
            "overall": self.overall.value,
            "metrics": dict(sorted(self.metrics.items())),
            "slos": [item.as_dict() for item in self.slos],
            "findings": [item.as_dict() for item in self.findings],
        }


def effective_lease_state(
    lease: LeaseHealthRecord,
    *,
    session: SessionHealthRecord | None,
    now: datetime,
) -> EffectiveLeaseState:
    """Resolve the effective lease state without rewriting the source row."""

    _aware(now, "now")
    if lease.status != "ACTIVE":
        return EffectiveLeaseState.RELEASED
    if session is None:
        return EffectiveLeaseState.ORPHANED_OWNER_MISSING
    if not session.active:
        return EffectiveLeaseState.ORPHANED_OWNER_CLOSED
    if lease.expires_at <= now:
        return EffectiveLeaseState.EXPIRED_STALE_ROW
    return EffectiveLeaseState.ACTIVE


def _dedupe_findings(findings: Iterable[HealthFinding]) -> tuple[HealthFinding, ...]:
    seen: set[tuple[HealthCode, str, str]] = set()
    ordered: list[HealthFinding] = []
    for finding in findings:
        key = (finding.code, finding.subject_type, finding.subject_id)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(finding)
    return tuple(ordered)


def _overall(findings: Sequence[HealthFinding]) -> OverallHealth:
    severities = {finding.severity for finding in findings}
    if HealthSeverity.CRITICAL in severities or HealthSeverity.ERROR in severities:
        return OverallHealth.RED
    if HealthSeverity.WARNING in severities:
        return OverallHealth.AMBER
    return OverallHealth.GREEN


def evaluate_control_plane_health(
    *,
    now: datetime,
    sessions: Sequence[SessionHealthRecord],
    leases: Sequence[LeaseHealthRecord],
    contexts: Sequence[ContextHealthRecord] = (),
    projections: Sequence[ProjectionHealthRecord] = (),
    bootstrap_noncompliant_count: int = 0,
    dead_letter_count: int = 0,
    policy: HealthPolicy | None = None,
) -> ControlPlaneHealthReport:
    """Evaluate current control-plane health and SLOs from immutable snapshots."""

    _aware(now, "now")
    if bootstrap_noncompliant_count < 0 or dead_letter_count < 0:
        raise ValueError("counts cannot be negative")
    policy = policy or HealthPolicy()
    findings: list[HealthFinding] = []

    grouped_sessions: dict[str, list[SessionHealthRecord]] = {}
    for session in sessions:
        grouped_sessions.setdefault(session.session_id, []).append(session)

    duplicate_session_ids = 0
    for session_id, rows in grouped_sessions.items():
        if len(rows) > 1:
            duplicate_session_ids += 1
            findings.append(
                HealthFinding(
                    HealthCode.SESSION_ID_REUSED,
                    HealthSeverity.CRITICAL,
                    "session",
                    session_id,
                    f"session_id appears {len(rows)} times",
                    "create a fresh session ID; never reuse a historical writer identity",
                )
            )

    session_by_id = {
        session_id: rows[-1]
        for session_id, rows in grouped_sessions.items()
        if len(rows) == 1
    }

    stale_active_sessions = 0
    for session in sessions:
        if session.active and now - session.last_heartbeat > policy.session_heartbeat_max_age:
            stale_active_sessions += 1
            findings.append(
                HealthFinding(
                    HealthCode.SESSION_HEARTBEAT_STALE,
                    HealthSeverity.WARNING,
                    "session",
                    session.session_id,
                    f"last heartbeat is {(now - session.last_heartbeat).total_seconds():.0f}s old",
                    "refresh heartbeat or close/supersede the session explicitly",
                )
            )

    stale_active_lease_rows = 0
    orphaned_active_lease_rows = 0
    effective_active_leases = 0
    lease_integrity_failures = 0

    for lease in leases:
        owner = session_by_id.get(lease.owner_session_id)
        state = effective_lease_state(lease, session=owner, now=now)
        if state is EffectiveLeaseState.ACTIVE:
            effective_active_leases += 1
        elif state is EffectiveLeaseState.EXPIRED_STALE_ROW:
            stale_active_lease_rows += 1
            findings.append(
                HealthFinding(
                    HealthCode.ACTIVE_LEASE_EXPIRED_STALE_ROW,
                    HealthSeverity.WARNING,
                    "lease",
                    lease.lease_id,
                    f"row says ACTIVE but expired at {lease.expires_at.isoformat()}",
                    "append/reconcile an expiry or release event; do not treat the row as a live fence",
                )
            )
        elif state is EffectiveLeaseState.ORPHANED_OWNER_MISSING:
            orphaned_active_lease_rows += 1
            findings.append(
                HealthFinding(
                    HealthCode.ACTIVE_LEASE_OWNER_MISSING,
                    HealthSeverity.ERROR,
                    "lease",
                    lease.lease_id,
                    "ACTIVE lease has no matching owner session",
                    "quarantine the lease row and reconcile its provenance before any overlapping write",
                )
            )
        elif state is EffectiveLeaseState.ORPHANED_OWNER_CLOSED:
            orphaned_active_lease_rows += 1
            findings.append(
                HealthFinding(
                    HealthCode.ACTIVE_LEASE_OWNER_CLOSED,
                    HealthSeverity.WARNING,
                    "lease",
                    lease.lease_id,
                    f"row says ACTIVE while owner session is {owner.status if owner else 'missing'}",
                    "reconcile the lease row from later release/completion evidence",
                )
            )

        if owner is not None:
            if lease.owner_agent_id != owner.agent_id:
                lease_integrity_failures += 1
                findings.append(
                    HealthFinding(
                        HealthCode.LEASE_AGENT_MISMATCH,
                        HealthSeverity.CRITICAL,
                        "lease",
                        lease.lease_id,
                        "lease owner agent does not match the session agent",
                        "deny the lease and reconstruct ownership from authoritative events",
                    )
                )
            if lease.context_id != owner.context_id:
                lease_integrity_failures += 1
                findings.append(
                    HealthFinding(
                        HealthCode.LEASE_CONTEXT_MISMATCH,
                        HealthSeverity.CRITICAL,
                        "lease",
                        lease.lease_id,
                        "lease context differs from owner session context",
                        "deny the lease and create a correctly scoped lease",
                    )
                )

        if not lease.scope.strip():
            lease_integrity_failures += 1
            findings.append(
                HealthFinding(
                    HealthCode.LEASE_SCOPE_EMPTY,
                    HealthSeverity.CRITICAL,
                    "lease",
                    lease.lease_id,
                    "lease has no resource scope",
                    "deny the lease and require an explicit minimal resource scope",
                )
            )

        if state is EffectiveLeaseState.ACTIVE and now - lease.last_heartbeat > policy.lease_heartbeat_max_age:
            findings.append(
                HealthFinding(
                    HealthCode.LEASE_HEARTBEAT_STALE,
                    HealthSeverity.WARNING,
                    "lease",
                    lease.lease_id,
                    f"lease heartbeat is {(now - lease.last_heartbeat).total_seconds():.0f}s old",
                    "refresh the lease heartbeat or release it before continuing writes",
                )
            )

    stale_contexts = 0
    for context in contexts:
        if context.status == "ACTIVE" and now - context.updated_at > policy.context_max_age:
            stale_contexts += 1
            findings.append(
                HealthFinding(
                    HealthCode.CONTEXT_REGISTRY_STALE,
                    HealthSeverity.WARNING,
                    "context",
                    context.context_id,
                    f"context registry record is {(now - context.updated_at).total_seconds():.0f}s old",
                    "refresh the context registry watermark/notes from current main and Event Bus without copying volatile projections",
                )
            )

    stale_projections = 0
    for projection in projections:
        if now - projection.generated_at > policy.projection_max_age:
            stale_projections += 1
            findings.append(
                HealthFinding(
                    HealthCode.PROJECTION_STALE,
                    HealthSeverity.ERROR,
                    "projection",
                    projection.name,
                    f"projection is {(now - projection.generated_at).total_seconds():.0f}s old (watermark={projection.watermark})",
                    "recompute the derived projection from current canonical evidence; do not patch cells by assumption",
                )
            )

    if bootstrap_noncompliant_count:
        findings.append(
            HealthFinding(
                HealthCode.BOOTSTRAP_NONCOMPLIANT,
                HealthSeverity.CRITICAL,
                "bootstrap",
                "active_writers",
                f"{bootstrap_noncompliant_count} active writer(s) are non-compliant",
                "block new write claims for those sessions until BootstrapGuard passes",
            )
        )

    if dead_letter_count:
        findings.append(
            HealthFinding(
                HealthCode.DEAD_LETTER_PRESENT,
                HealthSeverity.ERROR,
                "runtime",
                "dead_letters",
                f"{dead_letter_count} unresolved dead-letter item(s)",
                "inspect poison/unroutable events and resolve or explicitly quarantine them",
            )
        )

    findings_tuple = _dedupe_findings(findings)
    metrics = {
        "sessions": len(sessions),
        "active_sessions": sum(1 for value in sessions if value.active),
        "duplicate_session_ids": duplicate_session_ids,
        "stale_active_sessions": stale_active_sessions,
        "leases": len(leases),
        "effective_active_leases": effective_active_leases,
        "stale_active_lease_rows": stale_active_lease_rows,
        "orphaned_active_lease_rows": orphaned_active_lease_rows,
        "lease_integrity_failures": lease_integrity_failures,
        "stale_contexts": stale_contexts,
        "stale_projections": stale_projections,
        "bootstrap_noncompliant": bootstrap_noncompliant_count,
        "dead_letters": dead_letter_count,
    }

    slos = (
        SloResult("bootstrap_compliance", bootstrap_noncompliant_count == 0, bootstrap_noncompliant_count, "0 non-compliant active writers"),
        SloResult("session_identity_uniqueness", duplicate_session_ids == 0, duplicate_session_ids, "0 reused session IDs"),
        SloResult("lease_fencing_integrity", lease_integrity_failures == 0 and orphaned_active_lease_rows == 0, lease_integrity_failures + orphaned_active_lease_rows, "0 orphaned/mismatched active leases"),
        SloResult("lease_row_hygiene", stale_active_lease_rows == 0, stale_active_lease_rows, "0 expired rows still marked ACTIVE"),
        SloResult("context_freshness", stale_contexts == 0, stale_contexts, "0 ACTIVE contexts older than policy TTL"),
        SloResult("projection_freshness", stale_projections == 0, stale_projections, "0 projections older than policy SLA"),
        SloResult("dead_letter_budget", dead_letter_count == 0, dead_letter_count, "0 unresolved dead letters"),
    )

    return ControlPlaneHealthReport(
        generated_at=now,
        overall=_overall(findings_tuple),
        findings=findings_tuple,
        metrics=metrics,
        slos=slos,
    )
