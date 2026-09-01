import unittest
from datetime import datetime, timezone

from uexchanges.models import GateResult
from uexchanges.runtime_graph import (
    ActionNode,
    ExecutorType,
    GateNode,
    RuntimeGraph,
    classify_executor,
    compile_mass_apply_row,
    merge_runtime_graphs,
    parse_gate_result,
)

NOW = datetime(2026, 9, 1, 17, 45, tzinfo=timezone.utc)


class RuntimeGraphTests(unittest.TestCase):
    def test_executor_partition(self):
        self.assertEqual(
            classify_executor("HUMAN_FINAL_REVIEW_AND_SUBMIT"), ExecutorType.HUMAN
        )
        self.assertEqual(
            classify_executor("PAY_50_EUR_AND_STORE_RECEIPT"), ExecutorType.HUMAN
        )
        self.assertEqual(classify_executor("VERIFY_CURRENT_ROUTE"), ExecutorType.AGENT)
        self.assertEqual(classify_executor("RECOMPUTE_FRONTIER"), ExecutorType.SYSTEM)

    def test_gate_parser_fail_dominates(self):
        self.assertEqual(
            parse_gate_result("PASS_SPANISH BUT HARD_REQUIREMENT_FAIL"),
            GateResult.FAIL,
        )
        self.assertEqual(parse_gate_result("SPAIN_CONFIRMED"), GateResult.PASS)
        self.assertEqual(parse_gate_result("ROUTE_PENDING"), GateResult.UNKNOWN)

    def test_unknown_gate_blocks_action(self):
        graph = RuntimeGraph()
        graph.add_gate(GateNode("g1", "app", "route", GateResult.UNKNOWN))
        graph.add_action(
            ActionNode(
                "a1",
                "app",
                "SUBMIT",
                ExecutorType.HUMAN,
                "Submit",
                "receipt",
                requires=("g1",),
                idempotency_key="k1",
            )
        )
        self.assertEqual(graph.human_frontier(NOW), [])
        graph.gates["g1"] = GateNode("g1", "app", "route", GateResult.PASS)
        self.assertEqual(
            [action.action_id for action in graph.human_frontier(NOW)], ["a1"]
        )

    def test_human_action_cannot_be_claimed_by_agent(self):
        graph = RuntimeGraph(
            gates={"g": GateNode("g", "app", "route", GateResult.PASS)},
            actions={
                "a": ActionNode(
                    "a",
                    "app",
                    "SUBMIT",
                    ExecutorType.HUMAN,
                    "Submit",
                    "receipt",
                    requires=("g",),
                    idempotency_key="idem",
                )
            },
        )
        with self.assertRaises(PermissionError):
            graph.claim("a", executor=ExecutorType.AGENT, now=NOW)

    def test_completion_unlocks_next_action(self):
        graph = RuntimeGraph(
            gates={"g": GateNode("g", "app", "source", GateResult.PASS)}
        )
        graph.add_action(
            ActionNode(
                "a1",
                "app",
                "VERIFY_ROUTE",
                ExecutorType.AGENT,
                "Verify",
                "evidence",
                requires=("g",),
                idempotency_key="k1",
            )
        )
        graph.add_action(
            ActionNode(
                "a2",
                "app",
                "HUMAN_FINAL",
                ExecutorType.HUMAN,
                "Review",
                "approval",
                requires=("a1",),
                idempotency_key="k2",
            )
        )
        self.assertEqual(
            [action.action_id for action in graph.agent_frontier(NOW)], ["a1"]
        )
        graph.complete("a1", executor=ExecutorType.AGENT, now=NOW, evidence_ref="ev1")
        self.assertEqual(
            [action.action_id for action in graph.human_frontier(NOW)], ["a2"]
        )

    def test_idempotent_completion(self):
        graph = RuntimeGraph(
            gates={"g": GateNode("g", "app", "route", GateResult.PASS)}
        )
        graph.add_action(
            ActionNode(
                "a",
                "app",
                "VERIFY",
                ExecutorType.AGENT,
                "Verify",
                "evidence",
                requires=("g",),
                idempotency_key="same",
            )
        )
        first = graph.complete("a", executor=ExecutorType.AGENT, now=NOW)
        second = graph.complete("a", executor=ExecutorType.AGENT, now=NOW)
        self.assertEqual(first.event_id, second.event_id)
        self.assertEqual(len(graph.events), 1)

    def test_compile_human_submit_row(self):
        graph = compile_mass_apply_row(
            {
                "Application ID": "app-1",
                "Opportunity ID": "opp-1",
                "Title": "Example",
                "Provider": "EYP",
                "Deadline": "2026-09-02T23:59:00+02:00",
                "Bucket": "T0_TODAY",
                "Spain Gate": "PASS_SPAIN_CONFIRMED",
                "Role Gate": "PASS_PROFILE_CONFIRMED",
                "Infopack/Form/AI": "PASS_FORM_VERIFIED_AI_ALLOWED",
                "Submit State": "READY",
                "Next Action": "HUMAN_FINAL_REVIEW_AND_SUBMIT",
            }
        )
        frontier = graph.human_frontier(NOW)
        self.assertEqual(len(frontier), 1)
        self.assertEqual(frontier[0].executor, ExecutorType.HUMAN)
        self.assertEqual(frontier[0].priority, 100)

    def test_compile_terminal_row_never_becomes_human_submit(self):
        graph = compile_mass_apply_row(
            {
                "Application ID": "app-2",
                "Opportunity ID": "opp-2",
                "Title": "Closed",
                "Provider": "SALTO",
                "Deadline": "2026-08-31",
                "Bucket": "T0_TODAY",
                "Spain Gate": "SPAIN_CONFIRMED",
                "Role Gate": "HARD_REQUIREMENT_FAIL_CURRENT_CYCLE",
                "Infopack/Form/AI": "SOURCE_VERIFIED",
                "Submit State": "NOT_SUBMITTED_HARD_FAIL",
                "Next Action": "SUBMIT",
            }
        )
        action = next(iter(graph.actions.values()))
        self.assertEqual(action.action_type, "TERMINAL_ARCHIVE")
        self.assertEqual(action.executor, ExecutorType.SYSTEM)
        self.assertEqual(graph.human_frontier(NOW), [])

    def test_merge_rejects_duplicate_action(self):
        row = {
            "Application ID": "app-1",
            "Opportunity ID": "opp-1",
            "Title": "X",
            "Provider": "X",
            "Spain Gate": "PASS",
            "Role Gate": "PASS",
            "Infopack/Form/AI": "PASS",
            "Submit State": "READY",
            "Next Action": "VERIFY",
        }
        first = compile_mass_apply_row(row)
        second = compile_mass_apply_row(row)
        with self.assertRaises(ValueError):
            merge_runtime_graphs([first, second])

    def test_deadline_must_be_aware(self):
        with self.assertRaises(ValueError):
            ActionNode(
                "a",
                "app",
                "VERIFY",
                ExecutorType.AGENT,
                "x",
                "y",
                deadline=datetime(2026, 9, 1),
            )


if __name__ == "__main__":
    unittest.main()
