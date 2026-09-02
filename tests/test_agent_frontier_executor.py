import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.coordination import AgentSession, LeaseStatus, SessionStatus, WorkLease
from uexchanges.runtime_graph import ActionNode, ActionState, ExecutorType, RuntimeGraph
from uexchanges.runtime_v2.action_handlers import (
    AgentActionResult,
    HandlerDisposition,
    HandlerRegistry,
    static_handler,
)
from uexchanges.runtime_v2.agent_executor import AgentExecutionStatus, AgentFrontierExecutor
from uexchanges.runtime_v2.closed_loop import ClosedLoopRuntime
from uexchanges.runtime_v2.dispatcher import AutonomousEventDispatcher
from uexchanges.runtime_v2.event_router import ExplicitEventRouter, IngressSource, NormalizedIngress
from uexchanges.runtime_v2.models import RuntimeEventKind

NOW = datetime(2026, 9, 2, 7, 0, tzinfo=timezone(timedelta(hours=2)))


def session():
    return AgentSession(
        session_id="SES-TEST-RG23",
        agent_id="AGT-TEST-RG23",
        project_id="UE-Xchanges-OS",
        context_id="CTX-TEST",
        started_at=NOW,
        last_heartbeat=NOW,
        status=SessionStatus.ACTIVE,
    )


def graph_with(action_type="VERIFY_SOURCE", *, executor=ExecutorType.AGENT, application_id="app-1"):
    graph = RuntimeGraph()
    graph.add_action(
        ActionNode(
            action_id=f"action:{application_id}:1",
            application_id=application_id,
            action_type=action_type,
            executor=executor,
            instruction=action_type.replace("_", " "),
            expected_output="evidence",
            priority=100,
            idempotency_key=f"idem:{application_id}:{action_type}",
            metadata={"title": "Test"},
        )
    )
    graph.recompute(NOW)
    return graph


def executor_for(graph, registry, *, existing=None, max_attempts=3):
    runtime = ClosedLoopRuntime(graph)
    dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
    return AgentFrontierExecutor(
        runtime=runtime,
        dispatcher=dispatcher,
        session=session(),
        handlers=registry,
        existing_action_leases=existing,
        max_attempts=max_attempts,
        retry_base=timedelta(minutes=1),
    )


class AgentFrontierExecutorTests(unittest.TestCase):
    def test_safe_agent_action_completes_only_with_evidence_and_releases_fence(self):
        graph = graph_with()
        registry = HandlerRegistry()
        registry.register_prefix(
            "VERIFY_",
            static_handler(
                AgentActionResult(
                    HandlerDisposition.SUCCEEDED,
                    observed_at=NOW,
                    evidence_refs=("official:test-source",),
                    reason_code="SOURCE_VERIFIED",
                )
            ),
        )
        executor = executor_for(graph, registry)
        record = executor.execute_one(action_id="action:app-1:1", now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.COMPLETED)
        self.assertEqual(graph.actions[record.action_id].state, ActionState.DONE)
        self.assertEqual(record.lease_id, record.fencing_token)
        self.assertEqual(executor.action_leases[record.action_id].status, LeaseStatus.RELEASED)
        self.assertIn("official:test-source", graph.completed_evidence)

    def test_misclassified_submit_action_is_blocked_even_when_executor_is_agent(self):
        graph = graph_with("VERIFY_SOURCE_THEN_SUBMIT")
        registry = HandlerRegistry()
        registry.register_prefix(
            "VERIFY_",
            static_handler(
                AgentActionResult(
                    HandlerDisposition.SUCCEEDED,
                    observed_at=NOW,
                    evidence_refs=("evidence:x",),
                )
            ),
        )
        record = executor_for(graph, registry).execute_one(action_id="action:app-1:1", now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_SAFETY)
        self.assertIsNone(record.lease_id)
        self.assertEqual(graph.actions[record.action_id].state, ActionState.READY)

    def test_human_action_is_never_claimed(self):
        graph = graph_with("VERIFY_SOURCE", executor=ExecutorType.HUMAN)
        registry = HandlerRegistry()
        record = executor_for(graph, registry).execute_one(action_id="action:app-1:1", now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_SAFETY)

    def test_missing_handler_fails_closed_without_claim(self):
        graph = graph_with("VERIFY_SOURCE")
        record = executor_for(graph, HandlerRegistry()).execute_one(action_id="action:app-1:1", now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.NO_HANDLER)
        self.assertIsNone(record.lease_id)

    def test_unexpired_foreign_action_lease_blocks_execution(self):
        graph = graph_with()
        action_id = "action:app-1:1"
        foreign = WorkLease(
            lease_id="LSE-FOREIGN",
            project_id="UE-Xchanges-OS",
            context_id="CTX-TEST",
            resource_type="runtime_action",
            resource_id=action_id,
            owner_agent_id="OTHER",
            owner_session_id="OTHER-SESSION",
            acquired_at=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(minutes=5),
            last_heartbeat=NOW - timedelta(minutes=1),
        )
        registry = HandlerRegistry()
        registry.register_prefix(
            "VERIFY_",
            static_handler(AgentActionResult(HandlerDisposition.SUCCEEDED, NOW, ("evidence:x",))),
        )
        record = executor_for(graph, registry, existing={action_id: foreign}).execute_one(action_id=action_id, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_LEASE)
        self.assertEqual(record.lease_id, "LSE-FOREIGN")
        self.assertEqual(graph.actions[action_id].state, ActionState.READY)

    def test_expired_lease_takeover_gets_new_fencing_token(self):
        graph = graph_with()
        action_id = "action:app-1:1"
        expired = WorkLease(
            lease_id="LSE-OLD",
            project_id="UE-Xchanges-OS",
            context_id="CTX-TEST",
            resource_type="runtime_action",
            resource_id=action_id,
            owner_agent_id="OTHER",
            owner_session_id="OTHER-SESSION",
            acquired_at=NOW - timedelta(minutes=20),
            expires_at=NOW - timedelta(minutes=10),
            last_heartbeat=NOW - timedelta(minutes=20),
        )
        registry = HandlerRegistry()
        registry.register_prefix(
            "VERIFY_",
            static_handler(AgentActionResult(HandlerDisposition.SUCCEEDED, NOW, ("evidence:x",))),
        )
        record = executor_for(graph, registry, existing={action_id: expired}).execute_one(action_id=action_id, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.COMPLETED)
        self.assertNotEqual(record.fencing_token, "LSE-OLD")

    def test_retryable_handler_resumes_then_completes(self):
        graph = graph_with()
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            if calls["n"] == 1:
                return AgentActionResult(
                    HandlerDisposition.RETRYABLE,
                    request.observed_at,
                    reason_code="TRANSIENT_PROVIDER_TIMEOUT",
                    retryable=True,
                )
            return AgentActionResult(
                HandlerDisposition.SUCCEEDED,
                request.observed_at,
                evidence_refs=("official:retry-success",),
            )

        registry = HandlerRegistry()
        registry.register_prefix("VERIFY_", handler)
        executor = executor_for(graph, registry)
        first = executor.run_cycle(now=NOW, max_actions=1).records[0]
        self.assertEqual(first.status, AgentExecutionStatus.RETRY_SCHEDULED)
        self.assertEqual(graph.actions[first.action_id].state, ActionState.WAITING)
        second = executor.run_cycle(now=NOW + timedelta(minutes=2), max_actions=1).records[0]
        self.assertEqual(second.status, AgentExecutionStatus.COMPLETED)
        self.assertEqual(calls["n"], 2)

    def test_retry_budget_exhaustion_is_terminal_for_the_action(self):
        graph = graph_with()

        def handler(request):
            return AgentActionResult(
                HandlerDisposition.RETRYABLE,
                request.observed_at,
                reason_code="TRANSIENT_FAILURE",
                retryable=True,
            )

        registry = HandlerRegistry()
        registry.register_prefix("VERIFY_", handler)
        executor = executor_for(graph, registry, max_attempts=3)
        times = (NOW, NOW + timedelta(minutes=2), NOW + timedelta(minutes=5))
        records = []
        for when in times:
            records.append(executor.run_cycle(now=when, max_actions=1).records[0])
        self.assertEqual(records[-1].status, AgentExecutionStatus.FAILED)
        self.assertEqual(graph.actions[records[-1].action_id].state, ActionState.FAILED)
        self.assertEqual(records[-1].attempts, 3)

    def test_cross_application_ingress_is_rejected_before_dispatch(self):
        graph = graph_with()
        ingress = NormalizedIngress(
            source=IngressSource.OFFICIAL_SOURCE,
            source_id="official:test",
            source_item_id="item-1",
            source_version="v1",
            observed_at=NOW,
            kind=RuntimeEventKind.EVIDENCE_ADDED,
            application_id="app-OTHER",
            authority="official_call_source",
            payload={"evidence_ref": "official:item-1"},
        )
        registry = HandlerRegistry()
        registry.register_prefix(
            "VERIFY_",
            static_handler(
                AgentActionResult(
                    HandlerDisposition.SUCCEEDED,
                    NOW,
                    evidence_refs=("official:item-1",),
                    ingresses=(ingress,),
                )
            ),
        )
        record = executor_for(graph, registry).execute_one(action_id="action:app-1:1", now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.FAILED)
        self.assertIn("HANDLER_CONTRACT_FAILURE", record.reason)
        self.assertEqual(graph.actions[record.action_id].state, ActionState.FAILED)

    def test_cycle_is_bounded(self):
        graph = RuntimeGraph()
        for index in range(5):
            graph.add_action(
                ActionNode(
                    action_id=f"action:app-{index}:1",
                    application_id=f"app-{index}",
                    action_type="VERIFY_SOURCE",
                    executor=ExecutorType.AGENT,
                    instruction="Verify source",
                    expected_output="evidence",
                    priority=100 - index,
                    idempotency_key=f"idem-{index}",
                )
            )
        graph.recompute(NOW)
        registry = HandlerRegistry()

        def handler(request):
            return AgentActionResult(
                HandlerDisposition.SUCCEEDED,
                request.observed_at,
                evidence_refs=(f"evidence:{request.application_id}",),
            )

        registry.register_prefix("VERIFY_", handler)
        cycle = executor_for(graph, registry).run_cycle(now=NOW, max_actions=2)
        self.assertEqual(len(cycle.records), 2)
        self.assertEqual(len(cycle.selected_action_ids), 2)
        self.assertEqual(len(cycle.completed), 2)


if __name__ == "__main__":
    unittest.main()
