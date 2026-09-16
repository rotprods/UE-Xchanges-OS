import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.execution import (
    ApplicationRoute,
    CommunicationState,
    ExecutionAction,
    SubmissionState,
    decide_application_route,
    evaluate_communication,
    evaluate_execution_gate,
    evaluate_outbound_preflight,
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

    def test_default_does_not_chase_after_one_day(self):
        decision = evaluate_communication(sent_at=NOW - timedelta(hours=25), now=NOW)
        self.assertEqual(decision.state, CommunicationState.SENT_WAITING)
        self.assertEqual(decision.action, ExecutionAction.WAIT_REPLY)

    def test_follow_up_after_five_day_sla(self):
        decision = evaluate_communication(sent_at=NOW - timedelta(hours=121), now=NOW)
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


class ApplicationRouteTests(unittest.TestCase):
    def test_email_authorized_skips_route_query(self):
        decision = decide_application_route(email_candidature_authorized=True)
        self.assertEqual(decision.route, ApplicationRoute.EMAIL)
        self.assertEqual(decision.action, ExecutionAction.SEND_EMAIL_CANDIDATURE)

    def test_required_form_is_not_replaced_by_email(self):
        decision = decide_application_route(form_required=True)
        self.assertEqual(decision.route, ApplicationRoute.FORM)
        self.assertEqual(decision.action, ExecutionAction.COMPLETE_FORM)

    def test_both_routes_without_order_stay_unresolved(self):
        decision = decide_application_route(form_required=True, email_required=True)
        self.assertEqual(decision.route, ApplicationRoute.UNKNOWN)
        self.assertEqual(decision.action, ExecutionAction.RESOLVE_CONTACT_ROUTE)

    def test_explicit_email_then_form_order(self):
        decision = decide_application_route(
            form_required=True,
            email_required=True,
            explicit_order="email_then_form",
        )
        self.assertEqual(decision.route, ApplicationRoute.EMAIL_THEN_FORM)
        self.assertEqual(decision.action, ExecutionAction.SEND_EMAIL_CANDIDATURE)


class OutboundPreflightTests(unittest.TestCase):
    def test_duplicate_initial_contact_blocks_send(self):
        decision = evaluate_outbound_preflight(duplicate_initial_contact=True)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, ExecutionAction.BLOCK_DUPLICATE_OUTREACH)

    def test_unknown_previous_send_blocks_retry(self):
        decision = evaluate_outbound_preflight(unknown_previous_send_outcome=True)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, ExecutionAction.RECONCILE_OUTBOUND_EFFECT)

    def test_signature_must_appear_exactly_once(self):
        for count in (0, 2):
            with self.subTest(count=count):
                decision = evaluate_outbound_preflight(signature_count=count)
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.action, ExecutionAction.FIX_SIGNATURE)

    def test_repeated_questions_and_internal_jargon_block(self):
        decision = evaluate_outbound_preflight(
            asks_already_answered_questions=True,
            contains_internal_process_jargon=True,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, ExecutionAction.HUMAN_REVIEW)

    def test_assist_only_requires_applicant_owned_text(self):
        decision = evaluate_outbound_preflight(
            ai_policy=AIPolicy.ASSIST_ONLY,
            applicant_owned_text=False,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, ExecutionAction.HUMAN_REVIEW)

    def test_clean_candidature_passes(self):
        decision = evaluate_outbound_preflight(
            signature_count=1,
            unresolved_blocking_questions=0,
            ai_policy=AIPolicy.UNKNOWN,
            applicant_owned_text=True,
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, ExecutionAction.SEND_EMAIL_CANDIDATURE)


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
            form_required=True,
        )
        args.update(changes)
        return evaluate_execution_gate(**args)

    def test_unknown_eligibility_routes_to_verification(self):
        decision = self.base(eligibility=GateResult.UNKNOWN)
        self.assertEqual(decision.action, ExecutionAction.VERIFY_ELIGIBILITY)

    def test_unknown_ai_policy_blocks_generated_final_text(self):
        decision = self.base(ai_policy=AIPolicy.UNKNOWN, human_owned_final_text=False)
        self.assertEqual(decision.action, ExecutionAction.RESOLVE_AI_POLICY)
        self.assertFalse(decision.ready_to_submit)

    def test_unknown_ai_policy_does_not_force_organiser_query_for_applicant_owned_text(self):
        decision = self.base(ai_policy=AIPolicy.UNKNOWN, human_owned_final_text=True)
        self.assertEqual(decision.action, ExecutionAction.SUBMIT)
        self.assertTrue(decision.ready_to_submit)

    def test_assist_only_requires_human_owned_text(self):
        decision = self.base(
            ai_policy=AIPolicy.ASSIST_ONLY,
            human_owned_final_text=False,
        )
        self.assertEqual(decision.action, ExecutionAction.HUMAN_WRITE_REQUIRED)

    def test_ai_prohibition_requires_human_owned_text(self):
        decision = self.base(
            ai_policy=AIPolicy.FINAL_TEXT_PROHIBITED,
            human_owned_final_text=False,
        )
        self.assertEqual(decision.action, ExecutionAction.HUMAN_WRITE_REQUIRED)

    def test_email_only_route_does_not_require_form_capture(self):
        decision = self.base(form_required=False, form_captured=False)
        self.assertEqual(decision.action, ExecutionAction.SUBMIT)
        self.assertTrue(decision.ready_to_submit)

    def test_form_route_requires_complete_capture(self):
        decision = self.base(form_required=True, form_captured=False)
        self.assertEqual(decision.action, ExecutionAction.CAPTURE_FORM)
        self.assertFalse(decision.ready_to_submit)

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
