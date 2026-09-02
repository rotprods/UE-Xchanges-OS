"""Measured disaster-recovery drill recorder for UE-Xchanges-OS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Sequence

from .recovery_manifest import RecoveryManifest
from .recovery_verifier import RecoveryStatus


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


class DrillStatus(str, Enum):
    PASS = "PASS"
    FAIL_RTO = "FAIL_RTO"
    FAIL_RPO = "FAIL_RPO"
    FAIL_RECOVERY = "FAIL_RECOVERY"
    FAIL_STEPS = "FAIL_STEPS"


@dataclass(frozen=True)
class RecoveryObjective:
    max_rto_seconds: int = 300
    max_event_loss: int = 0

    def __post_init__(self) -> None:
        if self.max_rto_seconds <= 0 or self.max_event_loss < 0:
            raise ValueError("invalid recovery objective")


@dataclass(frozen=True)
class RecoveryDrillReport:
    drill_id: str
    started_at: datetime
    completed_at: datetime
    manifest_bundle_hash: str
    source_event_ids: tuple[str, ...]
    recovered_event_ids: tuple[str, ...]
    missing_event_ids: tuple[str, ...]
    unexpected_event_ids: tuple[str, ...]
    required_steps: dict[str, bool]
    recovery_status: RecoveryStatus
    rto_seconds: float
    event_loss_count: int
    measured_rpo_zero: bool
    objective: RecoveryObjective
    status: DrillStatus

    def __post_init__(self) -> None:
        _aware(self.started_at, "started_at")
        _aware(self.completed_at, "completed_at")
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if not self.drill_id:
            raise ValueError("drill_id is required")
        if not self.source_event_ids:
            raise ValueError("source_event_ids inventory is required before claiming RPO")
        if len(set(self.source_event_ids)) != len(self.source_event_ids):
            raise ValueError("source_event_ids must be unique")
        if len(set(self.recovered_event_ids)) != len(self.recovered_event_ids):
            raise ValueError("recovered_event_ids must be unique")
        if not self.required_steps or any(not key for key in self.required_steps):
            raise ValueError("required_steps cannot be empty")
        if self.event_loss_count != len(self.missing_event_ids):
            raise ValueError("event_loss_count does not match missing events")
        if self.measured_rpo_zero != (self.event_loss_count == 0):
            raise ValueError("measured_rpo_zero must be derived from event inventory")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "UEX_RECOVERY_DRILL",
            "version": "1.0.0",
            "drill_id": self.drill_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "manifest_bundle_hash": self.manifest_bundle_hash,
            "source_event_ids": list(self.source_event_ids),
            "recovered_event_ids": list(self.recovered_event_ids),
            "missing_event_ids": list(self.missing_event_ids),
            "unexpected_event_ids": list(self.unexpected_event_ids),
            "required_steps": dict(sorted(self.required_steps.items())),
            "recovery_status": self.recovery_status.value,
            "rto_seconds": self.rto_seconds,
            "event_loss_count": self.event_loss_count,
            "measured_rpo_zero": self.measured_rpo_zero,
            "objective": {
                "max_rto_seconds": self.objective.max_rto_seconds,
                "max_event_loss": self.objective.max_event_loss,
            },
            "status": self.status.value,
        }


def _status(
    *,
    recovery_status: RecoveryStatus,
    rto_seconds: float,
    event_loss_count: int,
    steps_ok: bool,
    objective: RecoveryObjective,
) -> DrillStatus:
    if recovery_status is RecoveryStatus.NOT_RECOVERABLE:
        return DrillStatus.FAIL_RECOVERY
    if not steps_ok:
        return DrillStatus.FAIL_STEPS
    if event_loss_count > objective.max_event_loss:
        return DrillStatus.FAIL_RPO
    if rto_seconds > objective.max_rto_seconds:
        return DrillStatus.FAIL_RTO
    if recovery_status is not RecoveryStatus.RECOVERABLE:
        return DrillStatus.FAIL_RECOVERY
    return DrillStatus.PASS


def record_recovery_drill(
    *,
    drill_id: str,
    started_at: datetime,
    completed_at: datetime,
    manifest: RecoveryManifest,
    source_event_ids: Sequence[str],
    recovered_event_ids: Sequence[str],
    required_steps: Mapping[str, bool],
    recovery_status: RecoveryStatus,
    objective: RecoveryObjective | None = None,
) -> RecoveryDrillReport:
    _aware(started_at, "started_at")
    _aware(completed_at, "completed_at")
    if completed_at < started_at:
        raise ValueError("completed_at cannot precede started_at")
    objective = objective or RecoveryObjective()
    source = tuple(source_event_ids)
    recovered = tuple(recovered_event_ids)
    if not source:
        raise ValueError("source event inventory is mandatory")
    if len(set(source)) != len(source) or len(set(recovered)) != len(recovered):
        raise ValueError("event inventories must not contain duplicates")
    source_set = set(source)
    recovered_set = set(recovered)
    missing = tuple(event_id for event_id in source if event_id not in recovered_set)
    unexpected = tuple(event_id for event_id in recovered if event_id not in source_set)
    rto = (completed_at - started_at).total_seconds()
    steps = {str(key): bool(value) for key, value in required_steps.items()}
    if not steps:
        raise ValueError("required_steps inventory is mandatory")
    event_loss = len(missing)
    status = _status(
        recovery_status=recovery_status,
        rto_seconds=rto,
        event_loss_count=event_loss,
        steps_ok=all(steps.values()),
        objective=objective,
    )
    return RecoveryDrillReport(
        drill_id=drill_id,
        started_at=started_at,
        completed_at=completed_at,
        manifest_bundle_hash=manifest.bundle_hash,
        source_event_ids=source,
        recovered_event_ids=recovered,
        missing_event_ids=missing,
        unexpected_event_ids=unexpected,
        required_steps=steps,
        recovery_status=recovery_status,
        rto_seconds=rto,
        event_loss_count=event_loss,
        measured_rpo_zero=event_loss == 0,
        objective=objective,
        status=status,
    )
