from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from uexchanges.forms import (
    AuthRequirement,
    FieldOwnership,
    FieldSensitivity,
    FormExecutionPlan,
    FormExecutionState,
    FormField,
    FormFieldType,
    SubmissionAttempt,
    SubmissionAttemptStatus,
    SubmissionReceipt,
    SubmitAuthority,
)
from uexchanges.models import AIPolicy


NOW = datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)


def field(**overrides):
    base = dict(
        field_key="email",
        label="Email",
        field_type=FormFieldType.EMAIL,
        required=True,
        answer="candidate@example.com",
        answer_source="profile:email",
        evidence_ids=("ev-email",),
        ownership=FieldOwnership.GREEN,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=True,
    )
    base.update(overrides)
    return FormField(**base)


def plan(**overrides):
    base = dict(
        plan_id="plan-1",
        application_id="app-1",
        opportunity_id="opp-1",
        canonical_form_url="https://forms.example.org/apply",
        provider="generic_html",
        form_fingerprint="sha256:abc",
        fields=(field(),),
        ai_policy=AIPolicy.ASSIST_ONLY,
        auth_requirement=AuthRequirement.EXISTING_SESSION,
        submit_authority=SubmitAuthority.HUMAN_ONLY,
        allowed_origins=("https://forms.example.org",),
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        source_version="source-v1",
        state=FormExecutionState.ANSWER_PACK_RESOLVED,
    )
    base.update(overrides)
    return FormExecutionPlan(**base)


def test_black_field_never_carries_model_visible_answer():
    with pytest.raises(ValueError, match="BLACK fields must never"):
        field(
            field_key="otp",
            label="OTP",
            field_type=FormFieldType.TEXT,
            answer="123456",
            answer_source=None,
            evidence_ids=(),
            ownership=FieldOwnership.BLACK,
            sensitivity=FieldSensitivity.SECRET,
            editable_by_agent=False,
        )


def test_black_field_must_be_secret_and_not_agent_editable():
    with pytest.raises(ValueError, match="cannot be editable"):
        field(
            field_key="password",
            label="Password",
            answer=None,
            ownership=FieldOwnership.BLACK,
            sensitivity=FieldSensitivity.SECRET,
            editable_by_agent=True,
        )


def test_unresolved_required_field_blocks_prefill():
    unresolved = field(
        field_key="availability",
        label="Can you attend all dates?",
        field_type=FormFieldType.CONSENT,
        answer=None,
        answer_source=None,
        evidence_ids=(),
        ownership=FieldOwnership.UNRESOLVED,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=False,
    )
    compiled = plan(fields=(field(), unresolved))
    assert compiled.unresolved_fields == (unresolved,)
    assert compiled.ready_for_prefill is False


def test_plan_requires_canonical_origin_in_allowlist():
    with pytest.raises(ValueError, match="must be allowlisted"):
        plan(allowed_origins=("https://other.example.org",))


def test_plan_expiry_is_timezone_aware_and_strict():
    compiled = plan()
    assert compiled.is_expired(NOW + timedelta(minutes=59)) is False
    assert compiled.is_expired(NOW + timedelta(hours=1)) is True
    with pytest.raises(ValueError, match="timezone-aware"):
        plan(created_at=datetime(2026, 9, 1, 15, 0))


def test_duplicate_field_keys_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        plan(fields=(field(), field()))


def test_failed_attempt_requires_error_code():
    with pytest.raises(ValueError, match="error_code"):
        SubmissionAttempt(
            attempt_id="attempt-1",
            application_id="app-1",
            submission_key="key-1",
            attempted_at=NOW,
            form_fingerprint="fp",
            plan_hash="planhash",
            status=SubmissionAttemptStatus.FAILED,
        )


def test_receipt_requires_strong_or_captured_confirmation_evidence():
    with pytest.raises(ValueError, match="receipt requires"):
        SubmissionReceipt(
            receipt_id="receipt-1",
            application_id="app-1",
            submission_key="key-1",
            submitted_at=NOW,
            form_fingerprint="fp",
            plan_hash="planhash",
            confirmation_url="https://forms.example.org/thanks",
        )


def test_receipt_accepts_provider_reference():
    receipt = SubmissionReceipt(
        receipt_id="receipt-1",
        application_id="app-1",
        submission_key="key-1",
        submitted_at=NOW,
        form_fingerprint="fp",
        plan_hash="planhash",
        provider_reference="provider-response-123",
    )
    assert receipt.provider_reference == "provider-response-123"


def test_receipt_accepts_hashed_confirmation_plus_screenshot():
    receipt = SubmissionReceipt(
        receipt_id="receipt-2",
        application_id="app-1",
        submission_key="key-1",
        submitted_at=NOW,
        form_fingerprint="fp",
        plan_hash="planhash",
        confirmation_text_hash="sha256:confirmation",
        screenshot_ref="drive:receipt.png",
    )
    assert receipt.screenshot_ref == "drive:receipt.png"
