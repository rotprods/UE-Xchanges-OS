from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from .models import RuntimeDomainEvent, RuntimeEventKind


class IngressSource(str, Enum):
    GMAIL = "gmail"
    FORM = "form"
    RECEIPT = "receipt"
    OFFICIAL_SOURCE = "official_source"
    ORGANISER = "organiser"
    HUMAN = "human"
    SYSTEM = "system"


STRONG_RECEIPT_AUTHORITIES = frozenset(
    {
        "provider_confirmation",
        "email_receipt",
        "captured_confirmation",
        "organiser_submission_confirmation",
    }
)


@dataclass(frozen=True)
class NormalizedIngress:
    """Value-safe input to the dispatcher.

    Raw mailbox/web/form prose is deliberately outside this contract.  A caller
    must first normalize an observed fact into one explicit event kind and
    payload.  Routing never uses fuzzy title matching.
    """

    source: IngressSource
    source_id: str
    source_item_id: str
    source_version: str
    observed_at: datetime
    kind: RuntimeEventKind
    payload: Mapping[str, Any] = field(default_factory=dict)
    application_id: str | None = None
    opportunity_id: str | None = None
    authority: str = "normalized_source"
    sequence: int | None = None

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        for value, name in (
            (self.source_id, "source_id"),
            (self.source_item_id, "source_item_id"),
            (self.source_version, "source_version"),
            (self.authority, "authority"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if not self.application_id and not self.opportunity_id:
            raise ValueError("application_id or opportunity_id is required")
        if self.sequence is not None and self.sequence < 0:
            raise ValueError("sequence must be >= 0")

    @property
    def source_ref(self) -> str:
        return f"{self.source.value}:{self.source_item_id}"

    @property
    def ingress_idempotency_key(self) -> str:
        raw = json.dumps(
            [
                self.source.value,
                self.source_id,
                self.source_item_id,
                self.source_version,
                self.kind.value,
                dict(self.payload),
            ],
            ensure_ascii=False,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        return "rg21ing_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ExplicitEventRouter:
    """Resolve only explicit identifiers; never semantic/fuzzy names."""

    def __init__(self, opportunity_to_application: Mapping[str, str] | None = None) -> None:
        self._opportunity_to_application = dict(opportunity_to_application or {})

    def route(self, ingress: NormalizedIngress) -> str | None:
        if ingress.application_id:
            return ingress.application_id
        assert ingress.opportunity_id is not None
        return self._opportunity_to_application.get(ingress.opportunity_id)

    def register(self, *, opportunity_id: str, application_id: str) -> None:
        if not opportunity_id.strip() or not application_id.strip():
            raise ValueError("opportunity_id/application_id must be non-empty")
        existing = self._opportunity_to_application.get(opportunity_id)
        if existing is not None and existing != application_id:
            raise ValueError("opportunity already routes to another application")
        self._opportunity_to_application[opportunity_id] = application_id


def to_domain_event(ingress: NormalizedIngress, *, application_id: str) -> RuntimeDomainEvent:
    """Validate authority-sensitive kinds and build the RG2 domain event."""
    if not application_id.strip():
        raise ValueError("application_id must be non-empty")

    payload = dict(ingress.payload)
    if ingress.kind is RuntimeEventKind.RECEIPT_CONFIRMED:
        if ingress.authority not in STRONG_RECEIPT_AUTHORITIES:
            raise ValueError("receipt event requires strong authoritative receipt evidence")
        if payload.get("submission_identity_bound") is not True:
            raise ValueError("receipt event must be bound to canonical submission identity")
        if not str(payload.get("receipt_ref") or "").strip():
            raise ValueError("receipt event requires payload.receipt_ref")

    if ingress.kind is RuntimeEventKind.GATE_RESOLVED:
        if not str(payload.get("gate_name") or "").strip():
            raise ValueError("gate_resolved requires payload.gate_name")
        if str(payload.get("result") or "").lower() not in {"pass", "fail", "unknown"}:
            raise ValueError("gate_resolved result must be pass/fail/unknown")

    event_seed = f"{ingress.ingress_idempotency_key}|{application_id}"
    event_id = "rg21evt_" + hashlib.sha256(event_seed.encode("utf-8")).hexdigest()[:24]
    return RuntimeDomainEvent(
        event_id=event_id,
        kind=ingress.kind,
        application_id=application_id,
        occurred_at=ingress.observed_at,
        source_ref=ingress.source_ref,
        source_version=ingress.source_version,
        payload=payload,
    )
