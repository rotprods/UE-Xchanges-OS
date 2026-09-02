"""Observation-only bootstrap compliance watchdog.

Consumes BootstrapGuard findings and turns them into deduplicated, severity-ranked
alerts.  It never mutates sessions or leases; remediation belongs to a separate,
explicitly authorized control-plane capability.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Iterable, Mapping

from .bootstrap_guard import ComplianceFinding, GuardCode


class WatchdogSeverity(IntEnum):
    INFO = 10
    WARNING = 20
    HIGH = 30
    CRITICAL = 40


class AlertTransition(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    PERSISTING = "PERSISTING"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class PreviousAlert:
    subject_key: str
    fingerprint: str
    severity: WatchdogSeverity


@dataclass(frozen=True)
class WatchdogAlert:
    subject_key: str
    subject_type: str
    subject_id: str
    session_id: str | None
    fingerprint: str
    severity: WatchdogSeverity
    transition: AlertTransition
    codes: tuple[GuardCode, ...]
    notify: bool
    recommended_action: str

    def as_dict(self) -> dict[str, object]:
        return {
            "subject_key": self.subject_key,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "fingerprint": self.fingerprint,
            "severity": self.severity.name,
            "transition": self.transition.value,
            "codes": [code.value for code in self.codes],
            "notify": self.notify,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True)
class WatchdogReport:
    alerts: tuple[WatchdogAlert, ...]

    @property
    def open_alerts(self) -> tuple[WatchdogAlert, ...]:
        return tuple(item for item in self.alerts if item.transition is not AlertTransition.RESOLVED)

    @property
    def notifications(self) -> tuple[WatchdogAlert, ...]:
        return tuple(item for item in self.alerts if item.notify)

    @property
    def healthy(self) -> bool:
        return not any(item.severity >= WatchdogSeverity.HIGH for item in self.open_alerts)

    @property
    def current_state(self) -> dict[str, PreviousAlert]:
        return {
            item.subject_key: PreviousAlert(item.subject_key, item.fingerprint, item.severity)
            for item in self.open_alerts
        }

    def as_dict(self) -> dict[str, object]:
        counts = {severity.name: 0 for severity in WatchdogSeverity}
        for item in self.open_alerts:
            counts[item.severity.name] += 1
        return {
            "contract": "UEX_BOOTSTRAP_COMPLIANCE_WATCHDOG",
            "healthy": self.healthy,
            "open_alert_count": len(self.open_alerts),
            "notification_count": len(self.notifications),
            "open_by_severity": counts,
            "alerts": [item.as_dict() for item in self.alerts],
        }


_CODE_SEVERITY: dict[GuardCode, WatchdogSeverity] = {
    GuardCode.COMPLIANT: WatchdogSeverity.INFO,
    GuardCode.LEGACY_PRE_CONTRACT: WatchdogSeverity.INFO,
    GuardCode.SESSION_NOT_ACTIVE: WatchdogSeverity.HIGH,
    GuardCode.SESSION_REUSED: WatchdogSeverity.CRITICAL,
    GuardCode.MISSING_SESSION: WatchdogSeverity.CRITICAL,
    GuardCode.MISSING_BOOTSTRAP_ACK: WatchdogSeverity.CRITICAL,
    GuardCode.ACK_BEFORE_SESSION: WatchdogSeverity.CRITICAL,
    GuardCode.ACK_AFTER_LEASE: WatchdogSeverity.CRITICAL,
    GuardCode.ACK_IDENTITY_MISMATCH: WatchdogSeverity.CRITICAL,
    GuardCode.ACK_CONTEXT_MISMATCH: WatchdogSeverity.CRITICAL,
    GuardCode.STALE_MANIFEST_VERSION: WatchdogSeverity.HIGH,
    GuardCode.ACK_READSET_TIMING_INVALID: WatchdogSeverity.HIGH,
    GuardCode.MISSING_PUBLIC_READ_PROOF: WatchdogSeverity.HIGH,
    GuardCode.MISSING_PRIVATE_EVENT_WATERMARK: WatchdogSeverity.HIGH,
    GuardCode.MISSING_PRELEASE_REFRESH: WatchdogSeverity.CRITICAL,
    GuardCode.PRELEASE_MAIN_SHA_STALE: WatchdogSeverity.HIGH,
    GuardCode.MISSING_PRELEASE_EVENT_WATERMARK: WatchdogSeverity.HIGH,
    GuardCode.LEASE_SCAN_BEFORE_ACK: WatchdogSeverity.CRITICAL,
    GuardCode.LEASE_SCAN_AFTER_ACQUIRE: WatchdogSeverity.CRITICAL,
    GuardCode.LEASE_SCAN_STALE: WatchdogSeverity.HIGH,
    GuardCode.LEASE_OWNER_MISMATCH: WatchdogSeverity.CRITICAL,
    GuardCode.LEASE_CONTEXT_MISMATCH: WatchdogSeverity.CRITICAL,
    GuardCode.LEASE_SCOPE_EMPTY: WatchdogSeverity.CRITICAL,
    GuardCode.LEASE_NOT_ACTIVE: WatchdogSeverity.WARNING,
    GuardCode.LEASE_EXPIRED: WatchdogSeverity.WARNING,
}


def severity_for_codes(codes: Iterable[GuardCode]) -> WatchdogSeverity:
    values = tuple(codes)
    if not values:
        return WatchdogSeverity.WARNING
    return max((_CODE_SEVERITY.get(code, WatchdogSeverity.HIGH) for code in values), default=WatchdogSeverity.WARNING)


def _subject_key(finding: ComplianceFinding) -> str:
    return f"{finding.subject_type}:{finding.subject_id}"


def _fingerprint(finding: ComplianceFinding) -> str:
    payload = "|".join(
        [
            finding.subject_type,
            finding.subject_id,
            finding.session_id or "",
            *sorted(code.value for code in finding.codes),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _recommended_action(codes: tuple[GuardCode, ...]) -> str:
    code_set = set(codes)
    if GuardCode.SESSION_REUSED in code_set:
        return "STOP_WRITES_CREATE_FRESH_SESSION_AND_RECONCILE_DUPLICATE_SESSION_ID"
    if code_set & {
        GuardCode.MISSING_SESSION,
        GuardCode.LEASE_OWNER_MISMATCH,
        GuardCode.LEASE_CONTEXT_MISMATCH,
        GuardCode.ACK_IDENTITY_MISMATCH,
        GuardCode.ACK_CONTEXT_MISMATCH,
    }:
        return "STOP_WRITES_RECONCILE_IDENTITY_AND_FENCING"
    if code_set & {
        GuardCode.MISSING_BOOTSTRAP_ACK,
        GuardCode.ACK_BEFORE_SESSION,
        GuardCode.ACK_AFTER_LEASE,
        GuardCode.STALE_MANIFEST_VERSION,
        GuardCode.MISSING_PUBLIC_READ_PROOF,
        GuardCode.MISSING_PRIVATE_EVENT_WATERMARK,
    }:
        return "REMAIN_READ_ONLY_REPEAT_MANIFEST_BOOTSTRAP_AND_EMIT_ACK"
    if code_set & {
        GuardCode.MISSING_PRELEASE_REFRESH,
        GuardCode.PRELEASE_MAIN_SHA_STALE,
        GuardCode.MISSING_PRELEASE_EVENT_WATERMARK,
        GuardCode.LEASE_SCAN_BEFORE_ACK,
        GuardCode.LEASE_SCAN_AFTER_ACQUIRE,
        GuardCode.LEASE_SCAN_STALE,
    }:
        return "DO_NOT_USE_LEASE_REFRESH_MAIN_LEASES_EVENT_TAIL_AND_ACQUIRE_NEW_FENCE"
    if GuardCode.LEASE_SCOPE_EMPTY in code_set:
        return "RELEASE_LEASE_AND_ACQUIRE_EXPLICIT_MINIMAL_SCOPE"
    if code_set & {GuardCode.LEASE_NOT_ACTIVE, GuardCode.LEASE_EXPIRED}:
        return "RECONCILE_STALE_LEASE_ROW_DO_NOT_TREAT_AS_LIVE_AUTHORITY"
    if GuardCode.SESSION_NOT_ACTIVE in code_set:
        return "STOP_WRITES_REGISTER_NEW_ACTIVE_SESSION"
    if GuardCode.LEGACY_PRE_CONTRACT in code_set:
        return "NO_ACTION_HISTORICAL_PRE_CONTRACT_RECORD"
    return "REVIEW_BOOTSTRAP_PROTOCOL_VIOLATION"


def _previous_map(previous: Mapping[str, PreviousAlert] | None) -> Mapping[str, PreviousAlert]:
    return previous or {}


def build_watchdog_report(
    findings: Iterable[ComplianceFinding],
    *,
    previous: Mapping[str, PreviousAlert] | None = None,
    notify_threshold: WatchdogSeverity = WatchdogSeverity.HIGH,
) -> WatchdogReport:
    """Build a deterministic alert report from compliance findings.

    Compliant and legacy-pre-contract findings are not open alerts.  Previous
    alerts missing from the current violation set become `RESOLVED` entries.
    Notifications are emitted for NEW/UPDATED alerts at or above the configured
    severity threshold and for RESOLVED alerts that were previously HIGH/CRITICAL.
    """

    previous = _previous_map(previous)
    current: dict[str, WatchdogAlert] = {}

    for finding in findings:
        if finding.allowed or finding.codes == (GuardCode.LEGACY_PRE_CONTRACT,):
            continue
        key = _subject_key(finding)
        fingerprint = _fingerprint(finding)
        severity = severity_for_codes(finding.codes)
        old = previous.get(key)
        if old is None:
            transition = AlertTransition.NEW
        elif old.fingerprint != fingerprint or old.severity != severity:
            transition = AlertTransition.UPDATED
        else:
            transition = AlertTransition.PERSISTING
        current[key] = WatchdogAlert(
            subject_key=key,
            subject_type=finding.subject_type,
            subject_id=finding.subject_id,
            session_id=finding.session_id,
            fingerprint=fingerprint,
            severity=severity,
            transition=transition,
            codes=finding.codes,
            notify=transition in {AlertTransition.NEW, AlertTransition.UPDATED} and severity >= notify_threshold,
            recommended_action=_recommended_action(finding.codes),
        )

    resolved: list[WatchdogAlert] = []
    for key, old in previous.items():
        if key in current:
            continue
        subject_type, _, subject_id = key.partition(":")
        resolved.append(
            WatchdogAlert(
                subject_key=key,
                subject_type=subject_type,
                subject_id=subject_id,
                session_id=None,
                fingerprint=old.fingerprint,
                severity=old.severity,
                transition=AlertTransition.RESOLVED,
                codes=(),
                notify=old.severity >= notify_threshold,
                recommended_action="NO_ACTION_ALERT_RESOLVED",
            )
        )

    alerts = [*current.values(), *resolved]
    alerts.sort(key=lambda item: (-int(item.severity), item.subject_key, item.transition.value))
    return WatchdogReport(tuple(alerts))


def previous_state_from_json(data: Mapping[str, object]) -> dict[str, PreviousAlert]:
    result: dict[str, PreviousAlert] = {}
    for key, raw in data.items():
        if not isinstance(key, str) or not isinstance(raw, Mapping):
            raise ValueError("previous alert state must map strings to objects")
        fingerprint = raw.get("fingerprint")
        severity = raw.get("severity")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise ValueError("previous alert fingerprint invalid")
        if not isinstance(severity, str):
            raise ValueError("previous alert severity invalid")
        result[key] = PreviousAlert(key, fingerprint, WatchdogSeverity[severity])
    return result


def current_state_as_json(report: WatchdogReport) -> dict[str, dict[str, str]]:
    return {
        key: {"fingerprint": value.fingerprint, "severity": value.severity.name}
        for key, value in report.current_state.items()
    }
