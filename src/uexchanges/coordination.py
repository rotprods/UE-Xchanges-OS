from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Any, Collection


_ID_TOKEN = re.compile(r"[^A-Z0-9]+")


class SessionStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    HANDOFF_READY = "handoff_ready"
    COMPLETED = "completed"
    FAILED = "failed"


class LeaseStatus(str, Enum):
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class LeaseAction(str, Enum):
    ACQUIRE = "acquire"
    RENEW = "renew"
    BLOCK_CONFLICT = "block_conflict"
    TAKEOVER_EXPIRED = "takeover_expired"
    RELEASE = "release"


class EventApplyAction(str, Enum):
    APPLY = "apply"
    IGNORE_DUPLICATE = "ignore_duplicate"
    BLOCK_NO_LEASE = "block_no_lease"
    BLOCK_WRONG_OWNER = "block_wrong_owner"
    BLOCK_EXPIRED_LEASE = "block_expired_lease"
    BLOCK_SCOPE_MISMATCH = "block_scope_mismatch"
    BLOCK_LEASE_ID_MISMATCH = "block_lease_id_mismatch"


@dataclass(frozen=True)
class AgentSession:
    session_id: str
    agent_id: str
    project_id: str
    context_id: str
    started_at: datetime
    last_heartbeat: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    current_node: str | None = None
    lease_ids: tuple[str, ...] = ()
    input_state_ref: str | None = None
    output_state_ref: str | None = None
    handoff_summary: str | None = None
    capabilities: dict[str, bool] = field(default_factory=dict)
    writer_version: str = "coordination-v1"

    def __post_init__(self) -> None:
        _require_aware(self.started_at, "started_at")
        _require_aware(self.last_heartbeat, "last_heartbeat")
        if self.last_heartbeat < self.started_at:
            raise ValueError("last_heartbeat cannot precede started_at")
        _require_nonempty(self.session_id, "session_id")
        _require_nonempty(self.agent_id, "agent_id")
        _require_nonempty(self.project_id, "project_id")
        _require_nonempty(self.context_id, "context_id")


@dataclass(frozen=True)
class WorkLease:
    lease_id: str
    project_id: str
    context_id: str
    resource_type: str
    resource_id: str
    owner_agent_id: str
    owner_session_id: str
    acquired_at: datetime
    expires_at: datetime
    last_heartbeat: datetime
    status: LeaseStatus = LeaseStatus.ACTIVE
    conflict_policy: str = "BLOCK_OTHER_WRITERS"
    release_reason: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.acquired_at, "acquired_at"),
            (self.expires_at, "expires_at"),
            (self.last_heartbeat, "last_heartbeat"),
        ):
            _require_aware(value, name)
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be later than acquired_at")
        if self.last_heartbeat < self.acquired_at:
            raise ValueError("last_heartbeat cannot precede acquired_at")
        if self.status is LeaseStatus.ACTIVE and self.last_heartbeat > self.expires_at:
            raise ValueError("an active lease heartbeat cannot be after expiry")
        for value, name in (
            (self.lease_id, "lease_id"),
            (self.project_id, "project_id"),
            (self.context_id, "context_id"),
            (self.resource_type, "resource_type"),
            (self.resource_id, "resource_id"),
            (self.owner_agent_id, "owner_agent_id"),
            (self.owner_session_id, "owner_session_id"),
        ):
            _require_nonempty(value, name)

    def is_active_at(self, at: datetime) -> bool:
        _require_aware(at, "at")
        return self.status is LeaseStatus.ACTIVE and at < self.expires_at

    def covers(self, *, entity_type: str, entity_id: str) -> bool:
        return self.resource_type in {"*", entity_type} and self.resource_id in {
            "*",
            entity_id,
        }


@dataclass(frozen=True)
class AgentEvent:
    event_id: str
    occurred_at: datetime
    project_id: str
    context_id: str
    session_id: str
    agent_id: str
    event_type: str
    entity_type: str
    entity_id: str
    operation: str
    state_before: str | None
    state_after: str | None
    payload: dict[str, Any]
    source_ref: str | None
    causal_parent_event_id: str | None
    correlation_id: str | None
    lease_id: str | None
    idempotency_key: str
    severity: str = "INFO"
    ack_required: bool = False
    writer_version: str = "coordination-v1"

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        for value, name in (
            (self.event_id, "event_id"),
            (self.project_id, "project_id"),
            (self.context_id, "context_id"),
            (self.session_id, "session_id"),
            (self.agent_id, "agent_id"),
            (self.event_type, "event_type"),
            (self.entity_type, "entity_type"),
            (self.entity_id, "entity_id"),
            (self.operation, "operation"),
            (self.idempotency_key, "idempotency_key"),
        ):
            _require_nonempty(value, name)


@dataclass(frozen=True)
class LeaseDecision:
    action: LeaseAction
    allowed: bool
    reason: str
    lease: WorkLease | None


@dataclass(frozen=True)
class EventApplyDecision:
    action: EventApplyAction
    allowed: bool
    reason: str


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _require_nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _id_token(value: str) -> str:
    token = _ID_TOKEN.sub("-", value.upper()).strip("-")
    if not token:
        raise ValueError("identifier token cannot be empty")
    return token


def make_session_id(
    *, project_id: str, platform: str, started_at: datetime, sequence: int
) -> str:
    """Create the canonical human-readable ID used by the shared session registry."""
    _require_aware(started_at, "started_at")
    if sequence < 1 or sequence > 99:
        raise ValueError("sequence must be between 1 and 99")
    stamp = started_at.strftime("%Y%m%dT%H%M%S")
    return f"SES-{_id_token(project_id)}-{_id_token(platform)}-{stamp}-{sequence:02d}"


def build_idempotency_key(
    *,
    project_id: str,
    entity_type: str,
    entity_id: str,
    operation: str,
    authoritative_source_version: str,
) -> str:
    """Return a stable key; replaying one source-version transition becomes a no-op."""
    components = [
        _require_nonempty(project_id, "project_id"),
        _require_nonempty(entity_type, "entity_type"),
        _require_nonempty(entity_id, "entity_id"),
        _require_nonempty(operation, "operation"),
        _require_nonempty(authoritative_source_version, "authoritative_source_version"),
    ]
    raw = json.dumps(components, ensure_ascii=False, separators=(",", ":"))
    return "idem_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_agent_event(
    *,
    occurred_at: datetime,
    project_id: str,
    context_id: str,
    session_id: str,
    agent_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    operation: str,
    authoritative_source_version: str,
    state_before: str | None = None,
    state_after: str | None = None,
    payload: dict[str, Any] | None = None,
    source_ref: str | None = None,
    causal_parent_event_id: str | None = None,
    correlation_id: str | None = None,
    lease_id: str | None = None,
    severity: str = "INFO",
    ack_required: bool = False,
    writer_version: str = "coordination-v1",
) -> AgentEvent:
    _require_aware(occurred_at, "occurred_at")
    key = build_idempotency_key(
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        operation=operation,
        authoritative_source_version=authoritative_source_version,
    )
    event_id = "evt_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return AgentEvent(
        event_id=event_id,
        occurred_at=occurred_at,
        project_id=project_id,
        context_id=context_id,
        session_id=session_id,
        agent_id=agent_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        operation=operation,
        state_before=state_before,
        state_after=state_after,
        payload=dict(payload or {}),
        source_ref=source_ref,
        causal_parent_event_id=causal_parent_event_id,
        correlation_id=correlation_id,
        lease_id=lease_id,
        idempotency_key=key,
        severity=severity,
        ack_required=ack_required,
        writer_version=writer_version,
    )


def decide_lease(
    *,
    existing: WorkLease | None,
    lease_id: str,
    project_id: str,
    context_id: str,
    resource_type: str,
    resource_id: str,
    requester_agent_id: str,
    requester_session_id: str,
    now: datetime,
    expires_at: datetime,
) -> LeaseDecision:
    """Acquire, renew, block, or take over an expired/released exclusive lease."""
    _require_aware(now, "now")
    _require_aware(expires_at, "expires_at")
    if expires_at <= now:
        raise ValueError("expires_at must be later than now")

    requested_scope = (project_id, context_id, resource_type, resource_id)
    if existing is not None:
        existing_scope = (
            existing.project_id,
            existing.context_id,
            existing.resource_type,
            existing.resource_id,
        )
        if existing_scope != requested_scope:
            raise ValueError("existing lease scope does not match requested scope")

    if existing is None:
        lease = WorkLease(
            lease_id=lease_id,
            project_id=project_id,
            context_id=context_id,
            resource_type=resource_type,
            resource_id=resource_id,
            owner_agent_id=requester_agent_id,
            owner_session_id=requester_session_id,
            acquired_at=now,
            expires_at=expires_at,
            last_heartbeat=now,
        )
        return LeaseDecision(LeaseAction.ACQUIRE, True, "No active owner exists.", lease)

    same_owner = (
        existing.owner_agent_id == requester_agent_id
        and existing.owner_session_id == requester_session_id
    )
    if existing.is_active_at(now) and same_owner:
        lease = replace(existing, expires_at=expires_at, last_heartbeat=now)
        return LeaseDecision(LeaseAction.RENEW, True, "The current owner renewed.", lease)

    if existing.is_active_at(now):
        return LeaseDecision(
            LeaseAction.BLOCK_CONFLICT,
            False,
            "Another session owns an unexpired lease.",
            existing,
        )

    lease = WorkLease(
        lease_id=lease_id,
        project_id=project_id,
        context_id=context_id,
        resource_type=resource_type,
        resource_id=resource_id,
        owner_agent_id=requester_agent_id,
        owner_session_id=requester_session_id,
        acquired_at=now,
        expires_at=expires_at,
        last_heartbeat=now,
    )
    return LeaseDecision(
        LeaseAction.TAKEOVER_EXPIRED,
        True,
        "The previous lease was released or expired; takeover must be evented.",
        lease,
    )


def evaluate_event_application(
    *,
    event: AgentEvent,
    seen_idempotency_keys: Collection[str],
    lease: WorkLease | None,
    now: datetime,
    mutating: bool = True,
) -> EventApplyDecision:
    """Enforce duplicate and exclusive-writer guards before a projection mutation."""
    _require_aware(now, "now")
    if event.idempotency_key in seen_idempotency_keys:
        return EventApplyDecision(
            EventApplyAction.IGNORE_DUPLICATE,
            False,
            "The transition was already applied for this source version.",
        )
    if not mutating:
        return EventApplyDecision(
            EventApplyAction.APPLY, True, "Read-only/audit events do not require a lease."
        )
    if lease is None:
        return EventApplyDecision(
            EventApplyAction.BLOCK_NO_LEASE,
            False,
            "A mutating event requires an active lease.",
        )
    if not lease.is_active_at(now):
        return EventApplyDecision(
            EventApplyAction.BLOCK_EXPIRED_LEASE,
            False,
            "The lease is released or expired.",
        )
    if event.lease_id != lease.lease_id:
        return EventApplyDecision(
            EventApplyAction.BLOCK_LEASE_ID_MISMATCH,
            False,
            "The event does not reference the supplied lease.",
        )
    if (
        event.session_id != lease.owner_session_id
        or event.agent_id != lease.owner_agent_id
    ):
        return EventApplyDecision(
            EventApplyAction.BLOCK_WRONG_OWNER,
            False,
            "The event author is not the lease owner.",
        )
    if event.project_id != lease.project_id or event.context_id != lease.context_id:
        return EventApplyDecision(
            EventApplyAction.BLOCK_SCOPE_MISMATCH,
            False,
            "The event project/context is outside the lease scope.",
        )
    if not lease.covers(entity_type=event.entity_type, entity_id=event.entity_id):
        return EventApplyDecision(
            EventApplyAction.BLOCK_SCOPE_MISMATCH,
            False,
            "The event entity is outside the leased resource scope.",
        )
    return EventApplyDecision(
        EventApplyAction.APPLY, True, "Idempotency and lease guards pass."
    )


def heartbeat_session(session: AgentSession, *, at: datetime) -> AgentSession:
    _require_aware(at, "at")
    if session.status in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
        raise ValueError("a terminal session cannot heartbeat")
    if at < session.last_heartbeat:
        raise ValueError("session heartbeat must be monotonic")
    return replace(session, last_heartbeat=at)


def heartbeat_lease(lease: WorkLease, *, at: datetime) -> WorkLease:
    _require_aware(at, "at")
    if lease.status is not LeaseStatus.ACTIVE:
        raise ValueError("only an active lease can heartbeat")
    if at < lease.last_heartbeat:
        raise ValueError("lease heartbeat must be monotonic")
    if at >= lease.expires_at:
        raise ValueError("cannot heartbeat an expired lease; acquire a takeover")
    return replace(lease, last_heartbeat=at)


def release_lease(
    lease: WorkLease, *, requester_session_id: str, at: datetime, reason: str
) -> WorkLease:
    _require_aware(at, "at")
    _require_nonempty(reason, "reason")
    if lease.owner_session_id != requester_session_id:
        raise ValueError("only the owner session may release an active lease")
    if lease.status is not LeaseStatus.ACTIVE:
        raise ValueError("only an active lease may be released")
    if at < lease.last_heartbeat:
        raise ValueError("release time must not precede the last heartbeat")
    return replace(
        lease,
        status=LeaseStatus.RELEASED,
        last_heartbeat=at,
        expires_at=max(lease.expires_at, at),
        release_reason=reason,
    )
