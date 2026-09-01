from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from ..models import AIPolicy


class FormFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    CONSENT = "consent"
    UNKNOWN = "unknown"


class FieldOwnership(str, Enum):
    GREEN = "green_agent_factual"
    YELLOW = "yellow_agent_assisted_human_review"
    RED = "red_human_confirmation"
    BLACK = "black_secret_or_never_model"
    UNRESOLVED = "unresolved"


class FieldSensitivity(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class AuthRequirement(str, Enum):
    NONE = "none"
    EXISTING_SESSION = "existing_session"
    HUMAN_LOGIN = "human_login"
    HUMAN_MFA = "human_mfa"


class SubmitAuthority(str, Enum):
    HUMAN_ONLY = "human_only"
    AGENT_AFTER_APPROVAL = "agent_after_approval"


class FormExecutionState(str, Enum):
    FORM_CAPTURED = "form_captured"
    FORM_SCHEMA_VERIFIED = "form_schema_verified"
    ANSWER_PACK_RESOLVED = "answer_pack_resolved"
    PREFILL_READY = "prefill_ready"
    PREFILLED = "prefilled"
    VALIDATION_PASS = "validation_pass"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    HUMAN_APPROVED = "human_approved"
    SUBMIT_AUTHORIZED = "submit_authorized"
    SUBMIT_ATTEMPTED = "submit_attempted"
    SUBMISSION_CONFIRMATION_OBSERVED = "submission_confirmation_observed"
    RECEIPT_CAPTURED = "receipt_captured"
    SUBMITTED_CONFIRMED = "submitted_confirmed"
    BLOCKED = "blocked"


class SubmissionAttemptStatus(str, Enum):
    STARTED = "started"
    CONFIRMATION_OBSERVED = "confirmation_observed"
    RECEIPT_CONFIRMED = "receipt_confirmed"
    UNVERIFIED = "unverified"
    FAILED = "failed"


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _require_origin(value: str, name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be an absolute HTTP(S) URL")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


@dataclass(frozen=True)
class FormField:
    field_key: str
    label: str
    field_type: FormFieldType
    required: bool = False
    options: tuple[str, ...] = ()
    maxlength: int | None = None
    answer: Any | None = None
    answer_source: str | None = None
    evidence_ids: tuple[str, ...] = ()
    ownership: FieldOwnership = FieldOwnership.UNRESOLVED
    sensitivity: FieldSensitivity = FieldSensitivity.PRIVATE
    editable_by_agent: bool = False

    def __post_init__(self) -> None:
        if not self.field_key.strip():
            raise ValueError("field_key must be non-empty")
        if not self.label.strip():
            raise ValueError("label must be non-empty")
        if self.maxlength is not None and self.maxlength <= 0:
            raise ValueError("maxlength must be positive when provided")
        if self.ownership is FieldOwnership.BLACK:
            if self.answer is not None:
                raise ValueError("BLACK fields must never carry a model-visible answer")
            if self.editable_by_agent:
                raise ValueError("BLACK fields cannot be editable by the agent")
            if self.sensitivity is not FieldSensitivity.SECRET:
                raise ValueError("BLACK fields must be classified SECRET")
        if self.ownership in {FieldOwnership.RED, FieldOwnership.UNRESOLVED} and self.editable_by_agent:
            raise ValueError("RED/UNRESOLVED fields cannot be agent-editable")
        if self.field_type in {FormFieldType.SELECT, FormFieldType.RADIO} and not self.options:
            raise ValueError("select/radio fields require options")

    @property
    def resolved(self) -> bool:
        if self.ownership in {FieldOwnership.BLACK, FieldOwnership.UNRESOLVED}:
            return False
        if self.required and self.answer is None:
            return False
        return True


@dataclass(frozen=True)
class FormExecutionPlan:
    plan_id: str
    application_id: str
    opportunity_id: str
    canonical_form_url: str
    provider: str
    form_fingerprint: str
    fields: tuple[FormField, ...]
    ai_policy: AIPolicy
    auth_requirement: AuthRequirement
    submit_authority: SubmitAuthority
    allowed_origins: tuple[str, ...]
    created_at: datetime
    expires_at: datetime
    source_version: str
    attachments: tuple[str, ...] = ()
    state: FormExecutionState = FormExecutionState.FORM_SCHEMA_VERIFIED

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.application_id.strip() or not self.opportunity_id.strip():
            raise ValueError("plan_id/application_id/opportunity_id must be non-empty")
        if not self.provider.strip() or not self.form_fingerprint.strip() or not self.source_version.strip():
            raise ValueError("provider/fingerprint/source_version must be non-empty")
        canonical_origin = _require_origin(self.canonical_form_url, "canonical_form_url")
        created = _require_aware(self.created_at, "created_at")
        expires = _require_aware(self.expires_at, "expires_at")
        if expires <= created:
            raise ValueError("expires_at must be after created_at")
        if not self.allowed_origins:
            raise ValueError("allowed_origins must not be empty")
        normalized = tuple(_require_origin(origin, "allowed_origin") for origin in self.allowed_origins)
        if canonical_origin not in normalized:
            raise ValueError("canonical form origin must be allowlisted")
        keys = [field.field_key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("field_key values must be unique within a plan")

    @property
    def unresolved_fields(self) -> tuple[FormField, ...]:
        return tuple(field for field in self.fields if not field.resolved)

    def is_expired(self, now: datetime) -> bool:
        return _require_aware(now, "now") >= self.expires_at

    @property
    def ready_for_prefill(self) -> bool:
        return not self.unresolved_fields and self.state in {
            FormExecutionState.ANSWER_PACK_RESOLVED,
            FormExecutionState.PREFILL_READY,
        }


@dataclass(frozen=True)
class SubmissionAttempt:
    attempt_id: str
    application_id: str
    submission_key: str
    attempted_at: datetime
    form_fingerprint: str
    plan_hash: str
    status: SubmissionAttemptStatus = SubmissionAttemptStatus.STARTED
    confirmation_url: str | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.attempt_id, self.application_id, self.submission_key, self.form_fingerprint, self.plan_hash)):
            raise ValueError("submission attempt identifiers/hashes must be non-empty")
        _require_aware(self.attempted_at, "attempted_at")
        if self.confirmation_url is not None:
            _require_origin(self.confirmation_url, "confirmation_url")
        if self.status is SubmissionAttemptStatus.FAILED and not self.error_code:
            raise ValueError("failed attempts require an error_code")


@dataclass(frozen=True)
class SubmissionReceipt:
    receipt_id: str
    application_id: str
    submission_key: str
    submitted_at: datetime
    form_fingerprint: str
    plan_hash: str
    confirmation_url: str | None = None
    confirmation_text_hash: str | None = None
    screenshot_ref: str | None = None
    provider_reference: str | None = None
    email_receipt_ref: str | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.receipt_id, self.application_id, self.submission_key, self.form_fingerprint, self.plan_hash)):
            raise ValueError("receipt identifiers/hashes must be non-empty")
        _require_aware(self.submitted_at, "submitted_at")
        if self.confirmation_url is not None:
            _require_origin(self.confirmation_url, "confirmation_url")
        strong_ref = bool(self.provider_reference or self.email_receipt_ref)
        captured_confirmation = bool(self.confirmation_text_hash and self.screenshot_ref)
        if not (strong_ref or captured_confirmation):
            raise ValueError(
                "receipt requires provider/email reference or confirmation-text hash + screenshot reference"
            )
