import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.models import GateResult
from uexchanges.runtime_graph import ActionNode, ExecutorType, GateNode, RuntimeGraph
from uexchanges.runtime_v2.closed_loop import ClosedLoopRuntime
from uexchanges.runtime_v2.dispatcher import AutonomousEventDispatcher, DispatchStatus
from uexchanges.runtime_v2.event_router import (
    ExplicitEventRouter,
    IngressSource,
    NormalizedIngress,
)
from uexchanges.runtime_v2.models import RuntimeEventKind

NOW = datetime(2026, 9, 1, 21, 16, tzinfo=timezone.utc)


def _runtime() -> ClosedLoopRuntime:
    graph = RuntimeGraph()
    for app in ("app-1", "app-2"):
        gate_id = f"gate:{app}:route"
        graph.add_gate(GateNode(gate_id, app, "Route Gate", GateResult.UNKNOWN))
        graph.add_action(
            ActionNode(
                action_id=f"action:{app}:submit",
                application_id=app,
                action_type="SUBMIT",
                executor=ExecutorType.HUMAN,
                instruction="Submit",
                expected_output="receipt",
                requires=(gate_id,),
                priority=100,
                idempotency_key=f"idem:{app}:submit",
            )
        )
    graph.recompute(NOW)
    return ClosedLoopRuntime(graph)


def _gate_ingress(*, app="app-1", item="m1", sequence=1, observed_at=NOW):
    return NormalizedIngress(
        source=IngressSource.GMAIL,
        source_id="gmail:organiser-replies",
        source_item_id=item,
        source_version=f"gmail:{item}:v1",
        observed_at=observed_at,
        kind=RuntimeEventKind.GATE_RESOLVED,
        application_id=app,
        authority="organiser_email_fact",
        sequence=sequence,
        payload={
            "gate_name": "Route Gate",
            "result": "pass",
            "reason": "explicit organiser confirmation",
        },
    )


class RuntimeDispatcherTests(unittest.TestCase):
    def test_one_event_mutates_only_affected_application_and_unlocks_human(self):
        runtime = _runtime()
        dispatcher = AutonomousEventDispatcher(
            runtime=runtime, router=ExplicitEventRouter()
        )
        result = dispatcher.dispatch(_gate_ingress())
        self.assertEqual(result.status, DispatchStatus.APPLIED)
        self.assertEqual(
            result.frontier_change.human_added,
            ("action:app-1:submit",),
        )
        self.assertEqual(runtime.graph.gates["gate:app-1:route"].result, GateResult.PASS)
        self.assertEqual(runtime.graph.gates["gate:app-2:route"].result, GateResult.UNKNOWN)
        self.assertEqual(runtime.reducer.revision("app-1"), 1)
        self.assertEqual(runtime.reducer.revision("app-2"), 0)

    def test_duplicate_delivery_is_domain_noop(self):
        runtime = _runtime()
        dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
        ingress = _gate_ingress()
        first = dispatcher.dispatch(ingress)
        second = dispatcher.dispatch(ingress)
        self.assertEqual(first.status, DispatchStatus.APPLIED)
        self.assertEqual(second.status, DispatchStatus.DUPLICATE)
        self.assertEqual(runtime.reducer.revision("app-1"), 1)

    def test_unrouted_event_is_dead_lettered_and_does_not_block_cursor(self):
        runtime = _runtime()
        dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
        ingress = NormalizedIngress(
            source=IngressSource.OFFICIAL_SOURCE,
            source_id="source:salto",
            source_item_id="unknown-call",
            source_version="salto:unknown-call:v1",
            observed_at=NOW,
            kind=RuntimeEventKind.EVIDENCE_ADDED,
            opportunity_id="opp-not-mapped",
            sequence=7,
            payload={"evidence_ref": "source:unknown-call"},
        )
        result = dispatcher.dispatch(ingress)
        self.assertEqual(result.status, DispatchStatus.UNROUTED)
        self.assertEqual(len(dispatcher.dead_letters), 1)
        self.assertEqual(result.cursor.high_watermark, 7)

    def test_late_unique_event_applies_without_moving_cursor_backwards(self):
        runtime = _runtime()
        dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
        high = NormalizedIngress(
            source=IngressSource.SYSTEM,
            source_id="system:test",
            source_item_id="evt-10",
            source_version="v10",
            observed_at=NOW,
            kind=RuntimeEventKind.EVIDENCE_ADDED,
            application_id="app-1",
            sequence=10,
            payload={"evidence_ref": "ev:10"},
        )
        late = NormalizedIngress(
            source=IngressSource.SYSTEM,
            source_id="system:test",
            source_item_id="evt-5",
            source_version="v5",
            observed_at=NOW + timedelta(seconds=1),
            kind=RuntimeEventKind.EVIDENCE_ADDED,
            application_id="app-1",
            sequence=5,
            payload={"evidence_ref": "ev:5"},
        )
        self.assertEqual(dispatcher.dispatch(high).status, DispatchStatus.APPLIED)
        late_result = dispatcher.dispatch(late)
        self.assertEqual(late_result.status, DispatchStatus.APPLIED)
        self.assertEqual(late_result.cursor.high_watermark, 10)
        self.assertIn("ev:5", runtime.graph.completed_evidence)

    def test_raw_email_cannot_be_promoted_to_receipt(self):
        runtime = _runtime()
        dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
        ingress = NormalizedIngress(
            source=IngressSource.GMAIL,
            source_id="gmail:inbox",
            source_item_id="mail-receipt-ish",
            source_version="gmail:mail-receipt-ish:v1",
            observed_at=NOW,
            kind=RuntimeEventKind.RECEIPT_CONFIRMED,
            application_id="app-1",
            authority="organiser_email_fact",
            payload={
                "receipt_ref": "gmail:mail-receipt-ish",
                "submission_identity_bound": True,
            },
        )
        result = dispatcher.dispatch(ingress)
        self.assertEqual(result.status, DispatchStatus.DEAD_LETTER)
        self.assertNotIn("gmail:mail-receipt-ish", runtime.graph.completed_evidence)

    def test_strong_identity_bound_receipt_is_applied(self):
        runtime = _runtime()
        dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
        ingress = NormalizedIngress(
            source=IngressSource.RECEIPT,
            source_id="receipt:reconciler",
            source_item_id="rcpt-1",
            source_version="receipt:rcpt-1:v1",
            observed_at=NOW,
            kind=RuntimeEventKind.RECEIPT_CONFIRMED,
            application_id="app-1",
            authority="email_receipt",
            payload={
                "receipt_ref": "receipt:rcpt-1",
                "submission_identity_bound": True,
            },
        )
        result = dispatcher.dispatch(ingress)
        self.assertEqual(result.status, DispatchStatus.APPLIED)
        self.assertIn("receipt:rcpt-1", runtime.graph.completed_evidence)

    def test_retryable_failure_does_not_advance_cursor_until_success(self):
        class FlakyRuntime(ClosedLoopRuntime):
            def __init__(self, graph):
                super().__init__(graph)
                self.failures = 0

            def ingest_event(self, event):
                if self.failures < 2:
                    self.failures += 1
                    raise RuntimeError("temporary provider/reducer dependency")
                return super().ingest_event(event)

        base = _runtime()
        runtime = FlakyRuntime(base.graph)
        dispatcher = AutonomousEventDispatcher(
            runtime=runtime, router=ExplicitEventRouter(), max_attempts=3
        )
        ingress = _gate_ingress()
        one = dispatcher.dispatch(ingress)
        two = dispatcher.dispatch(ingress)
        three = dispatcher.dispatch(ingress)
        self.assertEqual(one.status, DispatchStatus.RETRY)
        self.assertEqual(two.status, DispatchStatus.RETRY)
        self.assertEqual(three.status, DispatchStatus.APPLIED)
        self.assertIsNone(one.cursor)
        self.assertIsNone(two.cursor)
        self.assertEqual(three.cursor.high_watermark, 1)

    def test_retry_budget_exhaustion_dead_letters_and_advances_cursor(self):
        class AlwaysFailRuntime(ClosedLoopRuntime):
            def ingest_event(self, event):
                raise RuntimeError("temporary forever")

        base = _runtime()
        runtime = AlwaysFailRuntime(base.graph)
        dispatcher = AutonomousEventDispatcher(
            runtime=runtime, router=ExplicitEventRouter(), max_attempts=3
        )
        ingress = _gate_ingress()
        self.assertEqual(dispatcher.dispatch(ingress).status, DispatchStatus.RETRY)
        self.assertEqual(dispatcher.dispatch(ingress).status, DispatchStatus.RETRY)
        final = dispatcher.dispatch(ingress)
        self.assertEqual(final.status, DispatchStatus.DEAD_LETTER)
        self.assertEqual(final.attempts, 3)
        self.assertEqual(final.cursor.high_watermark, 1)
        self.assertEqual(len(dispatcher.dead_letters), 1)


if __name__ == "__main__":
    unittest.main()
