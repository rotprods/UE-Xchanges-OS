from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

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


def make_field(**overrides):
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


def make_plan(**overrides):
    base = dict(
        plan_id="plan-1",
        application_id="app-1",
        opportunity_id="opp-1",
        canonical_form_url="https://forms.example.org/apply",
        provider="generic_html",
        form_fingerprint="sha256:abc",
        fields=(make_field(),),
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


class FormModelContractTests(unittest.TestCase):
    def test_black_field_never_carries_model_visible_answer(self):
        with self.assertRaisesRegex(ValueError, "BLACK fields must never"):
            make_field(
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

    def test_black_field_must_not_be_agent_editable(self):
        with self.assertRaisesRegex(ValueError, "cannot be editable"):
            make_field(
                field_key="password",
                label="Password",
                answer=None,
                ownership=FieldOwnership.BLACK,
                sensitivity=FieldSensitivity.SECRET,
                editable_by_agent=True,
            )

    def test_unresolved_required_field_blocks_prefill(self):
        unresolved = make_field(
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
        compiled = make_plan(fields=(make_field(), unresolved))
        self.assertEqual(compiled.unresolved_fields, (unresolved,))
        self.assertFalse(compiled.ready_for_prefill)

    def test_plan_requires_canonical_origin_in_allowlist(self):
        with self.assertRaisesRegex(ValueError, "must be allowlisted"):
            make_plan(allowed_origins=("https://other.example.org",))

    def test_plan_expiry_is_timezone_aware_and_strict(self):
        compiled = make_plan()
        self.assertFalse(compiled.is_expired(NOW + timedelta(minutes=59)))
        self.assertTrue(compiled.is_expired(NOW + timedelta(hours=1)))
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            make_plan(created_at=datetime(2026, 9, 1, 15, 0))

    def test_duplicate_field_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(fields=(make_field(), make_field()))

    def test_validation_signature_is_optional_for_research_but_strict_when_present(self):
        unbound = make_plan(validation_signature=None)
        self.assertFalse(unbound.validation_bound)
        bound = make_plan(validation_signature="sha256:" + "a" * 64)
        self.assertTrue(bound.validation_bound)
        with self.assertRaisesRegex(ValueError, "64 lowercase hex"):
            make_plan(validation_signature="sha256:not-a-real-signature")
        with self.assertRaisesRegex(ValueError, "64 lowercase hex"):
            make_plan(validation_signature="sha256:" + "A" * 64)

    def test_failed_attempt_requires_error_code(self):
        with self.assertRaisesRegex(ValueError, "error_code"):
            SubmissionAttempt(
                attempt_id="attempt-1",
                application_id="app-1",
                submission_key="key-1",
                attempted_at=NOW,
                form_fingerprint="fp",
                plan_hash="planhash",
                status=SubmissionAttemptStatus.FAILED,
            )

    def test_receipt_requires_strong_or_captured_confirmation_evidence(self):
        with self.assertRaisesRegex(ValueError, "receipt requires"):
            SubmissionReceipt(
                receipt_id="receipt-1",
                application_id="app-1",
                submission_key="key-1",
                submitted_at=NOW,
                form_fingerprint="fp",
                plan_hash="planhash",
                confirmation_url="https://forms.example.org/thanks",
            )

    def test_receipt_accepts_provider_reference(self):
        receipt = SubmissionReceipt(
            receipt_id="receipt-1",
            application_id="app-1",
            submission_key="key-1",
            submitted_at=NOW,
            form_fingerprint="fp",
            plan_hash="planhash",
            provider_reference="provider-response-123",
        )
        self.assertEqual(receipt.provider_reference, "provider-response-123")

    def test_receipt_accepts_hashed_confirmation_plus_screenshot(self):
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
        self.assertEqual(receipt.screenshot_ref, "drive:receipt.png")


if __name__ == "__main__":
    unittest.main()
