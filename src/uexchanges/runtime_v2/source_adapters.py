from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..forms.models import FormExecutionPlan, SubmissionReceipt
from ..models import GateResult
from .event_router import (
    IngressSource,
    NormalizedIngress,
    STRONG_RECEIPT_AUTHORITIES,
)
from .form_bridge import form_plan_runtime_events
from .models import RuntimeEventKind


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _safe_reason_code(value: str) -> str:
    reason = _nonempty(value, "reason_code")
    if "\n" in reason or "\r" in reason:
        raise ValueError("reason_code must be a concise single-line fact, not raw provider prose")
    if len(reason) > 240:
        raise ValueError("reason_code is too long; persist raw evidence upstream, not in RuntimeGraph")
    return reason


def _identity(application_id: str | None, opportunity_id: str | None) -> tuple[str | None, str | None]:
    if application_id is not None:
        application_id = _nonempty(application_id, "application_id")
    if opportunity_id is not None:
        opportunity_id = _nonempty(opportunity_id, "opportunity_id")
    if application_id is None and opportunity_id is None:
        raise ValueError("application_id or opportunity_id is required")
    return application_id, opportunity_id


@dataclass(frozen=True)
class GmailSourceAdapter:
    """Normalize explicit facts already extracted from a Gmail thread.

    This adapter deliberately has no raw-message/body argument and no receipt method.
    A Gmail message can become a receipt only after the canonical Receipt Reconciler
    constructs a strong SubmissionReceipt bound to submission identity.
    """

    source_id: str = "gmail:organiser-replies"

    def gate_fact(
        self,
        *,
        message_id: str,
        source_version: str,
        observed_at: datetime,
        gate_name: str,
        result: GateResult,
        reason_code: str,
        application_id: str | None = None,
        opportunity_id: str | None = None,
        sequence: int | None = None,
    ) -> NormalizedIngress:
        application_id, opportunity_id = _identity(application_id, opportunity_id)
        return NormalizedIngress(
            source=IngressSource.GMAIL,
            source_id=_nonempty(self.source_id, "source_id"),
            source_item_id=_nonempty(message_id, "message_id"),
            source_version=_nonempty(source_version, "source_version"),
            observed_at=_aware(observed_at, "observed_at"),
            kind=RuntimeEventKind.GATE_RESOLVED,
            application_id=application_id,
            opportunity_id=opportunity_id,
            authority="organiser_email_fact",
            sequence=sequence,
            payload={
                "gate_name": _nonempty(gate_name, "gate_name"),
                "result": result.value,
                "reason": _safe_reason_code(reason_code),
            },
        )

    def evidence_fact(
        self,
        *,
        message_id: str,
        source_version: str,
        observed_at: datetime,
        evidence_code: str,
        application_id: str | None = None,
        opportunity_id: str | None = None,
        sequence: int | None = None,
    ) -> NormalizedIngress:
        application_id, opportunity_id = _identity(application_id, opportunity_id)
        code = _safe_reason_code(evidence_code)
        return NormalizedIngress(
            source=IngressSource.GMAIL,
            source_id=_nonempty(self.source_id, "source_id"),
            source_item_id=_nonempty(message_id, "message_id"),
            source_version=_nonempty(source_version, "source_version"),
            observed_at=_aware(observed_at, "observed_at"),
            kind=RuntimeEventKind.EVIDENCE_ADDED,
            application_id=application_id,
            opportunity_id=opportunity_id,
            authority="organiser_email_fact",
            sequence=sequence,
            payload={"evidence_ref": f"gmail:{message_id}", "evidence_code": code},
        )


@dataclass(frozen=True)
class OfficialSourceAdapter:
    """Normalize explicit status/deadline facts from an authoritative call source."""

    provider: str

    def deadline_fact(
        self,
        *,
        call_id: str,
        source_version: str,
        observed_at: datetime,
        deadline: datetime,
        application_id: str | None = None,
        opportunity_id: str | None = None,
        sequence: int | None = None,
    ) -> NormalizedIngress:
        application_id, opportunity_id = _identity(application_id, opportunity_id)
        return NormalizedIngress(
            source=IngressSource.OFFICIAL_SOURCE,
            source_id=f"official:{_nonempty(self.provider, 'provider')}",
            source_item_id=_nonempty(call_id, "call_id"),
            source_version=_nonempty(source_version, "source_version"),
            observed_at=_aware(observed_at, "observed_at"),
            kind=RuntimeEventKind.DEADLINE_UPDATED,
            application_id=application_id,
            opportunity_id=opportunity_id,
            authority="official_call_source",
            sequence=sequence,
            payload={"deadline": _aware(deadline, "deadline").isoformat()},
        )

    def gate_fact(
        self,
        *,
        call_id: str,
        source_version: str,
        observed_at: datetime,
        gate_name: str,
        result: GateResult,
        reason_code: str,
        application_id: str | None = None,
        opportunity_id: str | None = None,
        sequence: int | None = None,
    ) -> NormalizedIngress:
        application_id, opportunity_id = _identity(application_id, opportunity_id)
        return NormalizedIngress(
            source=IngressSource.OFFICIAL_SOURCE,
            source_id=f"official:{_nonempty(self.provider, 'provider')}",
            source_item_id=_nonempty(call_id, "call_id"),
            source_version=_nonempty(source_version, "source_version"),
            observed_at=_aware(observed_at, "observed_at"),
            kind=RuntimeEventKind.GATE_RESOLVED,
            application_id=application_id,
            opportunity_id=opportunity_id,
            authority="official_call_source",
            sequence=sequence,
            payload={
                "gate_name": _nonempty(gate_name, "gate_name"),
                "result": result.value,
                "reason": _safe_reason_code(reason_code),
            },
        )


@dataclass(frozen=True)
class FormGatewayAdapter:
    """Convert the existing value-free FormExecutionPlan bridge into dispatcher ingress."""

    source_id_prefix: str = "form-gateway"

    def plan_ingresses(
        self,
        *,
        plan: FormExecutionPlan,
        observed_at: datetime,
        sequence_base: int | None = None,
    ) -> tuple[NormalizedIngress, ...]:
        observed_at = _aware(observed_at, "observed_at")
        domain_events = form_plan_runtime_events(plan=plan, observed_at=observed_at)
        output: list[NormalizedIngress] = []
        for index, event in enumerate(domain_events):
            sequence = None if sequence_base is None else sequence_base + index
            output.append(
                NormalizedIngress(
                    source=IngressSource.FORM,
                    source_id=f"{self.source_id_prefix}:{plan.provider}",
                    source_item_id=event.event_id,
                    source_version=event.source_version,
                    observed_at=event.occurred_at,
                    kind=event.kind,
                    application_id=plan.application_id,
                    authority="form_gateway_verified",
                    sequence=sequence,
                    payload=dict(event.payload),
                )
            )
        return tuple(output)


@dataclass(frozen=True)
class ReceiptSourceAdapter:
    """Normalize only strong canonical SubmissionReceipt objects."""

    source_id: str = "receipt:reconciler"

    def receipt_ingress(
        self,
        *,
        receipt: SubmissionReceipt,
        observed_at: datetime,
        sequence: int | None = None,
    ) -> NormalizedIngress:
        observed_at = _aware(observed_at, "observed_at")
        if receipt.provider_reference:
            authority = "provider_confirmation"
        elif receipt.email_receipt_ref:
            authority = "email_receipt"
        elif receipt.confirmation_text_hash and receipt.screenshot_ref:
            authority = "captured_confirmation"
        else:
            raise ValueError("SubmissionReceipt lacks a strong receipt authority")
        if authority not in STRONG_RECEIPT_AUTHORITIES:
            raise ValueError("receipt authority is not accepted by RuntimeGraph")
        return NormalizedIngress(
            source=IngressSource.RECEIPT,
            source_id=_nonempty(self.source_id, "source_id"),
            source_item_id=receipt.receipt_id,
            source_version=f"{receipt.receipt_id}:{receipt.submitted_at.isoformat()}:{receipt.submission_key}",
            observed_at=observed_at,
            kind=RuntimeEventKind.RECEIPT_CONFIRMED,
            application_id=receipt.application_id,
            authority=authority,
            sequence=sequence,
            payload={
                "receipt_ref": f"receipt:{receipt.receipt_id}",
                "submission_identity_bound": True,
            },
        )


def flatten_ingresses(groups: Iterable[Iterable[NormalizedIngress]]) -> tuple[NormalizedIngress, ...]:
    return tuple(item for group in groups for item in group)
