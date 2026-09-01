import unittest
from datetime import datetime, timezone

from uexchanges.models import GateResult
from uexchanges.runtime_compiler import compile_mass_apply_row_atomic
from uexchanges.runtime_graph import ExecutorType

NOW = datetime(2026, 9, 1, 16, 30, tzinfo=timezone.utc)


class RuntimeDeadlineTests(unittest.TestCase):
    def row(self, **overrides):
        base = {
            "Queue ID": "MAQ-X",
            "Application ID": "app-x",
            "Opportunity ID": "opp-x",
            "Title": "Example",
            "Provider": "TEST",
            "Role": "participant",
            "Deadline": "2026-08-31T23:59:00+02:00",
            "Bucket": "T1_2_3_DAYS",
            "Spain Gate": "SPAIN_CONFIRMED",
            "Role Gate": "PASS_PROFILE_CONFIRMED",
            "Infopack/Form/AI": "FORM_VERIFIED | AI_ALLOWED",
            "Submit State": "HUMAN_NOW",
            "Next Action": "HUMAN_FINAL_SUBMIT_STORE_RECEIPT",
        }
        base.update(overrides)
        return base

    def test_expired_deadline_replaces_human_submit_with_agent_verification(self):
        graph = compile_mass_apply_row_atomic(self.row(), now=NOW)
        deadline_gate = graph.gates["gate:app-x:deadline"]
        self.assertEqual(deadline_gate.result, GateResult.FAIL)
        self.assertEqual(graph.human_frontier(NOW), [])
        agent = graph.agent_frontier(NOW)
        self.assertEqual(len(agent), 1)
        self.assertEqual(agent[0].action_type, "VERIFY_DEADLINE_EXTENSION_OR_ARCHIVE")

    def test_authorised_late_route_keeps_submission_chain(self):
        graph = compile_mass_apply_row_atomic(
            self.row(
                **{
                    "Role Gate": "PASS_PARTICIPANT; HOST_AUTHORISED_LATE_APPLICATION",
                    "Infopack/Form/AI": "PUBLIC_FORM | LATE_ROUTE_AUTHORISED | AI_ALLOWED",
                    "Submit State": "READY_PENDING_HUMAN_FORM_COMPLETION",
                    "Next Action": "CAPTURE_FORM_QUESTIONS_COMPLETE_HUMAN_FINAL_SUBMIT_STORE_RECEIPT",
                }
            ),
            now=NOW,
        )
        self.assertEqual(graph.gates["gate:app-x:deadline"].result, GateResult.PASS)
        self.assertEqual(len(graph.agent_frontier(NOW)), 1)
        self.assertEqual(graph.agent_frontier(NOW)[0].action_type, "CAPTURE_FORM_QUESTIONS")

    def test_selected_payment_route_overrides_old_deadline(self):
        graph = compile_mass_apply_row_atomic(
            self.row(
                **{
                    "Bucket": "T0_SELECTED_HUMAN_CONFIRMATION",
                    "Role Gate": "SELECTED_BY_SENDING_ORG PASS",
                    "Submit State": "SELECTED_NOT_CONFIRMED",
                    "Next Action": "HUMAN_PAY_30_CAPTURE_RECEIPT",
                }
            ),
            now=NOW,
        )
        self.assertEqual(graph.gates["gate:app-x:deadline"].result, GateResult.PASS)
        human = graph.human_frontier(NOW)
        self.assertEqual(len(human), 1)
        self.assertEqual(human[0].executor, ExecutorType.HUMAN)

    def test_unknown_deadline_blocks_irreversible_action_behind_agent_verification(self):
        graph = compile_mass_apply_row_atomic(
            self.row(Deadline="ROLLING", Next_Action="unused") if False else self.row(**{
                "Deadline": "ROLLING",
                "Next Action": "HUMAN_FINAL_SUBMIT_STORE_RECEIPT",
            }),
            now=NOW,
        )
        self.assertEqual(graph.gates["gate:app-x:deadline"].result, GateResult.UNKNOWN)
        self.assertEqual(graph.human_frontier(NOW), [])
        agent = graph.agent_frontier(NOW)
        self.assertEqual(agent[0].action_type, "VERIFY_EXACT_DEADLINE_OR_LATE_ROUTE")


if __name__ == "__main__":
    unittest.main()
