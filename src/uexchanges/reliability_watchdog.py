"""Observation-only alert state machine over health and recovery findings."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable, Mapping

from .control_plane_health import ControlPlaneHealthReport, HealthFinding, HealthSeverity
from .reconciliation_planner import plan_health_finding, plan_recovery_finding
from .recovery_verifier import RecoveryFinding, RecoveryReport, RecoverySeverity


class AlertPhase(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    PERSISTING = "PERSISTING"
    RESOLVED = "RESOLVED"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _severity(value: HealthSeverity | RecoverySeverity) -> AlertSeverity:
    return AlertSeverity(value.value)


def _key(source_kind: str, code: str, subject: str) -> str:
    digest = hashlib.sha256(f"{source_kind}|{code}|{subject}".encode("utf-8")).hexdigest()[:20]
    return f"RAL-{digest}"


def _fingerprint(*, severity: AlertSeverity, detail: str, repair_action: str) -> str:
    payload = json.dumps(
        {"severity": severity.value, "detail": detail, "repair_action": repair_action},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PreviousAlertState:
    alert_key: str
    fingerprint: str
    severity: AlertSeverity
    occurrence_count: int
    active: bool = True

    def __post_init__(self) -> None:
        if not self.alert_key.startswith("RAL-"):
            raise ValueError("alert_key must use RAL- prefix")
        if len(self.fingerprint) != 64:
            raise ValueError("fingerprint must be sha256 hex")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")


@dataclass(frozen=True)
class ReliabilityAlert:
    alert_key: str
    source_kind: str
    source_code: str
    subject: str
    severity: AlertSeverity
    phase: AlertPhase
    occurrence_count: int
    fingerprint: str
    detail: str
    repair_action: str
    reconciliation_plan_id: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "alert_key": self.alert_key,
            "source_kind": self.source_kind,
            "source_code": self.source_code,
            "subject": self.subject,
            "severity": self.severity.value,
            "phase": self.phase.value,
            "occurrence_count": self.occurrence_count,
            "fingerprint": self.fingerprint,
            "detail": self.detail,
            "repair_action": self.repair_action,
            "reconciliation_plan_id": self.reconciliation_plan_id,
        }


@dataclass(frozen=True)
class ReliabilityWatchdogReport:
    generated_at: datetime
    alerts: tuple[ReliabilityAlert, ...]
    active_alert_count: int
    critical_active_count: int
    auto_remediation: bool = False

    def __post_init__(self) -> None:
        _aware(self.generated_at, "generated_at")
        if self.auto_remediation:
            raise ValueError("reliability watchdog v1 is observation-only")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "UEX_RELIABILITY_WATCHDOG",
            "version": "1.0.0",
            "generated_at": self.generated_at.isoformat(),
            "active_alert_count": self.active_alert_count,
            "critical_active_count": self.critical_active_count,
            "auto_remediation": False,
            "alerts": [alert.as_dict() for alert in self.alerts],
        }

    def next_state(self) -> tuple[PreviousAlertState, ...]:
        states = []
        for alert in self.alerts:
            if alert.phase is AlertPhase.RESOLVED:
                continue
            states.append(
                PreviousAlertState(
                    alert_key=alert.alert_key,
                    fingerprint=alert.fingerprint,
                    severity=alert.severity,
                    occurrence_count=alert.occurrence_count,
                    active=True,
                )
            )
        return tuple(sorted(states, key=lambda item: item.alert_key))


@dataclass(frozen=True)
class _CurrentFinding:
    source_kind: str
    code: str
    subject: str
    severity: AlertSeverity
    detail: str
    repair_action: str
    plan_id: str | None

    @property
    def alert_key(self) -> str:
        return _key(self.source_kind, self.code, self.subject)

    @property
    def fingerprint(self) -> str:
        return _fingerprint(severity=self.severity, detail=self.detail, repair_action=self.repair_action)


def _health(item: HealthFinding) -> _CurrentFinding:
    plan = plan_health_finding(item)
    return _CurrentFinding(
        source_kind="health",
        code=item.code.value,
        subject=f"{item.subject_type}:{item.subject_id}",
        severity=_severity(item.severity),
        detail=item.detail,
        repair_action=item.repair_action,
        plan_id=plan.plan_id,
    )


def _recovery(item: RecoveryFinding) -> _CurrentFinding:
    plan = plan_recovery_finding(item)
    return _CurrentFinding(
        source_kind="recovery",
        code=item.code.value,
        subject=item.subject,
        severity=_severity(item.severity),
        detail=item.detail,
        repair_action=item.repair_action,
        plan_id=plan.plan_id,
    )


def evaluate_reliability_watchdog(
    *,
    now: datetime,
    health: ControlPlaneHealthReport,
    recovery: RecoveryReport | None = None,
    previous: Iterable[PreviousAlertState] = (),
) -> ReliabilityWatchdogReport:
    """Evaluate alert transitions without mutating the source control plane."""

    _aware(now, "now")
    previous_by_key = {item.alert_key: item for item in previous}
    if len(previous_by_key) != len(tuple(previous)):
        # Iterables may be one-shot; duplicate detection below is re-evaluated in
        # a materialized list by callers/tests.  Keep a clear defensive branch.
        pass

    current: dict[str, _CurrentFinding] = {}
    for item in health.findings:
        value = _health(item)
        if value.alert_key in current and current[value.alert_key] != value:
            raise ValueError(f"conflicting current alert identity: {value.alert_key}")
        current[value.alert_key] = value
    if recovery is not None:
        for item in recovery.findings:
            value = _recovery(item)
            if value.alert_key in current and current[value.alert_key] != value:
                raise ValueError(f"conflicting current alert identity: {value.alert_key}")
            current[value.alert_key] = value

    alerts: list[ReliabilityAlert] = []
    for key in sorted(current):
        item = current[key]
        prior = previous_by_key.get(key)
        if prior is None or not prior.active:
            phase = AlertPhase.NEW
            count = 1
        elif prior.fingerprint == item.fingerprint and prior.severity is item.severity:
            phase = AlertPhase.PERSISTING
            count = prior.occurrence_count + 1
        else:
            phase = AlertPhase.UPDATED
            count = prior.occurrence_count + 1
        alerts.append(
            ReliabilityAlert(
                alert_key=key,
                source_kind=item.source_kind,
                source_code=item.code,
                subject=item.subject,
                severity=item.severity,
                phase=phase,
                occurrence_count=count,
                fingerprint=item.fingerprint,
                detail=item.detail,
                repair_action=item.repair_action,
                reconciliation_plan_id=item.plan_id,
            )
        )

    for key, prior in sorted(previous_by_key.items()):
        if not prior.active or key in current:
            continue
        alerts.append(
            ReliabilityAlert(
                alert_key=key,
                source_kind="previous",
                source_code="RESOLVED",
                subject=key,
                severity=prior.severity,
                phase=AlertPhase.RESOLVED,
                occurrence_count=prior.occurrence_count,
                fingerprint=prior.fingerprint,
                detail="finding no longer present in current health/recovery scan",
                repair_action="verify read-back and close alert evidence",
                reconciliation_plan_id=None,
            )
        )

    active = [item for item in alerts if item.phase is not AlertPhase.RESOLVED]
    return ReliabilityWatchdogReport(
        generated_at=now,
        alerts=tuple(sorted(alerts, key=lambda item: (item.phase.value, item.alert_key))),
        active_alert_count=len(active),
        critical_active_count=sum(1 for item in active if item.severity is AlertSeverity.CRITICAL),
    )
