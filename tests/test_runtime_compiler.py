import unittest
from datetime import datetime, timezone

from uexchanges.runtime_compiler import (
    compile_mass_apply_row_atomic,
    decompose_next_action,
    parse_live_gate_result,
)
from uexchanges.runtime_graph import ExecutorType
from uexchanges.runtime_projection import atomic_edges, snapshot_atomic
from uexchanges.models import GateResult

NOW = datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc)


class AtomicRuntimeCompilerTests(unittest.TestCase):
    def base_row(self, **overrides):
        row = {
            "Queue ID": "MAQ-X",
            "Application ID": "app-x",
            "Opportunity ID": "opp-x",
            "Title": "Example",
            "Provider": "TEST",
            "Role": "participant",
            "Deadline": "2026-09-02T23:59:00+02:00",
            "Bucket": "T0_TODAY",
            "Spain Gate": "SPAIN_CONFIRMED",
            "Role Gate": "PASS_PROFILE_CONFIRMED",
            "Infopack/Form/AI": "FORM_VERIFIED | AI_ALLOWED",
            "Submit State": "HUMAN_NOW",
            "Next Action": "OPEN_EXTERNAL_FORM_COMPLETE_AUTHENTIC_FINAL_SUBMIT_STORE_RECEIPT",
        }
        row.update(overrides)
        return row

    def test_external_form_becomes_agent_then_human(self):
        graph = compile_mass_apply_row_atomic(self.base_row())
        ordered = sorted(graph.actions.values(), key=lambda a: a.metadata["ordinal"])
        self.assertEqual(len(ordered), 2)
        self.assertEqual(ordered[0].executor, ExecutorType.AGENT)
        self.assertEqual(ordered[1].executor, ExecutorType.HUMAN)
        self.assertEqual(ordered[1].requires[0], ordered[0].action_id)
        self.assertEqual([a.action_id for a in graph.agent_frontier(NOW)], [ordered[0].action_id])
        self.assertEqual(graph.human_frontier(NOW), [])

    def test_tcanet_chain_is_human_agent_human(self):
        graph = compile_mass_apply_row_atomic(
            self.base_row(Next_Action="unused") if False else self.base_row(**{
                "Next Action": "CREATE_TCANET_ACCOUNT_CAPTURE_FORM_PERSONALLY_COMPLETE_SUBMIT_STORE_RECEIPT",
            })
        )
        ordered = sorted(graph.actions.values(), key=lambda a: a.metadata["ordinal"])
        self.assertEqual([a.executor for a in ordered], [ExecutorType.HUMAN, ExecutorType.AGENT, ExecutorType.HUMAN])
        self.assertEqual(len(graph.human_frontier(NOW)), 1)
        self.assertEqual(graph.human_frontier(NOW)[0].action_type, "CREATE_TCANET_ACCOUNT")

    def test_eyp_chain_includes_route_reconciliation(self):
        graph = compile_mass_apply_row_atomic(self.base_row(**{
            "Next Action": "CREATE_EYP_ESC_ACCOUNT_OPEN_53846_INGEST_YUPI_REPLY_FINALISE_ASSETS_SUBMIT_CURRENT_ROUTE_STORE_RECEIPT",
        }))
        ordered = sorted(graph.actions.values(), key=lambda a: a.metadata["ordinal"])
        self.assertEqual(len(ordered), 3)
        self.assertEqual([a.executor for a in ordered], [ExecutorType.HUMAN, ExecutorType.AGENT, ExecutorType.HUMAN])
        self.assertIn("VERIFY_CURRENT_ROUTE", ordered[1].action_type)

    def test_work_authorisation_verification_is_not_misclassified_as_login(self):
        graph = compile_mass_apply_row_atomic(self.base_row(**{
            "Infopack/Form/AI": "AI_UNKNOWN",
            "Next Action": "VERIFY_WORK_AUTH_PROFILE_EVIDENCE_CAPTURE_FORM_AI_POLICY_THEN_PREPARE",
        }))
        ordered = sorted(graph.actions.values(), key=lambda a: a.metadata["ordinal"])
        self.assertTrue(all(a.executor is ExecutorType.AGENT for a in ordered))
        self.assertEqual(len(graph.agent_frontier(NOW)), 1)

    def test_payment_waits_for_agent_ingest_first(self):
        graph = compile_mass_apply_row_atomic(self.base_row(**{
            "Infopack/Form/AI": "NO_FORM_REQUIRED | AI_UNKNOWN",
            "Next Action": "INGEST_PAYMENT_DETAILS_THEN_HUMAN_APPROVE_OR_DECLINE_TRANSFER",
            "Submit State": "WAITING_HUMAN_PAYMENT_GATE",
        }))
        ordered = sorted(graph.actions.values(), key=lambda a: a.metadata["ordinal"])
        self.assertEqual([a.executor for a in ordered], [ExecutorType.AGENT, ExecutorType.HUMAN])
        self.assertEqual(len(graph.agent_frontier(NOW)), 1)
        self.assertEqual(graph.human_frontier(NOW), [])

    def test_terminal_has_only_system_archive(self):
        graph = compile_mass_apply_row_atomic(self.base_row(**{
            "Submit State": "NOT_SUBMITTED_HARD_FAIL",
            "Role Gate": "HARD_REQUIREMENT_FAIL_CURRENT_CYCLE",
            "Next Action": "SUBMIT",
        }))
        self.assertEqual(len(graph.actions), 1)
        action = next(iter(graph.actions.values()))
        self.assertEqual(action.executor, ExecutorType.SYSTEM)
        self.assertEqual(action.action_type, "TERMINAL_ARCHIVE")

    def test_live_gate_parser_conservative_conflict(self):
        self.assertEqual(parse_live_gate_result("CURRENT_EYP_VERIFIED | STALE_CONFLICT | AI_ASSIST_ONLY", kind="form"), GateResult.UNKNOWN)
        self.assertEqual(parse_live_gate_result("LIVE_FORM | AI_ALLOWED", kind="form"), GateResult.PASS)
        self.assertEqual(parse_live_gate_result("SPAIN_LISTED", kind="spain"), GateResult.PASS)

    def test_atomic_edges_contain_precedes_and_one_current_pointer(self):
        graph = compile_mass_apply_row_atomic(self.base_row())
        edges = atomic_edges(graph)
        rels = [edge["type"] for edge in edges]
        self.assertIn("PRECEDES", rels)
        self.assertEqual(rels.count("HAS_NEXT_ACTION"), 1)

    def test_atomic_snapshot_counts_application_once(self):
        graph = compile_mass_apply_row_atomic(self.base_row())
        snap = snapshot_atomic(graph, generated_at=NOW, source_revision="drive:r1")
        self.assertEqual(snap["counts"]["applications"], 1)
        self.assertEqual(snap["counts"]["actions"], 2)
        recovered = graph.from_snapshot(snap)
        self.assertEqual(len(recovered.actions), 2)

    def test_decomposition_semicolon_preserves_sequence(self):
        steps = decompose_next_action("WAIT_REPLY; CAPTURE_FORM; HUMAN_FINAL_SUBMIT")
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[-1].executor, ExecutorType.HUMAN)


if __name__ == "__main__":
    unittest.main()
