from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.forms import (
    AuthRequirement,
    DuplicateDisposition,
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
    answer_pack_hash,
    build_submission_attempt,
    evaluate_duplicate_guard,
    execution_plan_hash,
    reconcile_receipt,
    submission_key,
)
from uexchanges.models import AIPolicy


NOW = datetime(2026, 9, 1, 16, 15, tzinfo=timezone.utc)


def make_field(*, answer="Roberto", evidence_ids=("ev-name",)) -> FormField:
    return FormField(
        field_key="name",
        label="Name",
        field_type=FormFieldType.TEXT,
        required=True,
        answer=answer,
        answer_source="profile:name",
        evidence_ids=evidence_ids,
        ownership=FieldOwnership.GREEN,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=True,
    )


def make_plan(**overrides) -> FormExecutionPlan:
    base = dict(
        plan_id="plan-1",
        application_id="app-1",
        opportunity_id="opp-1",
        canonical_form_url="https://forms.example.org/apply",
        provider="generic_html",
        form_fingerprint="sha256:form-v1",
        fields=(make_field(),),
        ai_policy=AIPolicy.ASSIST_ONLY,
        auth_requirement=AuthRequirement.EXISTING_SESSION,
        submit_authority=SubmitAuthority.HUMAN_ONLY,
        allowed_origins=("https://forms.example.org",),
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        source_version="source-v1",
        attachments=("drive:cv-v1",),
        state=FormExecutionState.HUMAN_APPROVED,
    )
    base.update(overrides)
    return FormExecutionPlan(**base)


def make_receipt(*, plan: FormExecutionPlan, receipt_id="receipt-1", submitted_at=None) -> SubmissionReceipt:
    return SubmissionReceipt(
        receipt_id=receipt_id,
        application_id=plan.application_id,
        submission_key=submission_key(plan),
        submitted_at=submitted_at or (NOW + timedelta(seconds=10)),
        form_fingerprint=plan.form_fingerprint,
        plan_hash=execution_plan_hash(plan),
        provider_reference="provider-ref-123",
    )


class FormReceiptTests(unittest.TestCase):
    def test_submission_key_ignores_plan_timestamps_but_tracks_payload(self):
        first = make_plan()
        second = make_plan(
            plan_id="plan-2",
            created_at=NOW + timedelta(minutes=5),
            expires_at=NOW + timedelta(hours=2),
        )
        self.assertEqual(answer_pack_hash(first), answer_pack_hash(second))
        self.assertEqual(submission_key(first), submission_key(second))
        self.assertNotEqual(execution_plan_hash(first), execution_plan_hash(second))

    def test_submission_key_changes_when_answer_changes(self):
        first = make_plan()
        changed = make_plan(fields=(make_field(answer="Another value"),))
        self.assertNotEqual(answer_pack_hash(first), answer_pack_hash(changed))
        self.assertNotEqual(submission_key(first), submission_key(changed))

    def test_submission_key_changes_when_form_fingerprint_changes(self):
        first = make_plan()
        changed = make_plan(form_fingerprint="sha256:form-v2")
        self.assertEqual(answer_pack_hash(first), answer_pack_hash(changed))
        self.assertNotEqual(submission_key(first), submission_key(changed))

    def test_execution_plan_hash_tracks_evidence_even_when_submission_payload_same(self):
        first = make_plan()
        changed_evidence = make_plan(fields=(make_field(evidence_ids=("ev-name-new",)),))
        self.assertEqual(submission_key(first), submission_key(changed_evidence))
        self.assertNotEqual(execution_plan_hash(first), execution_plan_hash(changed_evidence))

    def test_confirmed_matching_receipt_blocks_duplicate(self):
        plan = make_plan()
        decision = evaluate_duplicate_guard(plan=plan, receipts=(make_receipt(plan=plan),))
        self.assertIs(decision.disposition, DuplicateDisposition.BLOCK_CONFIRMED_DUPLICATE)
        self.assertEqual(decision.receipt_id, "receipt-1")

    def test_prior_started_attempt_requires_reconciliation(self):
        plan = make_plan()
        attempt = build_submission_attempt(plan=plan, attempt_id="attempt-1", attempted_at=NOW)
        decision = evaluate_duplicate_guard(plan=plan, attempts=(attempt,))
        self.assertIs(decision.disposition, DuplicateDisposition.RECONCILE_UNVERIFIED_ATTEMPT)
        self.assertEqual(decision.attempt_id, "attempt-1")

    def test_failed_attempt_allows_retry(self):
        plan = make_plan()
        failed = SubmissionAttempt(
            attempt_id="attempt-failed",
            application_id=plan.application_id,
            submission_key=submission_key(plan),
            attempted_at=NOW,
            form_fingerprint=plan.form_fingerprint,
            plan_hash=execution_plan_hash(plan),
            status=SubmissionAttemptStatus.FAILED,
            error_code="network_before_submit",
        )
        decision = evaluate_duplicate_guard(plan=plan, attempts=(failed,))
        self.assertIs(decision.disposition, DuplicateDisposition.SAFE_TO_ATTEMPT)

    def test_different_payload_attempt_does_not_block_current_payload(self):
        current = make_plan()
        old_plan = make_plan(fields=(make_field(answer="Old answer"),))
        old_attempt = build_submission_attempt(plan=old_plan, attempt_id="attempt-old", attempted_at=NOW)
        decision = evaluate_duplicate_guard(plan=current, attempts=(old_attempt,))
        self.assertIs(decision.disposition, DuplicateDisposition.SAFE_TO_ATTEMPT)

    def test_reconcile_receipt_requires_exact_identity(self):
        plan = make_plan()
        attempt = build_submission_attempt(plan=plan, attempt_id="attempt-1", attempted_at=NOW)
        receipt = make_receipt(plan=plan)
        reconciled = reconcile_receipt(attempt=attempt, receipt=receipt)
        self.assertIs(reconciled.status, SubmissionAttemptStatus.RECEIPT_CONFIRMED)

        wrong_app = SubmissionReceipt(
            receipt_id="receipt-wrong-app",
            application_id="other-app",
            submission_key=receipt.submission_key,
            submitted_at=receipt.submitted_at,
            form_fingerprint=receipt.form_fingerprint,
            plan_hash=receipt.plan_hash,
            provider_reference="provider-ref",
        )
        with self.assertRaisesRegex(ValueError, "application_id"):
            reconcile_receipt(attempt=attempt, receipt=wrong_app)

        wrong_key = SubmissionReceipt(
            receipt_id="receipt-wrong-key",
            application_id=receipt.application_id,
            submission_key="sha256:wrong",
            submitted_at=receipt.submitted_at,
            form_fingerprint=receipt.form_fingerprint,
            plan_hash=receipt.plan_hash,
            provider_reference="provider-ref",
        )
        with self.assertRaisesRegex(ValueError, "submission_key"):
            reconcile_receipt(attempt=attempt, receipt=wrong_key)

        wrong_fp = SubmissionReceipt(
            receipt_id="receipt-wrong-fp",
            application_id=receipt.application_id,
            submission_key=receipt.submission_key,
            submitted_at=receipt.submitted_at,
            form_fingerprint="sha256:other-form",
            plan_hash=receipt.plan_hash,
            provider_reference="provider-ref",
        )
        with self.assertRaisesRegex(ValueError, "form_fingerprint"):
            reconcile_receipt(attempt=attempt, receipt=wrong_fp)

        wrong_plan_hash = SubmissionReceipt(
            receipt_id="receipt-wrong-plan",
            application_id=receipt.application_id,
            submission_key=receipt.submission_key,
            submitted_at=receipt.submitted_at,
            form_fingerprint=receipt.form_fingerprint,
            plan_hash="sha256:other-plan",
            provider_reference="provider-ref",
        )
        with self.assertRaisesRegex(ValueError, "plan_hash"):
            reconcile_receipt(attempt=attempt, receipt=wrong_plan_hash)

    def test_receipt_cannot_precede_attempt(self):
        plan = make_plan()
        attempt = build_submission_attempt(plan=plan, attempt_id="attempt-1", attempted_at=NOW)
        receipt = make_receipt(plan=plan, submitted_at=NOW - timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "cannot precede"):
            reconcile_receipt(attempt=attempt, receipt=receipt)


if __name__ == "__main__":
    unittest.main()
