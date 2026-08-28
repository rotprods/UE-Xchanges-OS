import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.execution import (
    CommunicationState,
    ExecutionAction,
    SubmissionState,
    evaluate_communication,
    evaluate_execution_gate,
    resolve_submission_state,
)
from uexchanges.models import AIPolicy, GateResult


UTC = timezone.utc
NOW = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


class CommunicationExecutionTests(unittest.TestCase):
    def test_wait_inside_reply_sla(self):
        decision = evaluate_communication(sent_at=NOW - timedelta(hours=2), now=NOW)
        self.assertEqual(decision.state, CommunicationState.SENT_WAITING)
        self.assertEqual(decision.action, ExecutionAction.WAIT_REPLY)

    def test_follow_up_after_sla(self):
        decision = evaluate_communication(sent_at=NOW - timedelta(hours=25), now=NOW)
        self.assertEqual(decision.state, CommunicationState.FOLLOW_UP_DUE)
        self.assertEqual(decision.action, ExecutionAction.FOLLOW_UP)

    def test_deadline_critical_escalates_without_duplicate_guessing(self):
        decision = evaluate_communication(
            sent_at=NOW - timedelta(hours=2),
            now=NOW,
            deadline=NOW + timedelta(hours=3),
        )
        self.assertEqual(decision.state, CommunicationState.DEADLINE_CRITICAL_NO_REPLY)
        self.assertEqual(decision.action, ExecutionAction.ESCALATE_DIRECT_ROUTE)

    def test_reply_routes_to_ingestion(self):
        decision = evaluate_communication(sent_at=NOW, now=NOW, reply_received=True)
        self.assertEqual(decision.action, ExecutionAction.INGEST_REPLY)

    def test_bounce_routes_to_contact_resolution(self):
        decision = evaluate_communication(sent_at=NOW, now=NOW, bounced=True)
        self.assertEqual(decision.action, ExecutionAction.RESOLVE_CONTACT_ROUTE)

    def test_deadline_passed_no_reply_is_not_rejection(self):
        decision = evaluate_communication(
            sent_at=NOW - timedelta(days=2),
            now=NOW,
            deadline=NOW - timedelta(minutes=1),
        )
        self.assertEqual(decision.state, CommunicationState.DEADLINE_PASSED_NO_REPLY)
        self.assertEqual(decision.action, ExecutionAction.NO_ACTION)
        self.assertIn("not a rejection", decision.reason)

    def test_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_communication(sent_at=datetime(2026, 8, 28), now=NOW)


class SubmissionResolutionTests(unittest.TestCase):
    def test_receipt_confirms_submission(self):
        decision = resolve_submission_state(
            deadline=NOW + timedelta(hours=1),
            now=NOW,
            receipt_ref="receipt-123",
        )
        self.assertEqual(decision.state, SubmissionState.SUBMITTED_CONFIRMED)
        self.assertEqual(decision.action, ExecutionAction.RECORD_SUBMITTED)

    def test_applicant_confirmation_without_receipt_stays_unverified(self):
        decision = resolve_submission_state(
            deadline=NOW - timedelta(hours=1),
            now=NOW,
            applicant_confirms_submitted=True,
        )
        self.assertEqual(decision.state, SubmissionState.SUBMITTED_UNVERIFIED)
        self.assertEqual(decision.action, ExecutionAction.VERIFY_RECEIPT)

    def test_deadline_passed_without_evidence_preserves_ambiguity(self):
        decision = resolve_submission_state(deadline=NOW - timedelta(minutes=1), now=NOW)
        self.assertEqual(decision.state, SubmissionState.DEADLINE_PASSED_RECEIPT_UNKNOWN)
        self.assertEqual(decision.action, ExecutionAction.VERIFY_RECEIPT)

    def test_explicit_non_submission_is_required_to_close(self):
        decision = resolve_submission_state(
            deadline=NOW - timedelta(hours=1),
            now=NOW,
            explicit_not_submitted=True,
        )
        self.assertEqual(decision.state, SubmissionState.CLOSED_NOT_SUBMITTED)

    def test_conflicting_submission_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_submission_state(
                deadline=NOW,
                now=NOW,
                receipt_ref="receipt",
                explicit_not_submitted=True,
            )


class ApplicationExecutionGateTests(unittest.TestCase):
    def base(self, **changes):
        args = dict(
            eligibility=GateResult.PASS,
            ai_policy=AIPolicy.ALLOWED,
            private_gates_resolved=True,
            form_captured=True,
            mandatory_assets_ready=True,
            human_review_complete=True,
            human_owned_final_text=True,
            now=NOW,
            deadline=NOW + timedelta(days=2),
        )
        args.update(changes)
        return evaluate_execution_gate(**args)

    def test_unknown_eligibility_routes_to_verification(self):
        decision = self.base(eligibility=GateResult.UNKNOWN)
        self.assertEqual(decision.action, ExecutionAction.VERIFY_ELIGIBILITY)

    def test_unknown_ai_policy_blocks_final_execution(self):
        decision = self.base(ai_policy=AIPolicy.UNKNOWN)
        self.assertEqual(decision.action, ExecutionAction.RESOLVE_AI_POLICY)
        self.assertFalse(decision.ready_to_submit)

    def test_ai_prohibition_requires_human_owned_text(self):
        decision = self.base(
            ai_policy=AIPolicy.FINAL_TEXT_PROHIBITED,
            human_owned_final_text=False,
        )
        self.assertEqual(decision.action, ExecutionAction.HUMAN_WRITE_REQUIRED)

    def test_all_gates_pass_routes_to_submit(self):
        decision = self.base()
        self.assertEqual(decision.action, ExecutionAction.SUBMIT)
        self.assertTrue(decision.ready_to_submit)

    def test_deadline_passed_routes_to_receipt_resolution(self):
        decision = self.base(deadline=NOW - timedelta(seconds=1))
        self.assertEqual(decision.action, ExecutionAction.VERIFY_RECEIPT)
        self.assertFalse(decision.ready_to_submit)


if __name__ == "__main__":
    unittest.main()
