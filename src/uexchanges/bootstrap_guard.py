"""Fail-closed bootstrap authorization and compliance auditing.

This module turns the repository's manifest-led bootstrap contract into a
pure, deterministic authorization primitive.  It intentionally has no Drive,
GitHub, browser or network dependencies so every writer surface can reuse the
same rules without duplicating policy.

The guard does not grant domain authority.  It answers a narrower question:
"May this session acquire/use this write lease under the current bootstrap
contract?"
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
    ACK_MAIN_SHA_STALE = "ACK_MAIN_SHA_STALE"
    PRELEASE_MAIN_SHA_STALE = "PRELEASE_MAIN_SHA_STALE"
    MISSING_PUBLIC_READ_PROOF = "MISSING_PUBLIC_READ_PROOF"
    MISSING_PRIVATE_EVENT_WATERMARK = "MISSING_PRIVATE_EVENT_WATERMARK"
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
        if self.public_read_set_sha256 is not None:
            if not re.fullmatch(r"[0-9a-f]{64}", self.public_read_set_sha256):
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
        if isinstance(payload, str):
            loaded = json.loads(payload)
        else:
            loaded = dict(payload)
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
        return {
            "allowed": self.allowed,
            "codes": [code.value for code in self.codes],
        }


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
    prelease: PreLeaseRefresh | None = None,
) -> GuardDecision:
    """Return whether an existing/proposed lease satisfies bootstrap v1.

    ``prelease`` is the live refresh immediately before acquisition.  For
    historical audit records that do not persist a separate refresh object,
    the acknowledgement's recorded main/lease-scan/watermark may be used.
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

    # Closed historical leases from before bootstrap v1 are classified rather
    # than retroactively treated as protocol violations.
    if lease.acquired_at < policy.effective_at and lease.status != "ACTIVE":
        historical = _dedupe_codes([GuardCode.LEGACY_PRE_CONTRACT, *codes])
        return GuardDecision(False, historical)

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
    if ack.observed_main_sha != policy.current_main_sha:
        codes.append(GuardCode.ACK_MAIN_SHA_STALE)
    if not ack.public_read_set_sha256 and not ack.public_read_refs:
        codes.append(GuardCode.MISSING_PUBLIC_READ_PROOF)
    if not ack.private_event_watermark.strip():
        codes.append(GuardCode.MISSING_PRIVATE_EVENT_WATERMARK)
    if ack.lease_scan_at > ack.event_at:
        # Initial bootstrap lease scan should be part of the read-set completed
        # no later than the acknowledgement itself.
        codes.append(GuardCode.LEASE_SCAN_AFTER_ACQUIRE)

    refresh = prelease or PreLeaseRefresh(
        observed_main_sha=ack.observed_main_sha,
        lease_scan_at=ack.lease_scan_at,
        private_event_watermark=ack.private_event_watermark,
    )
    if refresh.observed_main_sha != policy.current_main_sha:
        codes.append(GuardCode.PRELEASE_MAIN_SHA_STALE)
    if not refresh.private_event_watermark.strip():
        codes.append(GuardCode.MISSING_PRELEASE_EVENT_WATERMARK)
    if refresh.lease_scan_at < ack.event_at:
        # Acknowledgement proves bootstrap; acquisition requires one more fresh
        # concurrency/event-tail scan at or after the ack.
        if prelease is not None:
            codes.append(GuardCode.LEASE_SCAN_BEFORE_ACK)
    if refresh.lease_scan_at > lease.acquired_at:
        codes.append(GuardCode.LEASE_SCAN_AFTER_ACQUIRE)
    else:
        age = lease.acquired_at - refresh.lease_scan_at
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
) -> tuple[ComplianceFinding, ...]:
    """Audit session/lease bootstrap compliance from durable snapshots.

    The auditor is deliberately conservative.  It checks ACTIVE sessions and
    all leases.  Historical pre-contract closed leases are reported as legacy,
    while post-contract or currently-active leases require a valid bootstrap
    acknowledgement that predates acquisition.
    """

    _aware(now, "now")
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

    # An active post-contract session without any acknowledgement is already a
    # protocol violation even before it acquires a lease.
    for session in sessions:
        if session.session_id in reused_ids:
            continue
        if session.status == "ACTIVE" and now >= policy.effective_at:
            valid_identity_ack = any(
                ack.event_at >= session.started_at
                and ack.agent_id == session.agent_id
                and ack.context_id == session.context_id
                for ack in ack_by_session.get(session.session_id, ())
            )
            if not valid_identity_ack:
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
        sid: rows[0]
        for sid, rows in session_groups.items()
        if len(rows) == 1
    }

    for lease in leases:
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
            prelease=None,
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
