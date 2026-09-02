"""Deterministic reconciliation planning for control-plane/recovery findings.

Plans are deliberately non-executing.  They make remediation explicit, scoped and
idempotent without granting mutation authority to the diagnostic layer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

from .control_plane_health import HealthCode, HealthFinding, HealthSeverity
from .recovery_verifier import RecoveryCode, RecoveryFinding, RecoverySeverity


class RepairOperation(str, Enum):
    RECONCILE_SESSION_IDENTITY = "RECONCILE_SESSION_IDENTITY"
    RECONCILE_LEASE_STATUS = "RECONCILE_LEASE_STATUS"
    RECONSTRUCT_LEASE_OWNERSHIP = "RECONSTRUCT_LEASE_OWNERSHIP"
    REPLACE_INVALID_LEASE = "REPLACE_INVALID_LEASE"
    REFRESH_SESSION_HEARTBEAT_OR_CLOSE = "REFRESH_SESSION_HEARTBEAT_OR_CLOSE"
    REFRESH_CONTEXT_REGISTRY = "REFRESH_CONTEXT_REGISTRY"
    REBUILD_DERIVED_PROJECTION = "REBUILD_DERIVED_PROJECTION"
    REBOOTSTRAP_SESSION = "REBOOTSTRAP_SESSION"
    RESOLVE_DEAD_LETTER = "RESOLVE_DEAD_LETTER"
    RESTORE_RECOVERY_ARTIFACT = "RESTORE_RECOVERY_ARTIFACT"
    UPDATE_BOOTSTRAP_MANIFEST = "UPDATE_BOOTSTRAP_MANIFEST"
    RESTORE_PRIVATE_CONTROL_PLANE_ACCESS = "RESTORE_PRIVATE_CONTROL_PLANE_ACCESS"
    REBUILD_RUNTIME_COMMAND_CENTER = "REBUILD_RUNTIME_COMMAND_CENTER"
    REFRESH_RECOVERY_SNAPSHOT = "REFRESH_RECOVERY_SNAPSHOT"
    CLEAN_STABLE_DOCUMENT = "CLEAN_STABLE_DOCUMENT"
    ESTABLISH_MAIN_AUTHORITY = "ESTABLISH_MAIN_AUTHORITY"
    ESTABLISH_EVENT_WATERMARK = "ESTABLISH_EVENT_WATERMARK"


class RepairRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RepairSurface(str, Enum):
    SESSION_ROW = "SESSION_ROW"
    LEASE_ROW = "LEASE_ROW"
    CONTEXT_REGISTRY = "CONTEXT_REGISTRY"
    DERIVED_PROJECTION = "DERIVED_PROJECTION"
    BOOTSTRAP = "BOOTSTRAP"
    DEAD_LETTER = "DEAD_LETTER"
    VERSIONED_RECOVERY = "VERSIONED_RECOVERY"
    PRIVATE_CONTROL_PLANE = "PRIVATE_CONTROL_PLANE"
    RUNTIME_COMMAND_CENTER = "RUNTIME_COMMAND_CENTER"
    STABLE_DOCUMENT = "STABLE_DOCUMENT"
    EXTERNAL_CODE_AUTHORITY = "EXTERNAL_CODE_AUTHORITY"
    EVENT_BUS = "EVENT_BUS"


@dataclass(frozen=True)
class ReconciliationPlan:
    plan_id: str
    source_kind: str
    source_code: str
    subject_type: str
    subject_id: str
    operation: RepairOperation
    surface: RepairSurface
    risk: RepairRisk
    required_lease_scope: str
    preconditions: tuple[str, ...]
    expected_readback: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    canonical_domain_mutation: bool = False
    auto_execute: bool = False

    def __post_init__(self) -> None:
        if not self.plan_id.startswith("RPL-") or len(self.plan_id) != 20:
            raise ValueError("plan_id must be RPL- plus 16 hex chars")
        if not self.source_kind or not self.source_code or not self.subject_id:
            raise ValueError("source identity is required")
        if not self.required_lease_scope.strip():
            raise ValueError("required_lease_scope is required")
        if not self.preconditions or not self.expected_readback:
            raise ValueError("preconditions and expected_readback are required")
        if self.canonical_domain_mutation:
            raise ValueError("reconciliation planner v1 cannot plan canonical domain mutations")
        if self.auto_execute:
            raise ValueError("reconciliation planner v1 is plan-only")

    def as_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "source_kind": self.source_kind,
            "source_code": self.source_code,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "operation": self.operation.value,
            "surface": self.surface.value,
            "risk": self.risk.value,
            "required_lease_scope": self.required_lease_scope,
            "preconditions": list(self.preconditions),
            "expected_readback": list(self.expected_readback),
            "evidence_requirements": list(self.evidence_requirements),
            "canonical_domain_mutation": False,
            "auto_execute": False,
        }


def _plan_id(*, source_kind: str, source_code: str, subject_type: str, subject_id: str, operation: RepairOperation) -> str:
    payload = json.dumps(
        {
            "source_kind": source_kind,
            "source_code": source_code,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "operation": operation.value,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "RPL-" + hashlib.sha256(payload).hexdigest()[:16]


def _risk_from_health(severity: HealthSeverity) -> RepairRisk:
    return {
        HealthSeverity.INFO: RepairRisk.LOW,
        HealthSeverity.WARNING: RepairRisk.MEDIUM,
        HealthSeverity.ERROR: RepairRisk.HIGH,
        HealthSeverity.CRITICAL: RepairRisk.CRITICAL,
    }[severity]


def _risk_from_recovery(severity: RecoverySeverity) -> RepairRisk:
    return {
        RecoverySeverity.INFO: RepairRisk.LOW,
        RecoverySeverity.WARNING: RepairRisk.MEDIUM,
        RecoverySeverity.ERROR: RepairRisk.HIGH,
        RecoverySeverity.CRITICAL: RepairRisk.CRITICAL,
    }[severity]


def _build(
    *,
    source_kind: str,
    source_code: str,
    subject_type: str,
    subject_id: str,
    operation: RepairOperation,
    surface: RepairSurface,
    risk: RepairRisk,
    lease_scope: str,
    preconditions: Sequence[str],
    readback: Sequence[str],
    evidence: Sequence[str],
) -> ReconciliationPlan:
    return ReconciliationPlan(
        plan_id=_plan_id(
            source_kind=source_kind,
            source_code=source_code,
            subject_type=subject_type,
            subject_id=subject_id,
            operation=operation,
        ),
        source_kind=source_kind,
        source_code=source_code,
        subject_type=subject_type,
        subject_id=subject_id,
        operation=operation,
        surface=surface,
        risk=risk,
        required_lease_scope=lease_scope,
        preconditions=tuple(preconditions),
        expected_readback=tuple(readback),
        evidence_requirements=tuple(evidence),
    )


_HEALTH_MAPPING: dict[HealthCode, tuple[RepairOperation, RepairSurface, str]] = {
    HealthCode.SESSION_ID_REUSED: (RepairOperation.RECONCILE_SESSION_IDENTITY, RepairSurface.SESSION_ROW, "drive:Agent_Sessions:{subject_id}"),
    HealthCode.SESSION_HEARTBEAT_STALE: (RepairOperation.REFRESH_SESSION_HEARTBEAT_OR_CLOSE, RepairSurface.SESSION_ROW, "drive:Agent_Sessions:{subject_id}"),
    HealthCode.ACTIVE_LEASE_EXPIRED_STALE_ROW: (RepairOperation.RECONCILE_LEASE_STATUS, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}"),
    HealthCode.ACTIVE_LEASE_OWNER_MISSING: (RepairOperation.RECONSTRUCT_LEASE_OWNERSHIP, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}+drive:Agent_Sessions"),
    HealthCode.ACTIVE_LEASE_OWNER_CLOSED: (RepairOperation.RECONCILE_LEASE_STATUS, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}"),
    HealthCode.LEASE_AGENT_MISMATCH: (RepairOperation.REPLACE_INVALID_LEASE, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}"),
    HealthCode.LEASE_CONTEXT_MISMATCH: (RepairOperation.REPLACE_INVALID_LEASE, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}"),
    HealthCode.LEASE_SCOPE_EMPTY: (RepairOperation.REPLACE_INVALID_LEASE, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}"),
    HealthCode.LEASE_HEARTBEAT_STALE: (RepairOperation.RECONCILE_LEASE_STATUS, RepairSurface.LEASE_ROW, "drive:Work_Leases:{subject_id}"),
    HealthCode.CONTEXT_REGISTRY_STALE: (RepairOperation.REFRESH_CONTEXT_REGISTRY, RepairSurface.CONTEXT_REGISTRY, "drive:Context_Registry:{subject_id}"),
    HealthCode.PROJECTION_STALE: (RepairOperation.REBUILD_DERIVED_PROJECTION, RepairSurface.DERIVED_PROJECTION, "derived_projection:{subject_id}"),
    HealthCode.BOOTSTRAP_NONCOMPLIANT: (RepairOperation.REBOOTSTRAP_SESSION, RepairSurface.BOOTSTRAP, "drive:Agent_Sessions+drive:Agent_Event_Bus"),
    HealthCode.DEAD_LETTER_PRESENT: (RepairOperation.RESOLVE_DEAD_LETTER, RepairSurface.DEAD_LETTER, "drive:RuntimeGraphV2CommandCenter:Dead_Letters"),
}


_RECOVERY_MAPPING: dict[RecoveryCode, tuple[RepairOperation, RepairSurface, str]] = {
    RecoveryCode.CURRENT_MAIN_UNAVAILABLE: (RepairOperation.ESTABLISH_MAIN_AUTHORITY, RepairSurface.EXTERNAL_CODE_AUTHORITY, "github:main"),
    RecoveryCode.EVENT_WATERMARK_MISSING: (RepairOperation.ESTABLISH_EVENT_WATERMARK, RepairSurface.EVENT_BUS, "drive:Agent_Event_Bus"),
    RecoveryCode.REQUIRED_ARTIFACT_MISSING: (RepairOperation.RESTORE_RECOVERY_ARTIFACT, RepairSurface.VERSIONED_RECOVERY, "github:{subject_id}"),
    RecoveryCode.MANIFEST_READSET_INCOMPLETE: (RepairOperation.UPDATE_BOOTSTRAP_MANIFEST, RepairSurface.BOOTSTRAP, "github:agent_context/bootstrap_manifest.json"),
    RecoveryCode.PRIVATE_CONTROL_PLANE_UNAVAILABLE: (RepairOperation.RESTORE_PRIVATE_CONTROL_PLANE_ACCESS, RepairSurface.PRIVATE_CONTROL_PLANE, "private:{subject_id}"),
    RecoveryCode.COMMAND_CENTER_UNAVAILABLE: (RepairOperation.REBUILD_RUNTIME_COMMAND_CENTER, RepairSurface.RUNTIME_COMMAND_CENTER, "drive:RuntimeGraphV2CommandCenter"),
    RecoveryCode.SNAPSHOT_STALE: (RepairOperation.REFRESH_RECOVERY_SNAPSHOT, RepairSurface.VERSIONED_RECOVERY, "github:{subject_id}"),
    RecoveryCode.SNAPSHOT_MAIN_STALE: (RepairOperation.REFRESH_RECOVERY_SNAPSHOT, RepairSurface.VERSIONED_RECOVERY, "github:{subject_id}"),
    RecoveryCode.MEMORY_CONTAINS_VOLATILE_STATE: (RepairOperation.CLEAN_STABLE_DOCUMENT, RepairSurface.STABLE_DOCUMENT, "github:MEMORY.md"),
    RecoveryCode.STABLE_GOAL_EMBEDS_VOLATILE_SCALE: (RepairOperation.CLEAN_STABLE_DOCUMENT, RepairSurface.STABLE_DOCUMENT, "github:goal.md"),
}


def plan_health_finding(finding: HealthFinding) -> ReconciliationPlan:
    try:
        operation, surface, lease_template = _HEALTH_MAPPING[finding.code]
    except KeyError as exc:
        raise ValueError(f"unsupported health finding: {finding.code.value}") from exc
    subject_id = finding.subject_id
    lease_scope = lease_template.format(subject_id=subject_id)
    return _build(
        source_kind="health",
        source_code=finding.code.value,
        subject_type=finding.subject_type,
        subject_id=subject_id,
        operation=operation,
        surface=surface,
        risk=_risk_from_health(finding.severity),
        lease_scope=lease_scope,
        preconditions=(
            "bootstrap guard PASS for the repair writer",
            "fresh current-main, unexpired-lease and EventBus read immediately before repair lease",
            "authoritative evidence still reproduces the finding",
            "no unexpired overlapping lease exists",
        ),
        readback=(
            "read the exact target by stable ID after mutation",
            "rerun control-plane health evaluation",
            "append a reconciliation event with before/after and evidence refs",
        ),
        evidence=(finding.detail, finding.repair_action),
    )


def plan_recovery_finding(finding: RecoveryFinding) -> ReconciliationPlan:
    try:
        operation, surface, lease_template = _RECOVERY_MAPPING[finding.code]
    except KeyError as exc:
        raise ValueError(f"unsupported recovery finding: {finding.code.value}") from exc
    subject_id = finding.subject
    lease_scope = lease_template.format(subject_id=subject_id)
    return _build(
        source_kind="recovery",
        source_code=finding.code.value,
        subject_type="recovery",
        subject_id=subject_id,
        operation=operation,
        surface=surface,
        risk=_risk_from_recovery(finding.severity),
        lease_scope=lease_scope,
        preconditions=(
            "bootstrap guard PASS for the recovery writer",
            "re-read current code/private authority before repair",
            "finding reproduced from the current recovery drill",
            "repair does not overwrite a newer authoritative source",
        ),
        readback=(
            "verify the restored/refreshed artifact or source by exact identity",
            "rerun recovery verifier",
            "record the new recovery manifest/drill evidence",
        ),
        evidence=(finding.detail, finding.repair_action),
    )


def build_reconciliation_plan(
    *,
    health_findings: Iterable[HealthFinding] = (),
    recovery_findings: Iterable[RecoveryFinding] = (),
) -> tuple[ReconciliationPlan, ...]:
    """Build a stable, de-duplicated plan ordered by risk then plan id."""

    plans = [plan_health_finding(item) for item in health_findings]
    plans.extend(plan_recovery_finding(item) for item in recovery_findings)
    by_id: dict[str, ReconciliationPlan] = {}
    for plan in plans:
        existing = by_id.get(plan.plan_id)
        if existing is not None and existing != plan:
            raise ValueError(f"plan identity collision: {plan.plan_id}")
        by_id[plan.plan_id] = plan
    risk_order = {RepairRisk.CRITICAL: 0, RepairRisk.HIGH: 1, RepairRisk.MEDIUM: 2, RepairRisk.LOW: 3}
    return tuple(sorted(by_id.values(), key=lambda item: (risk_order[item.risk], item.plan_id)))
