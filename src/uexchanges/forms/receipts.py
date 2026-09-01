from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
from typing import Any

from .models import (
    FormExecutionPlan,
    SubmissionAttempt,
    SubmissionAttemptStatus,
    SubmissionReceipt,
)
from .normalization import normalize_answer


class DuplicateDisposition(str, Enum):
    SAFE_TO_ATTEMPT = "safe_to_attempt"
    BLOCK_CONFIRMED_DUPLICATE = "block_confirmed_duplicate"
    RECONCILE_UNVERIFIED_ATTEMPT = "reconcile_unverified_attempt"


@dataclass(frozen=True)
class DuplicateDecision:
    disposition: DuplicateDisposition
    submission_key: str
    reason: str
    attempt_id: str | None = None
    receipt_id: str | None = None


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"value is not deterministic-JSON serializable: {type(value).__name__}")


def _sha256_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def answer_pack_hash(plan: FormExecutionPlan) -> str:
    """Hash the canonical semantic payload, never representation noise."""
    payload = {
        "fields": [
            {
                "field_key": field.field_key,
                "answer": normalize_answer(field),
            }
            for field in plan.fields
        ],
        "attachments": list(plan.attachments),
    }
    return _sha256_json(payload)


def submission_key(plan: FormExecutionPlan) -> str:
    """Stable idempotency key for application + structure + validation + payload."""
    validation_identity = plan.validation_signature or "validation:unbound"
    raw = (
        f"{plan.application_id}|{plan.form_fingerprint}|{validation_identity}|{answer_pack_hash(plan)}"
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def execution_plan_hash(plan: FormExecutionPlan) -> str:
    """Audit hash for the complete model-visible plan, excluding hidden secrets."""
    payload = {
        "plan_id": plan.plan_id,
        "application_id": plan.application_id,
        "opportunity_id": plan.opportunity_id,
        "canonical_form_url": plan.canonical_form_url,
        "provider": plan.provider,
        "form_fingerprint": plan.form_fingerprint,
        "validation_signature": plan.validation_signature,
        "ai_policy": plan.ai_policy,
        "auth_requirement": plan.auth_requirement,
        "submit_authority": plan.submit_authority,
        "allowed_origins": plan.allowed_origins,
        "created_at": plan.created_at,
        "expires_at": plan.expires_at,
        "source_version": plan.source_version,
        "attachments": plan.attachments,
        "state": plan.state,
        "fields": [
            {
                "field_key": field.field_key,
                "field_type": field.field_type,
                "required": field.required,
                "answer": normalize_answer(field),
                "answer_source": field.answer_source,
                "evidence_ids": field.evidence_ids,
                "ownership": field.ownership,
                "sensitivity": field.sensitivity,
                "editable_by_agent": field.editable_by_agent,
            }
            for field in plan.fields
        ],
    }
    return _sha256_json(payload)


def build_submission_attempt(*, plan: FormExecutionPlan, attempt_id: str, attempted_at: datetime) -> SubmissionAttempt:
    return SubmissionAttempt(
        attempt_id=attempt_id,
        application_id=plan.application_id,
        submission_key=submission_key(plan),
        attempted_at=attempted_at,
        form_fingerprint=plan.form_fingerprint,
        plan_hash=execution_plan_hash(plan),
    )


def evaluate_duplicate_guard(
    *,
    plan: FormExecutionPlan,
    attempts: tuple[SubmissionAttempt, ...] = (),
    receipts: tuple[SubmissionReceipt, ...] = (),
) -> DuplicateDecision:
    key = submission_key(plan)

    for receipt in receipts:
        if receipt.submission_key == key:
            return DuplicateDecision(
                DuplicateDisposition.BLOCK_CONFIRMED_DUPLICATE,
                key,
                "A receipt already confirms this exact application/form/validation/payload submission.",
                receipt_id=receipt.receipt_id,
            )

    unresolved_statuses = {
        SubmissionAttemptStatus.STARTED,
        SubmissionAttemptStatus.CONFIRMATION_OBSERVED,
        SubmissionAttemptStatus.UNVERIFIED,
        SubmissionAttemptStatus.RECEIPT_CONFIRMED,
    }
    for attempt in attempts:
        if attempt.submission_key == key and attempt.status in unresolved_statuses:
            return DuplicateDecision(
                DuplicateDisposition.RECONCILE_UNVERIFIED_ATTEMPT,
                key,
                "An earlier non-failed attempt exists without a matching stored receipt; reconcile before another click.",
                attempt_id=attempt.attempt_id,
            )

    return DuplicateDecision(
        DuplicateDisposition.SAFE_TO_ATTEMPT,
        key,
        "No confirmed or unresolved prior attempt exists for this exact submission identity.",
    )


def reconcile_receipt(*, attempt: SubmissionAttempt, receipt: SubmissionReceipt) -> SubmissionAttempt:
    if receipt.application_id != attempt.application_id:
        raise ValueError("receipt application_id does not match attempt")
    if receipt.submission_key != attempt.submission_key:
        raise ValueError("receipt submission_key does not match attempt")
    if receipt.form_fingerprint != attempt.form_fingerprint:
        raise ValueError("receipt form_fingerprint does not match attempt")
    if receipt.plan_hash != attempt.plan_hash:
        raise ValueError("receipt plan_hash does not match attempt")
    if receipt.submitted_at < attempt.attempted_at:
        raise ValueError("receipt submitted_at cannot precede attempt")

    return replace(
        attempt,
        status=SubmissionAttemptStatus.RECEIPT_CONFIRMED,
        confirmation_url=receipt.confirmation_url or attempt.confirmation_url,
        error_code=None,
    )
