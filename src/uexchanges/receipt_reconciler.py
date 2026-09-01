from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from .forms.models import SubmissionAttempt, SubmissionReceipt
from .forms.receipts import reconcile_receipt
from .runtime_v2.models import RuntimeDomainEvent, RuntimeEventKind


@dataclass(frozen=True)
class ReceiptCandidate:
    application_id: str
    submitted_at: datetime
    source_ref: str
    source_version: str
    provider_reference: str | None = None
    email_receipt_ref: str | None = None
    confirmation_url: str | None = None
    confirmation_text_hash: str | None = None
    screenshot_ref: str | None = None
    authoritative_confirmation: bool = False

    def __post_init__(self) -> None:
        if self.submitted_at.tzinfo is None or self.submitted_at.utcoffset() is None:
            raise ValueError("submitted_at must be timezone-aware")
        for value, name in (
            (self.application_id, "application_id"),
            (self.source_ref, "source_ref"),
            (self.source_version, "source_version"),
        ):
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True)
class ReceiptReconciliation:
    receipt: SubmissionReceipt
    reconciled_attempt: SubmissionAttempt
    runtime_event: RuntimeDomainEvent


def reconcile_receipt_candidate(
    *,
    candidate: ReceiptCandidate,
    attempt: SubmissionAttempt,
    verification_action_id: str | None = None,
) -> ReceiptReconciliation:
    """Convert already-verified receipt evidence into canonical receipt contracts.

    Raw email prose is deliberately out of scope. The caller must explicitly assert
    authoritative_confirmation after reading the source/portal/thread.
    """
    if not candidate.authoritative_confirmation:
        raise ValueError("receipt candidate is not authoritative")
    if candidate.application_id != attempt.application_id:
        raise ValueError("receipt candidate application_id does not match attempt")
    if candidate.submitted_at < attempt.attempted_at:
        raise ValueError("receipt cannot predate submission attempt")

    strong_ref = bool(candidate.provider_reference or candidate.email_receipt_ref)
    captured_confirmation = bool(
        candidate.confirmation_text_hash and candidate.screenshot_ref
    )
    if not (strong_ref or captured_confirmation):
        raise ValueError("candidate lacks strong receipt evidence")

    raw = (
        f"{attempt.application_id}|{attempt.submission_key}|{candidate.source_version}|"
        f"{candidate.provider_reference or candidate.email_receipt_ref or candidate.confirmation_text_hash}"
    )
    receipt_id = "receipt_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    receipt = SubmissionReceipt(
        receipt_id=receipt_id,
        application_id=attempt.application_id,
        submission_key=attempt.submission_key,
        submitted_at=candidate.submitted_at,
        form_fingerprint=attempt.form_fingerprint,
        plan_hash=attempt.plan_hash,
        confirmation_url=candidate.confirmation_url,
        confirmation_text_hash=candidate.confirmation_text_hash,
        screenshot_ref=candidate.screenshot_ref,
        provider_reference=candidate.provider_reference,
        email_receipt_ref=candidate.email_receipt_ref,
        evidence_refs=(candidate.source_ref,),
    )
    reconciled = reconcile_receipt(attempt=attempt, receipt=receipt)
    event = RuntimeDomainEvent(
        event_id=f"rgevt:{receipt_id}",
        kind=RuntimeEventKind.RECEIPT_CONFIRMED,
        application_id=attempt.application_id,
        occurred_at=candidate.submitted_at,
        source_ref=candidate.source_ref,
        source_version=candidate.source_version,
        payload={
            "receipt_ref": receipt_id,
            "verification_action_id": verification_action_id,
            "executor": "AGENT",
        },
    )
    return ReceiptReconciliation(receipt, reconciled, event)


def gmail_receipt_candidate(
    *,
    application_id: str,
    message_id: str,
    message_timestamp: datetime,
    authoritative_confirmation: bool,
    provider_reference: str | None = None,
) -> ReceiptCandidate:
    if not message_id.strip():
        raise ValueError("message_id is required")
    return ReceiptCandidate(
        application_id=application_id,
        submitted_at=message_timestamp,
        source_ref=f"gmail:{message_id}",
        source_version=f"gmail:{message_id}:{message_timestamp.isoformat()}",
        email_receipt_ref=f"gmail:{message_id}",
        provider_reference=provider_reference,
        authoritative_confirmation=authoritative_confirmation,
    )
