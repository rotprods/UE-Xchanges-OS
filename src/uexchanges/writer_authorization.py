"""Fail-closed coordination authorization for UE-Xchanges writers.

The broker composes BootstrapGuard with current health/SLO evidence and an
explicit overlap inventory.  It never acquires a lease, mutates a provider or
confers domain/external-side-effect authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Sequence

from .bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    GuardDecision,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
    authorize_lease,
)
from .control_plane_health import (
    ControlPlaneHealthReport,
    HealthCode,
    HealthSeverity,
)

_REPAIR_PLAN = re.compile(r"^RPL-[0-9a-f]{16}$")


class WriteIntent(str, Enum):
    VERSIONED_CODE = "VERSIONED_CODE"
    CONTROL_PLANE_REPAIR = "CONTROL_PLANE_REPAIR"
    DERIVED_PROJECTION = "DERIVED_PROJECTION"
    CANONICAL_DOMAIN = "CANONICAL_DOMAIN"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"


class AuthorizationCode(str, Enum):
    ALLOWED = "ALLOWED"
    BOOTSTRAP_DENIED = "BOOTSTRAP_DENIED"
    HEALTH_REPORT_STALE = "HEALTH_REPORT_STALE"
    REQUIRED_SLO_FAILED = "REQUIRED_SLO_FAILED"
    SUBJECT_HEALTH_BLOCKER = "SUBJECT_HEALTH_BLOCKER"
    OVERLAPPING_LEASE = "OVERLAPPING_LEASE"
    REPAIR_PLAN_REQUIRED = "REPAIR_PLAN_REQUIRED"
    EXTERNAL_SIDE_EFFECT_REQUIRES_SEPARATE_CAPABILITY = "EXTERNAL_SIDE_EFFECT_REQUIRES_SEPARATE_CAPABILITY"


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


@dataclass(frozen=True)
class WriterAuthorizationPolicy:
    bootstrap: BootstrapPolicy
    max_health_report_age_seconds: int = 120

    def __post_init__(self) -> None:
        if self.max_health_report_age_seconds <= 0:
            raise ValueError("max_health_report_age_seconds must be positive")

    @property
    def max_health_report_age(self) -> timedelta:
        return timedelta(seconds=self.max_health_report_age_seconds)


@dataclass(frozen=True)
class WriterAuthorizationDecision:
    coordination_allowed: bool
    intent: WriteIntent
    codes: tuple[AuthorizationCode, ...]
    bootstrap: GuardDecision
    failed_slos: tuple[str, ...]
    health_blockers: tuple[str, ...]
    overlapping_lease_ids: tuple[str, ...]
    evaluated_at: datetime
    decision_digest: str
    repair_plan_id: str | None = None

    def __post_init__(self) -> None:
        _aware(self.evaluated_at, "evaluated_at")
        if not self.codes:
            raise ValueError("authorization codes are required")
        if not re.fullmatch(r"[0-9a-f]{64}", self.decision_digest):
            raise ValueError("decision_digest must be 64 lowercase hex chars")
        if self.coordination_allowed and self.codes != (AuthorizationCode.ALLOWED,):
            raise ValueError("allowed decision must contain only ALLOWED")

    @property
    def is_domain_authority(self) -> bool:
        return False

    @property
    def is_external_capability(self) -> bool:
        return False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "UEX_WRITER_AUTHORIZATION",
            "version": "1.0.0",
            "coordination_allowed": self.coordination_allowed,
            "intent": self.intent.value,
            "codes": [code.value for code in self.codes],
            "bootstrap": self.bootstrap.as_dict(),
            "failed_slos": list(self.failed_slos),
            "health_blockers": list(self.health_blockers),
            "overlapping_lease_ids": list(self.overlapping_lease_ids),
            "evaluated_at": self.evaluated_at.isoformat(),
            "decision_digest": self.decision_digest,
            "repair_plan_id": self.repair_plan_id,
            "domain_authority": false_value(),
            "external_capability": false_value(),
        }


def false_value() -> bool:
    """Named helper makes the non-authority fields hard to accidentally invert."""

    return False


_BASE_SLOS = (
    "bootstrap_compliance",
    "session_identity_uniqueness",
    "lease_fencing_integrity",
)

_INTENT_SLOS: dict[WriteIntent, tuple[str, ...]] = {
    WriteIntent.VERSIONED_CODE: _BASE_SLOS,
    WriteIntent.CONTROL_PLANE_REPAIR: (),
    WriteIntent.DERIVED_PROJECTION: _BASE_SLOS,
    WriteIntent.CANONICAL_DOMAIN: _BASE_SLOS + ("context_freshness",),
    WriteIntent.EXTERNAL_SIDE_EFFECT: (),
}

_SUBJECT_BLOCKING_CODES = {
    HealthCode.SESSION_ID_REUSED,
    HealthCode.SESSION_HEARTBEAT_STALE,
    HealthCode.ACTIVE_LEASE_OWNER_MISSING,
    HealthCode.ACTIVE_LEASE_OWNER_CLOSED,
    HealthCode.LEASE_AGENT_MISMATCH,
    HealthCode.LEASE_CONTEXT_MISMATCH,
    HealthCode.LEASE_SCOPE_EMPTY,
    HealthCode.LEASE_HEARTBEAT_STALE,
    HealthCode.BOOTSTRAP_NONCOMPLIANT,
}


def _dedupe(values: Iterable[AuthorizationCode]) -> tuple[AuthorizationCode, ...]:
    seen: set[AuthorizationCode] = set()
    result: list[AuthorizationCode] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _digest(
    *,
    allowed: bool,
    intent: WriteIntent,
    codes: Sequence[AuthorizationCode],
    bootstrap: GuardDecision,
    failed_slos: Sequence[str],
    blockers: Sequence[str],
    overlaps: Sequence[str],
    session_id: str | None,
    lease_id: str,
    repair_plan_id: str | None,
) -> str:
    payload = {
        "allowed": allowed,
        "intent": intent.value,
        "codes": [code.value for code in codes],
        "bootstrap_codes": [code.value for code in bootstrap.codes],
        "failed_slos": list(failed_slos),
        "blockers": list(blockers),
        "overlaps": list(overlaps),
        "session_id": session_id,
        "lease_id": lease_id,
        "repair_plan_id": repair_plan_id,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def authorize_writer(
    *,
    policy: WriterAuthorizationPolicy,
    session: SessionSnapshot | None,
    ack: BootstrapAckSnapshot | None,
    proposed_lease: LeaseSnapshot,
    prelease: PreLeaseRefresh | None,
    health: ControlPlaneHealthReport,
    now: datetime,
    overlapping_unexpired_lease_ids: Sequence[str] = (),
    intent: WriteIntent = WriteIntent.VERSIONED_CODE,
    repair_plan_id: str | None = None,
) -> WriterAuthorizationDecision:
    """Evaluate coordination eligibility without granting the lease itself."""

    _aware(now, "now")
    bootstrap = authorize_lease(
        policy=policy.bootstrap,
        session=session,
        ack=ack,
        lease=proposed_lease,
        now=now,
        prelease=prelease,
    )
    codes: list[AuthorizationCode] = []
    failed_slos: list[str] = []
    blockers: list[str] = []
    overlaps = tuple(sorted(set(overlapping_unexpired_lease_ids)))

    if intent is WriteIntent.EXTERNAL_SIDE_EFFECT:
        codes.append(AuthorizationCode.EXTERNAL_SIDE_EFFECT_REQUIRES_SEPARATE_CAPABILITY)

    if intent is WriteIntent.CONTROL_PLANE_REPAIR:
        if repair_plan_id is None or not _REPAIR_PLAN.fullmatch(repair_plan_id):
            codes.append(AuthorizationCode.REPAIR_PLAN_REQUIRED)

    if not bootstrap.allowed:
        codes.append(AuthorizationCode.BOOTSTRAP_DENIED)

    age = now - health.generated_at
    if age < timedelta(0) or age > policy.max_health_report_age:
        codes.append(AuthorizationCode.HEALTH_REPORT_STALE)

    slo_by_name = {item.name: item for item in health.slos}
    for name in _INTENT_SLOS[intent]:
        slo = slo_by_name.get(name)
        if slo is None or not slo.passed:
            failed_slos.append(name)
    if failed_slos:
        codes.append(AuthorizationCode.REQUIRED_SLO_FAILED)

    session_id = session.session_id if session is not None else None
    target_ids = {proposed_lease.lease_id}
    if session_id:
        target_ids.add(session_id)
    for finding in health.findings:
        if finding.code not in _SUBJECT_BLOCKING_CODES:
            continue
        if finding.subject_id not in target_ids and finding.subject_id != "active_writers":
            continue
        if finding.severity in {HealthSeverity.WARNING, HealthSeverity.ERROR, HealthSeverity.CRITICAL}:
            blockers.append(f"{finding.code.value}:{finding.subject_id}")
    if blockers:
        codes.append(AuthorizationCode.SUBJECT_HEALTH_BLOCKER)

    if overlaps:
        codes.append(AuthorizationCode.OVERLAPPING_LEASE)

    final_codes = _dedupe(codes)
    allowed = not final_codes
    if allowed:
        final_codes = (AuthorizationCode.ALLOWED,)

    digest = _digest(
        allowed=allowed,
        intent=intent,
        codes=final_codes,
        bootstrap=bootstrap,
        failed_slos=tuple(sorted(set(failed_slos))),
        blockers=tuple(sorted(set(blockers))),
        overlaps=overlaps,
        session_id=session_id,
        lease_id=proposed_lease.lease_id,
        repair_plan_id=repair_plan_id,
    )
    return WriterAuthorizationDecision(
        coordination_allowed=allowed,
        intent=intent,
        codes=final_codes,
        bootstrap=bootstrap,
        failed_slos=tuple(sorted(set(failed_slos))),
        health_blockers=tuple(sorted(set(blockers))),
        overlapping_lease_ids=overlaps,
        evaluated_at=now,
        decision_digest=digest,
        repair_plan_id=repair_plan_id,
    )
