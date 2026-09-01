from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .models import FormExecutionPlan, FormExecutionState, SubmitAuthority
from .receipts import execution_plan_hash, submission_key


MAX_APPROVAL_TTL_SECONDS = 300
MIN_HMAC_KEY_BYTES = 32


class ApprovalAction(str, Enum):
    SUBMIT = "submit"


class ApprovalStatus(str, Enum):
    VALID = "valid"
    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    BINDING_MISMATCH = "binding_mismatch"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class ApprovalClaims:
    token_id: str
    application_id: str
    form_fingerprint: str
    validation_signature: str
    submission_key: str
    plan_hash: str
    approved_by_ref: str
    approved_at: datetime
    expires_at: datetime
    action: ApprovalAction
    nonce: str


@dataclass(frozen=True)
class ApprovalVerification:
    status: ApprovalStatus
    valid: bool
    reason: str
    claims: ApprovalClaims | None = None


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _require_secret(secret: bytes) -> None:
    if not isinstance(secret, bytes) or len(secret) < MIN_HMAC_KEY_BYTES:
        raise ValueError(f"approval signing secret must be at least {MIN_HMAC_KEY_BYTES} bytes")


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _claims_payload(claims: ApprovalClaims) -> dict[str, Any]:
    return {
        "token_id": claims.token_id,
        "application_id": claims.application_id,
        "form_fingerprint": claims.form_fingerprint,
        "validation_signature": claims.validation_signature,
        "submission_key": claims.submission_key,
        "plan_hash": claims.plan_hash,
        "approved_by_ref": claims.approved_by_ref,
        "approved_at": claims.approved_at.isoformat(),
        "expires_at": claims.expires_at.isoformat(),
        "action": claims.action.value,
        "nonce": claims.nonce,
    }


def _encode_claims(claims: ApprovalClaims) -> bytes:
    return json.dumps(_claims_payload(claims), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sign(payload: bytes, secret: bytes) -> str:
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def issue_approval_token(
    *,
    plan: FormExecutionPlan,
    approved_by_ref: str,
    secret: bytes,
    approved_at: datetime,
    ttl_seconds: int = MAX_APPROVAL_TTL_SECONDS,
    nonce: str | None = None,
) -> str:
    """Issue a short-lived capability for one exact, validation-bound submit plan."""
    _require_secret(secret)
    approved_at = _require_aware(approved_at, "approved_at")
    if not approved_by_ref.strip():
        raise ValueError("approved_by_ref must be non-empty")
    if ttl_seconds <= 0 or ttl_seconds > MAX_APPROVAL_TTL_SECONDS:
        raise ValueError(f"ttl_seconds must be between 1 and {MAX_APPROVAL_TTL_SECONDS}")
    if plan.is_expired(approved_at):
        raise ValueError("cannot approve an expired execution plan")
    if plan.state is not FormExecutionState.HUMAN_APPROVED:
        raise ValueError("approval token requires plan state HUMAN_APPROVED")
    if plan.submit_authority is not SubmitAuthority.AGENT_AFTER_APPROVAL:
        raise ValueError("approval token is only valid for AGENT_AFTER_APPROVAL submit authority")
    if plan.unresolved_fields:
        raise ValueError("cannot approve a plan with unresolved fields")
    if not plan.validation_signature:
        raise ValueError("approval token requires a validation-bound execution plan")

    expires_at = approved_at + timedelta(seconds=ttl_seconds)
    if expires_at > plan.expires_at:
        expires_at = plan.expires_at
    token_nonce = nonce or secrets.token_urlsafe(18)
    if not token_nonce.strip():
        raise ValueError("nonce must be non-empty")

    claims = ApprovalClaims(
        token_id=f"approval:{hashlib.sha256(f'{plan.plan_id}|{approved_at.isoformat()}|{token_nonce}'.encode()).hexdigest()}",
        application_id=plan.application_id,
        form_fingerprint=plan.form_fingerprint,
        validation_signature=plan.validation_signature,
        submission_key=submission_key(plan),
        plan_hash=execution_plan_hash(plan),
        approved_by_ref=approved_by_ref,
        approved_at=approved_at,
        expires_at=expires_at,
        action=ApprovalAction.SUBMIT,
        nonce=token_nonce,
    )
    payload = _encode_claims(claims)
    return f"{_b64encode(payload)}.{_sign(payload, secret)}"


def _parse_claims(payload: bytes) -> ApprovalClaims:
    raw = json.loads(payload.decode("utf-8"))
    return ApprovalClaims(
        token_id=str(raw["token_id"]),
        application_id=str(raw["application_id"]),
        form_fingerprint=str(raw["form_fingerprint"]),
        validation_signature=str(raw["validation_signature"]),
        submission_key=str(raw["submission_key"]),
        plan_hash=str(raw["plan_hash"]),
        approved_by_ref=str(raw["approved_by_ref"]),
        approved_at=_require_aware(datetime.fromisoformat(str(raw["approved_at"])), "approved_at"),
        expires_at=_require_aware(datetime.fromisoformat(str(raw["expires_at"])), "expires_at"),
        action=ApprovalAction(str(raw["action"])),
        nonce=str(raw["nonce"]),
    )


def verify_approval_token(
    *,
    token: str,
    plan: FormExecutionPlan,
    secret: bytes,
    now: datetime,
) -> ApprovalVerification:
    """Verify signature, lifetime and exact structure/validation/payload binding."""
    _require_secret(secret)
    now = _require_aware(now, "now")
    try:
        payload_part, signature = token.split(".", 1)
        payload = _b64decode(payload_part)
    except Exception:
        return ApprovalVerification(ApprovalStatus.MALFORMED, False, "Approval token encoding is malformed.")

    expected = _sign(payload, secret)
    if not hmac.compare_digest(signature, expected):
        return ApprovalVerification(ApprovalStatus.INVALID_SIGNATURE, False, "Approval token signature is invalid.")

    try:
        claims = _parse_claims(payload)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return ApprovalVerification(ApprovalStatus.MALFORMED, False, "Approval token claims are malformed.")

    if now < claims.approved_at:
        return ApprovalVerification(ApprovalStatus.NOT_YET_VALID, False, "Approval token is not yet valid.", claims)
    if now >= claims.expires_at:
        return ApprovalVerification(ApprovalStatus.EXPIRED, False, "Approval token has expired.", claims)
    if plan.is_expired(now):
        return ApprovalVerification(ApprovalStatus.EXPIRED, False, "Execution plan has expired.", claims)
    if plan.state is not FormExecutionState.HUMAN_APPROVED:
        return ApprovalVerification(ApprovalStatus.BINDING_MISMATCH, False, "Current plan is no longer HUMAN_APPROVED.", claims)
    if plan.submit_authority is not SubmitAuthority.AGENT_AFTER_APPROVAL:
        return ApprovalVerification(ApprovalStatus.BINDING_MISMATCH, False, "Current plan no longer permits agent submit after approval.", claims)
    if not plan.validation_signature:
        return ApprovalVerification(ApprovalStatus.BINDING_MISMATCH, False, "Current plan is no longer validation-bound.", claims)

    expected_binding = (
        plan.application_id,
        plan.form_fingerprint,
        plan.validation_signature,
        submission_key(plan),
        execution_plan_hash(plan),
        ApprovalAction.SUBMIT,
    )
    actual_binding = (
        claims.application_id,
        claims.form_fingerprint,
        claims.validation_signature,
        claims.submission_key,
        claims.plan_hash,
        claims.action,
    )
    if not hmac.compare_digest("|".join(map(str, actual_binding)), "|".join(map(str, expected_binding))):
        return ApprovalVerification(
            ApprovalStatus.BINDING_MISMATCH,
            False,
            "Approval no longer matches the current application/form/validation/payload/plan.",
            claims,
        )

    return ApprovalVerification(ApprovalStatus.VALID, True, "Approval token is valid for this exact validation-bound submit plan.", claims)
