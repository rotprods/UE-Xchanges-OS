import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.coordination import AgentSession, LeaseStatus, SessionStatus, WorkLease
from uexchanges.models import GateResult
from uexchanges.runtime_adapters import (
    EvidenceSignal,
    apply_evidence_signal,
    authorize_runtime_mutation,
    gmail_signal,
    todoist_human_projection,
)
from uexchanges.runtime_graph import (
    ActionNode,
    ActionState,
    ExecutorType,
    GateNode,
    RuntimeGraph,
    compile_mass_apply_row,
)

NOW = datetime(2026, 9, 1, 16, 0, tzinfo=timezone.utc)


class RuntimeAdapterTests(unittest.TestCase):
    def _session(self):
        return AgentSession(
            session_id="SES-1",
            agent_id="AGT-1",
            project_id="UE-Xchanges-OS",
            context_id="CTX-1",
            started_at=NOW,
            last_heartbeat=NOW,
            status=SessionStatus.ACTIVE,
        )

    def _lease(self, action_id="action:app:next", *, owner="SES-1", status=LeaseStatus.ACTIVE):
        return WorkLease(
            lease_id="LSE-1",
            project_id="UE-Xchanges-OS",
            context_id="CTX-1",
            resource_type="runtime_action",
            resource_id=action_id,
            owner_agent_id="AGT-1",
            owner_session_id=owner,
            acquired_at=NOW,
            expires_at=NOW + timedelta(hours=1),
            last_heartbeat=NOW,
            status=status,
        )

    def test_verification_action_is_ready_while_gates_unknown(self):
        graph = compile_mass_apply_row(
            {
                "Application ID": "app",
                "Opportunity ID": "opp",
                "Title": "Verify me",
                "Provider": "SALTO",
                "Bucket": "T1_2_3_DAYS",
                "Spain Gate": "SPAIN_INCLUDED_OR_ROUTE_TO_VERIFY",
                "Role Gate": "DETAIL_PROFILE_EXTRACTION_PENDING",
                "Infopack/Form/AI": "CAPTURE_PENDING | AI_UNKNOWN",
                "Submit State": "NOT_SUBMITTED",
                "Next Action": "EXTRACT_DETAIL_INFOPACK_FORM_POLICY_PREPARE",
            }
        )
        self.assertEqual(len(graph.agent_frontier(NOW)), 1)
        self.assertEqual(graph.human_frontier(NOW), [])

    def test_submit_remains_blocked_on_unknown_form_policy(self):
        graph = compile_mass_apply_row(
            {
                "Application ID": "app",
                "Opportunity ID": "opp",
                "Title": "Submit me",
                "Provider": "SALTO",
                "Bucket": "T0_TODAY",
                "Spain Gate": "SPAIN_CONFIRMED",
                "Role Gate": "PASS_PROFILE_CONFIRMED",
                "Infopack/Form/AI": "FORM_VERIFIED | AI_UNKNOWN",
                "Submit State": "HUMAN_NOW",
                "Next Action": "HUMAN_FINAL_SUBMIT_STORE_RECEIPT",
            }
        )
        self.assertEqual(graph.human_frontier(NOW), [])

    def test_payment_does_not_require_ai_policy_gate(self):
        graph = compile_mass_apply_row(
            {
                "Application ID": "app",
                "Opportunity ID": "opp",
                "Title": "Payment gate",
                "Provider": "PARTNER",
                "Bucket": "T0_SELECTED_HUMAN_CONFIRMATION",
                "Spain Gate": "SPAIN_CONFIRMED",
                "Role Gate": "SELECTED_BY_SENDING_ORG PASS",
                "Infopack/Form/AI": "AI_UNKNOWN",
                "Submit State": "SELECTED_NOT_CONFIRMED",
                "Next Action": "HUMAN_PAY_30_CAPTURE_RECEIPT",
            }
        )
        self.assertEqual(len(graph.human_frontier(NOW)), 1)

    def test_waiting_external_is_not_frontier_noise(self):
        graph = compile_mass_apply_row(
            {
                "Application ID": "app",
                "Opportunity ID": "opp",
                "Title": "Waiting",
                "Provider": "HOST",
                "Bucket": "T1_ASAP",
                "Spain Gate": "SPAIN_CONFIRMED",
                "Role Gate": "PASS",
                "Infopack/Form/AI": "AI_UNKNOWN",
                "Submit State": "WAITING_EXTERNAL_EVIDENCE",
                "Next Action": "WAIT_HOST_REPLY_THEN_CAPTURE_FORM",
            }
        )
        action = next(iter(graph.actions.values()))
        self.assertEqual(action.state, ActionState.WAITING)
        self.assertEqual(graph.agent_frontier(NOW), [])

    def test_normalized_gmail_signal_updates_one_gate(self):
        graph = RuntimeGraph(
            gates={
                "g": GateNode("g", "app", "Role Gate", GateResult.UNKNOWN, "pending")
            }
        )
        signal = gmail_signal(
            application_id="app",
            gate_name="Role Gate",
            result=GateResult.PASS,
            reason="Organiser explicitly confirmed eligibility.",
            message_id="abc123",
            message_timestamp="2026-09-01T15:00:00+02:00",
        )
        updated = apply_evidence_signal(graph, signal)
        self.assertEqual(updated.result, GateResult.PASS)
        self.assertIn("gmail:abc123", updated.evidence_refs)

    def test_evidence_signal_refuses_ambiguous_gate_target(self):
        graph = RuntimeGraph()
        with self.assertRaises(ValueError):
            apply_evidence_signal(
                graph,
                EvidenceSignal("app", "Role Gate", GateResult.PASS, "x", "gmail:1", "v1"),
            )

    def test_runtime_mutation_requires_exact_action_lease(self):
        action = ActionNode(
            "action:app:next",
            "app",
            "VERIFY",
            ExecutorType.AGENT,
            "Verify",
            "evidence",
            idempotency_key="rgidem-x",
        )
        authorized = authorize_runtime_mutation(
            action=action,
            session=self._session(),
            lease=self._lease(),
            now=NOW + timedelta(minutes=1),
            operation="CLAIM",
            authoritative_source_version="drive:rev1",
        )
        self.assertTrue(authorized.allowed)

    def test_stale_writer_wrong_session_is_blocked(self):
        action = ActionNode(
            "action:app:next",
            "app",
            "VERIFY",
            ExecutorType.AGENT,
            "Verify",
            "evidence",
            idempotency_key="rgidem-x",
        )
        authorized = authorize_runtime_mutation(
            action=action,
            session=self._session(),
            lease=self._lease(owner="OTHER-SESSION"),
            now=NOW + timedelta(minutes=1),
            operation="CLAIM",
            authoritative_source_version="drive:rev1",
        )
        self.assertFalse(authorized.allowed)

    def test_wrong_action_scope_is_blocked(self):
        action = ActionNode(
            "action:other:next",
            "other",
            "VERIFY",
            ExecutorType.AGENT,
            "Verify",
            "evidence",
            idempotency_key="rgidem-y",
        )
        authorized = authorize_runtime_mutation(
            action=action,
            session=self._session(),
            lease=self._lease(action_id="action:app:next"),
            now=NOW + timedelta(minutes=1),
            operation="CLAIM",
            authoritative_source_version="drive:rev1",
        )
        self.assertFalse(authorized.allowed)

    def test_todoist_projection_contains_only_ready_human_actions(self):
        graph = RuntimeGraph()
        graph.add_action(ActionNode("h", "app1", "LOGIN", ExecutorType.HUMAN, "Login", "access", priority=100))
        graph.add_action(ActionNode("a", "app2", "VERIFY", ExecutorType.AGENT, "Verify", "evidence", priority=100))
        tasks = todoist_human_projection(graph, now=NOW, project_id="P", parent_id="ROOT")
        self.assertEqual(len(tasks), 1)
        self.assertIn("Login", tasks[0]["content"])
        self.assertEqual(tasks[0]["parentId"], "ROOT")


if __name__ == "__main__":
    unittest.main()
