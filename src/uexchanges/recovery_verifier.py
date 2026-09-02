"""Zero-context recovery verification for UE-Xchanges-OS.

The verifier checks whether the public/private recovery surface is sufficient to
reconstruct authority without chat memory.  It is pure and observation-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Mapping, Sequence

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class RecoverySeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RecoveryStatus(str, Enum):
    RECOVERABLE = "RECOVERABLE"
    DEGRADED = "DEGRADED"
    NOT_RECOVERABLE = "NOT_RECOVERABLE"


class RecoveryCode(str, Enum):
    CURRENT_MAIN_UNAVAILABLE = "CURRENT_MAIN_UNAVAILABLE"
    EVENT_WATERMARK_MISSING = "EVENT_WATERMARK_MISSING"
    REQUIRED_ARTIFACT_MISSING = "REQUIRED_ARTIFACT_MISSING"
    MANIFEST_READSET_INCOMPLETE = "MANIFEST_READSET_INCOMPLETE"
    PRIVATE_CONTROL_PLANE_UNAVAILABLE = "PRIVATE_CONTROL_PLANE_UNAVAILABLE"
    COMMAND_CENTER_UNAVAILABLE = "COMMAND_CENTER_UNAVAILABLE"
    SNAPSHOT_STALE = "SNAPSHOT_STALE"
    SNAPSHOT_MAIN_STALE = "SNAPSHOT_MAIN_STALE"
    MEMORY_CONTAINS_VOLATILE_STATE = "MEMORY_CONTAINS_VOLATILE_STATE"
    STABLE_GOAL_EMBEDS_VOLATILE_SCALE = "STABLE_GOAL_EMBEDS_VOLATILE_SCALE"


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


@dataclass(frozen=True)
class RecoveryArtifact:
    path: str
    exists: bool
    role: str
    updated_at: datetime | None = None
    embedded_main_sha: str | None = None
    snapshot: bool = False

    def __post_init__(self) -> None:
        if not self.path or not self.role:
            raise ValueError("path and role are required")
        if self.updated_at is not None:
            _aware(self.updated_at, "updated_at")
        if self.embedded_main_sha is not None and not _SHA40.fullmatch(self.embedded_main_sha):
            raise ValueError("embedded_main_sha must be a lowercase 40-char SHA")


@dataclass(frozen=True)
class RecoveryPolicy:
    snapshot_max_age_seconds: int = 6 * 60 * 60
    required_private_sources: tuple[str, ...] = (
        "Context_Registry",
        "Agent_Sessions",
        "Work_Leases",
        "Agent_Event_Bus",
        "RuntimeGraphV2CommandCenter",
    )

    def __post_init__(self) -> None:
        if self.snapshot_max_age_seconds <= 0:
            raise ValueError("snapshot_max_age_seconds must be positive")
        if any(not value for value in self.required_private_sources):
            raise ValueError("required_private_sources cannot contain empty values")

    @property
    def snapshot_max_age(self) -> timedelta:
        return timedelta(seconds=self.snapshot_max_age_seconds)


@dataclass(frozen=True)
class RecoveryFinding:
    code: RecoveryCode
    severity: RecoverySeverity
    subject: str
    detail: str
    repair_action: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "subject": self.subject,
            "detail": self.detail,
            "repair_action": self.repair_action,
        }


@dataclass(frozen=True)
class RecoveryReport:
    generated_at: datetime
    status: RecoveryStatus
    score: int
    findings: tuple[RecoveryFinding, ...]
    current_main_sha: str | None
    event_watermark: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "report_type": "recovery_drill_v1",
            "generated_at": self.generated_at.isoformat(),
            "status": self.status.value,
            "score": self.score,
            "current_main_sha": self.current_main_sha,
            "event_watermark": self.event_watermark,
            "findings": [finding.as_dict() for finding in self.findings],
        }


_VOLATILE_MEMORY_PATTERNS = (
    re.compile(r"(?im)^\s*[-*]?\s*(?:opportunities|applications|receipts|human\s+frontier|agent\s+frontier)\s*[:=]\s*\*?\*?\d+"),
    re.compile(r"(?im)^\s*current\s+(?:opportunity|application|receipt)\s+count\s*[:=]"),
)


def scan_stable_document(path: str, text: str) -> tuple[RecoveryFinding, ...]:
    """Detect volatile state embedded in documents intended to be durable."""

    findings: list[RecoveryFinding] = []
    if path == "MEMORY.md":
        if any(pattern.search(text) for pattern in _VOLATILE_MEMORY_PATTERNS):
            findings.append(
                RecoveryFinding(
                    RecoveryCode.MEMORY_CONTAINS_VOLATILE_STATE,
                    RecoverySeverity.ERROR,
                    path,
                    "slow-changing memory contains a live numeric/frontier assertion",
                    "move the volatile fact to a watermarked STATE/HANDOFF/agent_context artifact",
                )
            )
    if path == "goal.md" and "## Current canonical scale" in text:
        findings.append(
            RecoveryFinding(
                RecoveryCode.STABLE_GOAL_EMBEDS_VOLATILE_SCALE,
                RecoverySeverity.WARNING,
                path,
                "stable mission contract embeds a current-scale snapshot that will decay",
                "replace the numeric snapshot with a live-state pointer/authority rule",
            )
        )
    return tuple(findings)


def verify_recovery(
    *,
    now: datetime,
    current_main_sha: str | None,
    event_watermark: str | None,
    required_public_paths: Sequence[str],
    manifest_required_reads: Sequence[str],
    artifacts: Sequence[RecoveryArtifact],
    private_sources_available: Mapping[str, bool],
    command_center_available: bool,
    stable_documents: Mapping[str, str] | None = None,
    policy: RecoveryPolicy | None = None,
) -> RecoveryReport:
    """Verify that a zero-context successor can reconstruct the project."""

    _aware(now, "now")
    policy = policy or RecoveryPolicy()
    findings: list[RecoveryFinding] = []

    if current_main_sha is None or not _SHA40.fullmatch(current_main_sha):
        findings.append(
            RecoveryFinding(
                RecoveryCode.CURRENT_MAIN_UNAVAILABLE,
                RecoverySeverity.CRITICAL,
                "GitHub main",
                "current versioned code authority is unavailable or invalid",
                "restore/read GitHub main before allowing recovery writes",
            )
        )

    if not event_watermark:
        findings.append(
            RecoveryFinding(
                RecoveryCode.EVENT_WATERMARK_MISSING,
                RecoverySeverity.CRITICAL,
                "Agent_Event_Bus",
                "no private event watermark is available",
                "read the Event Bus tail and establish a durable high-watermark",
            )
        )

    artifact_by_path = {artifact.path: artifact for artifact in artifacts}
    for path in required_public_paths:
        artifact = artifact_by_path.get(path)
        if artifact is None or not artifact.exists:
            findings.append(
                RecoveryFinding(
                    RecoveryCode.REQUIRED_ARTIFACT_MISSING,
                    RecoverySeverity.CRITICAL,
                    path,
                    "mandatory recovery artifact is missing",
                    "restore the artifact from version control or regenerate it from canonical authority",
                )
            )

    manifest_set = set(manifest_required_reads)
    missing_manifest_reads = sorted(set(required_public_paths) - manifest_set)
    if missing_manifest_reads:
        findings.append(
            RecoveryFinding(
                RecoveryCode.MANIFEST_READSET_INCOMPLETE,
                RecoverySeverity.CRITICAL,
                "agent_context/bootstrap_manifest.json",
                f"manifest omits required reads: {', '.join(missing_manifest_reads)}",
                "update the bootstrap manifest and CI contract before the next writer starts",
            )
        )

    for source in policy.required_private_sources:
        if not private_sources_available.get(source, False):
            findings.append(
                RecoveryFinding(
                    RecoveryCode.PRIVATE_CONTROL_PLANE_UNAVAILABLE,
                    RecoverySeverity.CRITICAL,
                    source,
                    "required private control-plane source is unavailable",
                    "restore provider access or a verified private backup before write recovery",
                )
            )

    if not command_center_available:
        findings.append(
            RecoveryFinding(
                RecoveryCode.COMMAND_CENTER_UNAVAILABLE,
                RecoverySeverity.ERROR,
                "RuntimeGraphV2CommandCenter",
                "derived execution cockpit is unavailable",
                "rebuild it from canonical Drive evidence/Event Bus before resuming runtime execution",
            )
        )

    for artifact in artifacts:
        if not artifact.exists or not artifact.snapshot or artifact.updated_at is None:
            continue
        age = now - artifact.updated_at
        if age > policy.snapshot_max_age:
            findings.append(
                RecoveryFinding(
                    RecoveryCode.SNAPSHOT_STALE,
                    RecoverySeverity.WARNING,
                    artifact.path,
                    f"snapshot is {age.total_seconds():.0f}s old",
                    "treat it as navigation only and refresh live authorities before mutation",
                )
            )
        if (
            current_main_sha is not None
            and artifact.embedded_main_sha is not None
            and artifact.embedded_main_sha != current_main_sha
        ):
            findings.append(
                RecoveryFinding(
                    RecoveryCode.SNAPSHOT_MAIN_STALE,
                    RecoverySeverity.INFO,
                    artifact.path,
                    f"snapshot references {artifact.embedded_main_sha} while current main is {current_main_sha}",
                    "do not patch the snapshot blindly; refresh it only through the continuity/recovery workflow",
                )
            )

    for path, text in (stable_documents or {}).items():
        findings.extend(scan_stable_document(path, text))

    weights = {
        RecoverySeverity.INFO: 0,
        RecoverySeverity.WARNING: 3,
        RecoverySeverity.ERROR: 12,
        RecoverySeverity.CRITICAL: 30,
    }
    score = max(0, 100 - sum(weights[item.severity] for item in findings))
    severities = {item.severity for item in findings}
    if RecoverySeverity.CRITICAL in severities:
        status = RecoveryStatus.NOT_RECOVERABLE
    elif RecoverySeverity.ERROR in severities or RecoverySeverity.WARNING in severities:
        status = RecoveryStatus.DEGRADED
    else:
        status = RecoveryStatus.RECOVERABLE

    return RecoveryReport(
        generated_at=now,
        status=status,
        score=score,
        findings=tuple(findings),
        current_main_sha=current_main_sha,
        event_watermark=event_watermark,
    )
