"""Pure global convergence-barrier resolution for writer coordination.

A global barrier is higher-level coordination state (freeze, convergence gate,
incident hold) that can block one or more write intents independently of lease
overlap. This module is deliberately provider-neutral and mutation-free.

Adapters must supply the complete project/context barrier history through one
authoritative EventBus watermark. An ACTIVE barrier remains ACTIVE until a
higher revision for the same barrier_id explicitly records RELEASED. Missing
history, conflicting latest revisions or a stale/incomplete scan fail closed.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Sequence

_SHA64 = re.compile(r"^[0-9a-f]{64}$")
_ALL_INTENTS = "*"


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def scope_sha256(scope: str) -> str:
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("scope must be a non-empty string")
    return hashlib.sha256(scope.encode("utf-8")).hexdigest()


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class BarrierState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class BarrierCheckCode(str, Enum):
    CLEAR = "CLEAR"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    MISMATCH = "MISMATCH"
    ACTIVE = "ACTIVE"


@dataclass(frozen=True)
class BarrierRecord:
    """One append-only revision for one durable barrier identity.

    scope_sha256=None means project/context-wide. Otherwise the barrier is
    exact-scope only. blocked_intents accepts exact WriteIntent string values or
    "*" for every mutating intent.
    """

    barrier_id: str
    revision: int
    event_id: str
    project_id: str
    context_id: str
    state: BarrierState
    blocked_intents: tuple[str, ...]
    updated_at: datetime
    scope_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.barrier_id or not self.event_id or not self.project_id or not self.context_id:
            raise ValueError("barrier identity fields are required")
        if self.revision <= 0:
            raise ValueError("barrier revision must be positive")
        _aware(self.updated_at, "updated_at")
        if not self.blocked_intents:
            raise ValueError("blocked_intents cannot be empty")
        if any(not isinstance(value, str) or not value for value in self.blocked_intents):
            raise ValueError("blocked_intents must contain non-empty strings")
        if tuple(sorted(set(self.blocked_intents))) != self.blocked_intents:
            raise ValueError("blocked_intents must be sorted and unique")
        if self.scope_sha256 is not None and not _SHA64.fullmatch(self.scope_sha256):
            raise ValueError("scope_sha256 must be 64 lowercase hex chars")

    def canonical(self) -> dict[str, object]:
        return {
            "barrier_id": self.barrier_id,
            "revision": self.revision,
            "event_id": self.event_id,
            "project_id": self.project_id,
            "context_id": self.context_id,
            "state": self.state.value,
            "blocked_intents": list(self.blocked_intents),
            "scope_sha256": self.scope_sha256,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class GlobalBarrierSnapshot:
    """Resolved barrier state for one exact proposed write."""

    project_id: str
    context_id: str
    intent: str
    scope_sha256: str
    observed_at: datetime
    event_watermark: str
    authority_complete: bool
    revision_sha256: str
    active_barrier_ids: tuple[str, ...]
    conflict_barrier_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.project_id or not self.context_id or not self.intent:
            raise ValueError("snapshot identity fields are required")
        if not _SHA64.fullmatch(self.scope_sha256):
            raise ValueError("scope_sha256 must be 64 lowercase hex chars")
        _aware(self.observed_at, "observed_at")
        if not self.event_watermark:
            raise ValueError("event_watermark is required")
        if not _SHA64.fullmatch(self.revision_sha256):
            raise ValueError("revision_sha256 must be 64 lowercase hex chars")
        for field_name in ("active_barrier_ids", "conflict_barrier_ids"):
            values = getattr(self, field_name)
            if tuple(sorted(set(values))) != values or any(not value for value in values):
                raise ValueError(f"{field_name} must be sorted unique non-empty strings")

    @property
    def authority_known(self) -> bool:
        return self.authority_complete and not self.conflict_barrier_ids

    @property
    def blocked(self) -> bool:
        return self.authority_known and bool(self.active_barrier_ids)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "UEX_GLOBAL_BARRIER_SNAPSHOT",
            "version": "1.0.0",
            "project_id": self.project_id,
            "context_id": self.context_id,
            "intent": self.intent,
            "scope_sha256": self.scope_sha256,
            "observed_at": self.observed_at.isoformat(),
            "event_watermark": self.event_watermark,
            "authority_complete": self.authority_complete,
            "revision_sha256": self.revision_sha256,
            "active_barrier_ids": list(self.active_barrier_ids),
            "conflict_barrier_ids": list(self.conflict_barrier_ids),
        }


@dataclass(frozen=True)
class BarrierCheck:
    allowed: bool
    codes: tuple[BarrierCheckCode, ...]

    @property
    def primary_code(self) -> BarrierCheckCode:
        return self.codes[0]


def _applies(record: BarrierRecord, *, intent: str, exact_scope_sha256: str) -> bool:
    intent_match = _ALL_INTENTS in record.blocked_intents or intent in record.blocked_intents
    scope_match = record.scope_sha256 is None or record.scope_sha256 == exact_scope_sha256
    return intent_match and scope_match


def resolve_global_barriers(
    *,
    records: Sequence[BarrierRecord],
    project_id: str,
    context_id: str,
    intent: str,
    scope: str,
    observed_at: datetime,
    event_watermark: str,
    source_complete: bool,
) -> GlobalBarrierSnapshot:
    """Resolve latest explicit barrier revisions for one exact write.

    records must contain the complete durable barrier history for the
    project/context through event_watermark. The resolver never interprets
    absence from a partial query as release.
    """

    _aware(observed_at, "observed_at")
    if not project_id or not context_id or not intent or not event_watermark:
        raise ValueError("project/context/intent/watermark are required")
    exact_scope_sha256 = scope_sha256(scope)

    grouped: dict[str, list[BarrierRecord]] = {}
    for record in records:
        if record.project_id != project_id or record.context_id != context_id:
            continue
        grouped.setdefault(record.barrier_id, []).append(record)

    latest: list[BarrierRecord] = []
    conflicts: list[str] = []
    for barrier_id, rows in grouped.items():
        max_revision = max(row.revision for row in rows)
        candidates = [row for row in rows if row.revision == max_revision]
        canonical = {_sha256(row.canonical()) for row in candidates}
        if len(canonical) != 1:
            conflicts.append(barrier_id)
            continue
        latest.append(sorted(candidates, key=lambda row: row.event_id)[0])

    applicable = sorted(
        (record for record in latest if _applies(record, intent=intent, exact_scope_sha256=exact_scope_sha256)),
        key=lambda row: row.barrier_id,
    )
    active = tuple(sorted(record.barrier_id for record in applicable if record.state is BarrierState.ACTIVE))
    revision_payload = {
        "project_id": project_id,
        "context_id": context_id,
        "intent": intent,
        "scope_sha256": exact_scope_sha256,
        "latest_applicable_records": [record.canonical() for record in applicable],
    }
    return GlobalBarrierSnapshot(
        project_id=project_id,
        context_id=context_id,
        intent=intent,
        scope_sha256=exact_scope_sha256,
        observed_at=observed_at,
        event_watermark=event_watermark,
        authority_complete=bool(source_complete),
        revision_sha256=_sha256(revision_payload),
        active_barrier_ids=active,
        conflict_barrier_ids=tuple(sorted(conflicts)),
    )


def evaluate_global_barrier(
    snapshot: GlobalBarrierSnapshot | None,
    *,
    project_id: str,
    context_id: str,
    intent: str,
    scope: str,
    now: datetime,
    max_age_seconds: int,
) -> BarrierCheck:
    """Fail closed unless a complete fresh exact-scope snapshot is clear."""

    _aware(now, "now")
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    if snapshot is None or not snapshot.authority_known:
        return BarrierCheck(False, (BarrierCheckCode.UNKNOWN,))

    expected_scope = scope_sha256(scope)
    if (
        snapshot.project_id != project_id
        or snapshot.context_id != context_id
        or snapshot.intent != intent
        or snapshot.scope_sha256 != expected_scope
    ):
        return BarrierCheck(False, (BarrierCheckCode.MISMATCH,))

    age = now - snapshot.observed_at
    if age < timedelta(0) or age > timedelta(seconds=max_age_seconds):
        return BarrierCheck(False, (BarrierCheckCode.STALE,))

    if snapshot.active_barrier_ids:
        return BarrierCheck(False, (BarrierCheckCode.ACTIVE,))

    return BarrierCheck(True, (BarrierCheckCode.CLEAR,))
