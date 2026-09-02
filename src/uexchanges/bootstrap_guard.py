"""Fail-closed bootstrap authorization and compliance auditing.

The repository contract requires a writer to load the bootstrap context before
it can acquire a write lease.  This module turns that convention into a pure,
deterministic authorization primitive with no Drive/GitHub/browser/network
dependencies.

It does *not* grant domain authority.  It only answers whether a session is
bootstrap-compliant for a particular write lease.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Mapping, Sequence

_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class GuardCode(str, Enum):
    COMPLIANT = "COMPLIANT"
    LEGACY_PRE_CONTRACT = "LEGACY_PRE_CONTRACT"
    MISSING_SESSION = "MISSING_SESSION"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    SESSION_REUSED = "SESSION_REUSED"
    MISSING_BOOTSTRAP_ACK = "MISSING_BOOTSTRAP_ACK"
    ACK_BEFORE_SESSION = "ACK_BEFORE_SESSION"
    ACK_AFTER_LEASE = "ACK_AFTER_LEASE"
    ACK_IDENTITY_MISMATCH = "ACK_IDENTITY_MISMATCH"
    ACK_CONTEXT_MISMATCH = "ACK_CONTEXT_MISMATCH"
    STALE_MANIFEST_VERSION = "STALE_MANIFEST_VERSION"
    ACK_READSET_TIMING_INVALID = "ACK_READSET_TIMING_INVALID"
    MISSING_PUBLIC_READ_PROOF = "MISSING_PUBLIC_READ_PROOF"
    MISSING_PRIVATE_EVENT_WATERMARK = "MISSING_PRIVATE_EVENT_WATERMARK"
    MISSING_PRELEASE_REFRESH = "MISSING_PRELEASE_REFRESH"
    PRELEASE_MAIN_SHA_STALE = "PRELEASE_MAIN_SHA_STALE"
    MISSING_PRELEASE_EVENT_WATERMARK = "MISSING_PRELEASE_EVENT_WATERMARK"
    LEASE_SCAN_BEFORE_ACK = "LEASE_SCAN_BEFORE_ACK"
    LEASE_SCAN_AFTER_ACQUIRE = "LEASE_SCAN_AFTER_ACQUIRE"
    LEASE_SCAN_STALE = "LEASE_SCAN_STALE"
    LEASE_OWNER_MISMATCH = "LEASE_OWNER_MISMATCH"
    LEASE_CONTEXT_MISMATCH = "LEASE_CONTEXT_MISMATCH"
    LEASE_SCOPE_EMPTY = "LEASE_SCOPE_EMPTY"
    LEASE_NOT_ACTIVE = "LEASE_NOT_ACTIVE"
    LEASE_EXPIRED = "LEASE_EXPIRED"


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _sha40(value: str, field: str) -> str:
    if not isinstance(value, str) or not _SHA40_RE.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase 40-char git SHA")
    return value


def parse_iso8601(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _aware(parsed, "timestamp")


@dataclass(frozen=True)
class BootstrapPolicy:
    manifest_version: str
    current_main_sha: str
    context_id: str
    effective_at: datetime
    max_prelease_scan_age_seconds: int = 120

    def __post_init__(self) -> None:
        if not self.manifest_version:
            raise ValueError("manifest_version is required")
        _sha40(self.current_main_sha, "current_main_sha")
        if not self.context_id:
            raise ValueError("context_id is required")
        _aware(self.effective_at, "effective_at")
        if self.max_prelease_scan_age_seconds <= 0:
            raise ValueError("max_prelease_scan_age_seconds must be positive")

    @property
    def max_prelease_scan_age(self) -> timedelta:
        return timedelta(seconds=self.max_prelease_scan_age_seconds)


@dataclass(frozen=True)
class SessionSnapshot:
    session_id: str
    agent_id: str
    context_id: str
    started_at: datetime
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if not self.session_id or not self.agent_id or not self.context_id:
            raise ValueError("session_id, agent_id and context_id are required")
        _aware(self.started_at, "started_at")


@dataclass(frozen=True)
class BootstrapAckSnapshot:
    event_id: str
    event_at: datetime
    manifest_version: str
    observed_main_sha: str
    context_id: str
    agent_id: str
    session_id: str
    private_event_watermark: str
    lease_scan_at: datetime
    public_read_set_sha256: str | None = None
    public_read_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.event_id or not self.manifest_version:
            raise ValueError("event_id and manifest_version are required")
        _aware(self.event_at, "event_at")
        _sha40(self.observed_main_sha, "observed_main_sha")
        _aware(self.lease_scan_at, "lease_scan_at")
        if not self.context_id or not self.agent_id or not self.session_id:
            raise ValueError("bootstrap identity fields are required")
        if self.public_read_set_sha256 is not None and not re.fullmatch(
            r"[0-9a-f]{64}", self.public_read_set_sha256
        ):
            raise ValueError("public_read_set_sha256 must be 64 lowercase hex chars")
        if not self.public_read_set_sha256 and not self.public_read_refs:
            raise ValueError("a public read-set hash or refs are required")
        if any(not ref for ref in self.public_read_refs):
            raise ValueError("public_read_refs cannot contain empty values")

    @classmethod
    def from_event_payload(
        cls,
        *,
        event_id: str,
        event_at: datetime,
        payload: Mapping[str, object] | str,
    ) -> "BootstrapAckSnapshot":
        loaded = json.loads(payload) if isinstance(payload, str) else dict(payload)
        refs = loaded.get("public_read_refs", ())
        if refs is None:
            refs = ()
        if not isinstance(refs, (list, tuple)) or not all(isinstance(v, str) for v in refs):
            raise ValueError("public_read_refs must be a list of strings")
        sha = loaded.get("public_read_set_sha256") or loaded.get("public_read_set_hash")
        if sha is not None and not isinstance(sha, str):
            raise ValueError("public read-set hash must be a string")
        required = {
            "manifest_version",
            "observed_main_sha",
            "context_id",
            "private_event_watermark",
            "lease_scan_at",
            "agent_id",
            "session_id",
        }
        missing = sorted(key for key in required if not loaded.get(key))
        if missing:
            raise ValueError(f"bootstrap payload missing: {', '.join(missing)}")
        return cls(
            event_id=event_id,
            event_at=event_at,
            manifest_version=str(loaded["manifest_version"]),
            observed_main_sha=str(loaded["observed_main_sha"]),
            context_id=str(loaded["context_id"]),
            agent_id=str(loaded["agent_id"]),
            session_id=str(loaded["session_id"]),
            private_event_watermark=str(loaded["private_event_watermark"]),
            lease_scan_at=parse_iso8601(str(loaded["lease_scan_at"])),
            public_read_set_sha256=sha,
            public_read_refs=tuple(refs),
        )


@dataclass(frozen=True)
class PreLeaseRefresh:
    observed_main_sha: str
    lease_scan_at: datetime
    private_event_watermark: str

    def __post_init__(self) -> None:
        _sha40(self.observed_main_sha, "observed_main_sha")
        _aware(self.lease_scan_at, "lease_scan_at")


@dataclass(frozen=True)
class LeaseSnapshot:
    lease_id: str
    owner_session_id: str
    owner_agent_id: str
    context_id: str
    scope: str
    acquired_at: datetime
    expires_at: datetime
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if not self.lease_id or not self.owner_session_id or not self.owner_agent_id:
            raise ValueError("lease identity fields are required")
        if not self.context_id:
            raise ValueError("lease context_id is required")
        _aware(self.acquired_at, "acquired_at")
        _aware(self.expires_at, "expires_at")
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be later than acquired_at")


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    codes: tuple[GuardCode, ...]

    @property
    def primary_code(self) -> GuardCode:
        return self.codes[0]

    def as_dict(self) -> dict[str, object]:
        return {"allowed": self.allowed, "codes": [code.value for code in self.codes]}


@dataclass(frozen=True)
class ComplianceFinding:
    subject_type: str
    subject_id: str
    session_id: str | None
    allowed: bool
    codes: tuple[GuardCode, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "allowed": self.allowed,
            "codes": [code.value for code in self.codes],
        }


def _dedupe_codes(codes: Iterable[GuardCode]) -> tuple[GuardCode, ...]:
    seen: set[GuardCode] = set()
    ordered: list[GuardCode] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return tuple(ordered)


def authorize_lease(
    *,
    policy: BootstrapPolicy,
    session: SessionSnapshot | None,
    ack: BootstrapAckSnapshot | None,
    lease: LeaseSnapshot,
    now: datetime,
    prelease: PreLeaseRefresh | None,
) -> GuardDecision:
    """Authorize a *live/proposed* write lease under the bootstrap contract.

    A full bootstrap acknowledgement may be older than the current Git commit
    when the manifest version is unchanged.  The mandatory ``prelease`` refresh
    is what proves the writer re-read current main + concurrency immediately
    before acquisition.  This avoids forcing a full context reload for every
    unrelated commit while remaining fail-closed on stale write attempts.
    """

    _aware(now, "now")
    codes: list[GuardCode] = []

    if session is None:
        return GuardDecision(False, (GuardCode.MISSING_SESSION,))

    if session.status != "ACTIVE":
        codes.append(GuardCode.SESSION_NOT_ACTIVE)
    if lease.owner_session_id != session.session_id or lease.owner_agent_id != session.agent_id:
        codes.append(GuardCode.LEASE_OWNER_MISMATCH)
    if lease.context_id != session.context_id or lease.context_id != policy.context_id:
        codes.append(GuardCode.LEASE_CONTEXT_MISMATCH)
    if not lease.scope.strip():
        codes.append(GuardCode.LEASE_SCOPE_EMPTY)
    if lease.status != "ACTIVE":
        codes.append(GuardCode.LEASE_NOT_ACTIVE)
    if lease.expires_at <= now:
        codes.append(GuardCode.LEASE_EXPIRED)

    if ack is None:
        codes.append(GuardCode.MISSING_BOOTSTRAP_ACK)
        return GuardDecision(False, _dedupe_codes(codes))

    if ack.event_at < session.started_at:
        codes.append(GuardCode.ACK_BEFORE_SESSION)
    if ack.event_at > lease.acquired_at:
        codes.append(GuardCode.ACK_AFTER_LEASE)
    if ack.session_id != session.session_id or ack.agent_id != session.agent_id:
        codes.append(GuardCode.ACK_IDENTITY_MISMATCH)
    if ack.context_id != session.context_id or ack.context_id != policy.context_id:
        codes.append(GuardCode.ACK_CONTEXT_MISMATCH)
    if ack.manifest_version != policy.manifest_version:
        codes.append(GuardCode.STALE_MANIFEST_VERSION)
    if not ack.public_read_set_sha256 and not ack.public_read_refs:
        codes.append(GuardCode.MISSING_PUBLIC_READ_PROOF)
    if not ack.private_event_watermark.strip():
        codes.append(GuardCode.MISSING_PRIVATE_EVENT_WATERMARK)
    if ack.lease_scan_at > ack.event_at:
        codes.append(GuardCode.ACK_READSET_TIMING_INVALID)

    if prelease is None:
        codes.append(GuardCode.MISSING_PRELEASE_REFRESH)
    else:
        if prelease.observed_main_sha != policy.current_main_sha:
            codes.append(GuardCode.PRELEASE_MAIN_SHA_STALE)
        if not prelease.private_event_watermark.strip():
            codes.append(GuardCode.MISSING_PRELEASE_EVENT_WATERMARK)
        if prelease.lease_scan_at < ack.event_at:
            codes.append(GuardCode.LEASE_SCAN_BEFORE_ACK)
        if prelease.lease_scan_at > lease.acquired_at:
            codes.append(GuardCode.LEASE_SCAN_AFTER_ACQUIRE)
        else:
            age = lease.acquired_at - prelease.lease_scan_at
            if age > policy.max_prelease_scan_age:
                codes.append(GuardCode.LEASE_SCAN_STALE)

    final = _dedupe_codes(codes)
    if final:
        return GuardDecision(False, final)
    return GuardDecision(True, (GuardCode.COMPLIANT,))


def audit_control_plane(
    *,
    policy: BootstrapPolicy,
    sessions: Sequence[SessionSnapshot],
    acks: Sequence[BootstrapAckSnapshot],
    leases: Sequence[LeaseSnapshot],
    now: datetime,
    prelease_by_lease: Mapping[str, PreLeaseRefresh] | None = None,
) -> tuple[ComplianceFinding, ...]:
    """Audit current control-plane bootstrap compliance.

    The default watchdog focuses on *currently active* sessions/leases. Closed
    pre-contract history is classified as legacy rather than retroactively
    judged by a contract that did not yet exist.
    """

    _aware(now, "now")
    prelease_by_lease = prelease_by_lease or {}
    findings: list[ComplianceFinding] = []

    session_groups: dict[str, list[SessionSnapshot]] = {}
    for session in sessions:
        session_groups.setdefault(session.session_id, []).append(session)

    reused_ids = {sid for sid, rows in session_groups.items() if len(rows) > 1}
    for sid in sorted(reused_ids):
        findings.append(
            ComplianceFinding(
                subject_type="session",
                subject_id=sid,
                session_id=sid,
                allowed=False,
                codes=(GuardCode.SESSION_REUSED,),
            )
        )

    ack_by_session: dict[str, list[BootstrapAckSnapshot]] = {}
    for ack in acks:
        ack_by_session.setdefault(ack.session_id, []).append(ack)
    for rows in ack_by_session.values():
        rows.sort(key=lambda value: value.event_at)

    for session in sessions:
        if session.session_id in reused_ids or session.status != "ACTIVE":
            continue
        valid_identity_ack = any(
            ack.event_at >= session.started_at
            and ack.agent_id == session.agent_id
            and ack.context_id == session.context_id
            and ack.manifest_version == policy.manifest_version
            for ack in ack_by_session.get(session.session_id, ())
        )
        if not valid_identity_ack and session.started_at >= policy.effective_at:
            findings.append(
                ComplianceFinding(
                    subject_type="session",
                    subject_id=session.session_id,
                    session_id=session.session_id,
                    allowed=False,
                    codes=(GuardCode.MISSING_BOOTSTRAP_ACK,),
                )
            )

    session_by_id = {
        sid: rows[0] for sid, rows in session_groups.items() if len(rows) == 1
    }

    for lease in leases:
        # Historical closed leases remain useful for archaeology but are not an
        # active authorization problem.  Record pre-contract history only.
        if lease.status != "ACTIVE":
            if lease.acquired_at < policy.effective_at:
                findings.append(
                    ComplianceFinding(
                        subject_type="lease",
                        subject_id=lease.lease_id,
                        session_id=lease.owner_session_id,
                        allowed=False,
                        codes=(GuardCode.LEGACY_PRE_CONTRACT,),
                    )
                )
            continue

        session = session_by_id.get(lease.owner_session_id)
        eligible_acks = [
            ack
            for ack in ack_by_session.get(lease.owner_session_id, ())
            if ack.event_at <= lease.acquired_at
        ]
        ack = eligible_acks[-1] if eligible_acks else None
        decision = authorize_lease(
            policy=policy,
            session=session,
            ack=ack,
            lease=lease,
            now=now,
            prelease=prelease_by_lease.get(lease.lease_id),
        )
        findings.append(
            ComplianceFinding(
                subject_type="lease",
                subject_id=lease.lease_id,
                session_id=lease.owner_session_id,
                allowed=decision.allowed,
                codes=decision.codes,
            )
        )

    return tuple(findings)
