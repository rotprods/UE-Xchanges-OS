import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.forms.models import (
    AuthRequirement,
    FormExecutionPlan,
    FormExecutionState,
    SubmissionAttempt,
    SubmitAuthority,
)
from uexchanges.human_command_center import build_human_command_center
from uexchanges.models import AIPolicy, GateResult
from uexchanges.receipt_reconciler import ReceiptCandidate, reconcile_receipt_candidate
from uexchanges.runtime_graph import ActionNode, ExecutorType, GateNode, RuntimeGraph
from uexchanges.runtime_v2 import (
    ClaimRecord,
    ClaimStatus,
    ClosedLoopRuntime,
    EvidenceRecord,
    IncrementalRuntimeReducer,
    RuntimeDomainEvent,
    RuntimeEventKind,
    TemporalScope,
    form_plan_runtime_events,
)

NOW = datetime(2026, 9, 1, 20, 0, tzinfo=timezone.utc)


def graph_two_apps():
    graph = RuntimeGraph()
    graph.add_gate(GateNode("g:a:route", "app-a", "Spain Gate", GateResult.UNKNOWN))
    graph.add_gate(GateNode("g:b:route", "app-b", "Spain Gate", GateResult.UNKNOWN))
    graph.add_action(
        ActionNode(
            "a:submit",
            "app-a",
            "SUBMIT",
            ExecutorType.HUMAN,
            "Submit A",
            "receipt",
            requires=("g:a:route",),
            priority=100,
            idempotency_key="ida",
            metadata={"title": "A"},
        )
    )
    graph.add_action(
        ActionNode(
            "b:submit",
            "app-b",
            "SUBMIT",
            ExecutorType.HUMAN,
            "Submit B",
            "receipt",
            requires=("g:b:route",),
            priority=90,
            idempotency_key="idb",
            metadata={"title": "B"},
        )
    )
    graph.recompute(NOW)
    return graph


class IncrementalReducerTests(unittest.TestCase):
    def test_gate_event_changes_only_affected_application(self):
        graph = graph_two_apps()
        reducer = IncrementalRuntimeReducer()
        event = RuntimeDomainEvent(
            "evt-1",
            RuntimeEventKind.GATE_RESOLVED,
            "app-a",
            NOW,
            "gmail:m1",
            "gmail:m1:v1",
            {"gate_name": "Spain Gate", "result": "pass", "reason": "Host confirms Spain"},
        )
        delta = reducer.apply(graph, event)
        self.assertFalse(delta.duplicate)
        self.assertEqual(graph.gates["g:a:route"].result, GateResult.PASS)
        self.assertEqual(graph.gates["g:b:route"].result, GateResult.UNKNOWN)
        self.assertEqual([c.application_id for c in build_human_command_center(graph, now=NOW)], ["app-a"])

    def test_duplicate_event_is_noop(self):
        graph = graph_two_apps()
        reducer = IncrementalRuntimeReducer()
        event = RuntimeDomainEvent(
            "evt-1",
            RuntimeEventKind.GATE_RESOLVED,
            "app-a",
            NOW,
            "gmail:m1",
            "gmail:m1:v1",
            {"gate_name": "Spain Gate", "result": "pass"},
        )
        reducer.apply(graph, event)
        duplicate = reducer.apply(graph, event)
        self.assertTrue(duplicate.duplicate)
        self.assertEqual(reducer.revision("app-a"), 1)


class EvidenceClaimTests(unittest.TestCase):
    def test_historical_erasmus_does_not_prove_current_youth_worker(self):
        runtime = ClosedLoopRuntime(RuntimeGraph())
        runtime.add_evidence(
            EvidenceRecord(
                "ev-history",
                "app-a",
                "drive:certificate",
                NOW,
                "erasmus_youth_staff_participation",
                True,
                TemporalScope.HISTORICAL,
                role_scopes=("participant",),
                supports_claim_keys=("historical_youth_sector_experience",),
                cannot_prove=("current_youth_worker", "trainer", "toy_reference"),
            )
        )
        decision = runtime.add_claim(
            ClaimRecord(
                "claim-current-yw",
                "app-a",
                "current_youth_worker",
                True,
                ("ev-history",),
                TemporalScope.CURRENT,
                required_role="youth_worker",
            ),
            now=NOW,
        )
        self.assertEqual(decision.status, ClaimStatus.BLOCKED)

    def test_supported_scoped_claim_passes(self):
        runtime = ClosedLoopRuntime(RuntimeGraph())
        runtime.add_evidence(
            EvidenceRecord(
                "ev-media",
                "app-a",
                "drive:portfolio",
                NOW,
                "video_portfolio",
                True,
                TemporalScope.CURRENT,
                role_scopes=("participant", "communications"),
                supports_claim_keys=("video_production_experience",),
            )
        )
        decision = runtime.add_claim(
            ClaimRecord(
                "claim-video",
                "app-a",
                "video_production_experience",
                True,
                ("ev-media",),
                TemporalScope.CURRENT,
                required_role="participant",
            )
        )
        self.assertEqual(decision.status, ClaimStatus.VERIFIED)


class FormBridgeTests(unittest.TestCase):
    def _plan(self, policy):
        return FormExecutionPlan(
            plan_id="plan-1",
            application_id="app-a",
            opportunity_id="opp-a",
            canonical_form_url="https://example.org/form",
            provider="example",
            form_fingerprint="sha256:" + "1" * 64,
            fields=(),
            ai_policy=policy,
            auth_requirement=AuthRequirement.NONE,
            submit_authority=SubmitAuthority.HUMAN_ONLY,
            allowed_origins=("https://example.org",),
            created_at=NOW,
            expires_at=NOW + timedelta(hours=1),
            source_version="form-v1",
            validation_signature="sha256:" + "2" * 64,
            state=FormExecutionState.FORM_SCHEMA_VERIFIED,
        )

    def test_ai_unknown_stays_unknown(self):
        events = form_plan_runtime_events(plan=self._plan(AIPolicy.UNKNOWN), observed_at=NOW)
        gate = events[1]
        self.assertEqual(gate.payload["result"], "unknown")

    def test_known_policy_can_resolve_composite_gate(self):
        events = form_plan_runtime_events(plan=self._plan(AIPolicy.ASSIST_ONLY), observed_at=NOW)
        self.assertEqual(events[1].payload["result"], "pass")


class ReceiptTests(unittest.TestCase):
    def _attempt(self):
        return SubmissionAttempt(
            attempt_id="attempt-1",
            application_id="app-a",
            submission_key="sha256:" + "3" * 64,
            attempted_at=NOW,
            form_fingerprint="sha256:" + "4" * 64,
            plan_hash="sha256:" + "5" * 64,
        )

    def test_unverified_email_does_not_become_receipt(self):
        candidate = ReceiptCandidate(
            "app-a",
            NOW + timedelta(minutes=1),
            "gmail:m1",
            "gmail:m1:v1",
            email_receipt_ref="gmail:m1",
            authoritative_confirmation=False,
        )
        with self.assertRaises(ValueError):
            reconcile_receipt_candidate(candidate=candidate, attempt=self._attempt())

    def test_authoritative_email_confirmation_creates_runtime_event(self):
        candidate = ReceiptCandidate(
            "app-a",
            NOW + timedelta(minutes=1),
            "gmail:m1",
            "gmail:m1:v1",
            email_receipt_ref="gmail:m1",
            authoritative_confirmation=True,
        )
        result = reconcile_receipt_candidate(candidate=candidate, attempt=self._attempt())
        self.assertEqual(result.runtime_event.kind, RuntimeEventKind.RECEIPT_CONFIRMED)
        self.assertEqual(result.reconciled_attempt.status.value, "receipt_confirmed")


class HumanCommandCenterTests(unittest.TestCase):
    def test_only_ready_human_actions_are_exposed(self):
        graph = graph_two_apps()
        graph.gates["g:a:route"] = GateNode("g:a:route", "app-a", "Spain Gate", GateResult.PASS)
        cards = build_human_command_center(graph, now=NOW, max_items=5)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].application_id, "app-a")
        self.assertIn("envío", cards[0].instruction.lower())


if __name__ == "__main__":
    unittest.main()
