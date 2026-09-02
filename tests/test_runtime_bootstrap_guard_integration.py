import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.bootstrap_guard import GuardCode, GuardDecision
from uexchanges.coordination import AgentSession, SessionStatus
from uexchanges.runtime_graph import ActionNode, ActionState, ExecutorType, RuntimeGraph
from uexchanges.runtime_v2.action_handlers import AgentActionResult, HandlerDisposition, HandlerRegistry
from uexchanges.runtime_v2.agent_executor import AgentExecutionStatus, AgentFrontierExecutor
from uexchanges.runtime_v2.closed_loop import ClosedLoopRuntime
from uexchanges.runtime_v2.dispatcher import AutonomousEventDispatcher
from uexchanges.runtime_v2.event_router import ExplicitEventRouter

NOW = datetime(2026, 9, 2, 9, 0, tzinfo=timezone(timedelta(hours=2)))
ACTION_ID = "action:app-guard:verify"


def build_executor(*, authorizer, calls):
    graph = RuntimeGraph()
    graph.add_action(
        ActionNode(
            action_id=ACTION_ID,
            application_id="app-guard",
            action_type="VERIFY_SOURCE",
            executor=ExecutorType.AGENT,
            instruction="Verify source",
            expected_output="evidence",
            priority=100,
            idempotency_key="idem:app-guard:verify",
        )
    )
    graph.recompute(NOW)
    runtime = ClosedLoopRuntime(graph)
    dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
    registry = HandlerRegistry()

    def handler(request):
        calls["handler"] += 1
        return AgentActionResult(
            HandlerDisposition.SUCCEEDED,
            request.observed_at,
            evidence_refs=("official:guard-test",),
        )

    registry.register_prefix("VERIFY_", handler)
    executor = AgentFrontierExecutor(
        runtime=runtime,
        dispatcher=dispatcher,
        session=AgentSession(
            session_id="SES-GUARD",
            agent_id="AGT-GUARD",
            project_id="UE-Xchanges-OS",
            context_id="CTX-GUARD",
            started_at=NOW,
            last_heartbeat=NOW,
            status=SessionStatus.ACTIVE,
        ),
        handlers=registry,
        bootstrap_authorizer=authorizer,
    )
    return graph, executor


class RuntimeBootstrapGuardIntegrationTests(unittest.TestCase):
    def assertZeroClaimSideEffects(self, graph, executor, calls):
        self.assertEqual(graph.actions[ACTION_ID].state, ActionState.READY)
        self.assertEqual(calls["handler"], 0)
        self.assertNotIn(ACTION_ID, executor.action_leases)
        self.assertNotIn(ACTION_ID, executor.attempts)
        self.assertEqual(graph.completed_evidence, set())

    def test_missing_authorizer_is_fail_closed(self):
        calls = {"handler": 0}
        graph, executor = build_executor(authorizer=None, calls=calls)
        record = executor.execute_one(action_id=ACTION_ID, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_BOOTSTRAP)
        self.assertEqual(record.reason, "BOOTSTRAP_GUARD_NOT_CONFIGURED")
        self.assertIsNone(record.lease_id)
        self.assertZeroClaimSideEffects(graph, executor, calls)

    def test_guard_denial_is_fail_closed_and_reason_coded(self):
        calls = {"handler": 0}

        def deny(lease, now):
            return GuardDecision(False, (GuardCode.MISSING_BOOTSTRAP_ACK, GuardCode.PRELEASE_MAIN_SHA_STALE))

        graph, executor = build_executor(authorizer=deny, calls=calls)
        record = executor.execute_one(action_id=ACTION_ID, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_BOOTSTRAP)
        self.assertEqual(record.reason, "BOOTSTRAP_DENIED:MISSING_BOOTSTRAP_ACK,PRELEASE_MAIN_SHA_STALE")
        self.assertZeroClaimSideEffects(graph, executor, calls)

    def test_guard_exception_is_fail_closed(self):
        calls = {"handler": 0}

        def broken(lease, now):
            raise RuntimeError("connector unavailable")

        graph, executor = build_executor(authorizer=broken, calls=calls)
        record = executor.execute_one(action_id=ACTION_ID, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_BOOTSTRAP)
        self.assertEqual(record.reason, "BOOTSTRAP_GUARD_FAILURE:RuntimeError")
        self.assertZeroClaimSideEffects(graph, executor, calls)

    def test_invalid_authorizer_contract_is_fail_closed(self):
        calls = {"handler": 0}
        graph, executor = build_executor(authorizer=lambda lease, now: True, calls=calls)
        record = executor.execute_one(action_id=ACTION_ID, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.BLOCKED_BOOTSTRAP)
        self.assertEqual(record.reason, "BOOTSTRAP_GUARD_CONTRACT_INVALID")
        self.assertZeroClaimSideEffects(graph, executor, calls)

    def test_guard_allow_preserves_existing_executor_semantics(self):
        calls = {"handler": 0}
        graph, executor = build_executor(
            authorizer=lambda lease, now: GuardDecision(True, (GuardCode.COMPLIANT,)),
            calls=calls,
        )
        record = executor.execute_one(action_id=ACTION_ID, now=NOW)
        self.assertEqual(record.status, AgentExecutionStatus.COMPLETED)
        self.assertEqual(calls["handler"], 1)
        self.assertEqual(graph.actions[ACTION_ID].state, ActionState.DONE)
        self.assertIsNotNone(record.fencing_token)


if __name__ == "__main__":
    unittest.main()
