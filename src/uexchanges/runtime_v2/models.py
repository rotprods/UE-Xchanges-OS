from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class RuntimeEventKind(str, Enum):
    EVIDENCE_ADDED = "evidence_added"
    GATE_RESOLVED = "gate_resolved"
    ACTION_COMPLETED = "action_completed"
    DEADLINE_UPDATED = "deadline_updated"
    RECEIPT_CONFIRMED = "receipt_confirmed"
    OUTCOME_RECORDED = "outcome_recorded"


class TemporalScope(str, Enum):
    CURRENT = "current"
    HISTORICAL = "historical"
    CALL_SPECIFIC = "call_specific"
    TIMELESS = "timeless"


class ClaimStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value


@dataclass(frozen=True)
class RuntimeDomainEvent:
    event_id: str
    kind: RuntimeEventKind
    application_id: str
    occurred_at: datetime
    source_ref: str
    source_version: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _aware(self.occurred_at, "occurred_at")
        for value, name in (
            (self.event_id, "event_id"),
            (self.application_id, "application_id"),
            (self.source_ref, "source_ref"),
            (self.source_version, "source_version"),
        ):
            _nonempty(value, name)

    @property
    def idempotency_key(self) -> str:
        raw = json.dumps(
            [
                self.application_id,
                self.kind.value,
                self.source_version,
                dict(self.payload),
            ],
            sort_keys=True,
            default=str,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return "rg2idem_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    application_id: str
    source_ref: str
    observed_at: datetime
    fact_key: str
    fact_value: Any
    temporal_scope: TemporalScope
    role_scopes: tuple[str, ...] = ("*",)
    supports_claim_keys: tuple[str, ...] = ()
    cannot_prove: tuple[str, ...] = ()
    authority: str = "source"
    confidence: float = 1.0

    def __post_init__(self) -> None:
        _aware(self.observed_at, "observed_at")
        for value, name in (
            (self.evidence_id, "evidence_id"),
            (self.application_id, "application_id"),
            (self.source_ref, "source_ref"),
            (self.fact_key, "fact_key"),
            (self.authority, "authority"),
        ):
            _nonempty(value, name)
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.role_scopes:
            raise ValueError("role_scopes must not be empty")


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    application_id: str
    claim_key: str
    value: Any
    evidence_ids: tuple[str, ...]
    temporal_scope: TemporalScope
    required_role: str = "*"
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.claim_id, "claim_id"),
            (self.application_id, "application_id"),
            (self.claim_key, "claim_key"),
            (self.required_role, "required_role"),
        ):
            _nonempty(value, name)
        if not self.evidence_ids:
            raise ValueError("claims require at least one evidence_id")
        if self.valid_from is not None:
            _aware(self.valid_from, "valid_from")
        if self.valid_until is not None:
            _aware(self.valid_until, "valid_until")
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot precede valid_from")
