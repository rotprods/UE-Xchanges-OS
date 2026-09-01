import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.models import GateResult
from uexchanges.runtime_graph import ActionNode, ExecutorType, GateNode, RuntimeGraph
from uexchanges.runtime_v2.closed_loop import ClosedLoopRuntime
from uexchanges.runtime_v2.dispatcher import AutonomousEventDispatcher
from uexchanges.runtime_v2.event_router import ExplicitEventRouter
from uexchanges.runtime_v2.models import ClaimRecord, EvidenceRecord, TemporalScope
from uexchanges.runtime_v2.projection_health import (
    ObservedTodoistTask,
    ProjectionHealthStatus,
    ProjectionRepairAction,
    TodoistRepairAction,
    build_projection_repair_plan,
    build_todoist_repair_plan,
)
from uexchanges.runtime_v2.projections import (
    ProjectionDocument,
    build_projection_documents,
    expected_todoist_tasks,
)

NOW = datetime(2026, 9, 2, 0, 16, tzinfo=timezone(timedelta(hours=2)))


def _runtime_and_dispatcher():
    graph = RuntimeGraph()
    gate = GateNode(
        "gate:app-1:route",
        "app-1",
        "Route Gate",
        GateResult.PASS,
        evidence_refs=("official:route",),
    )
    graph.add_gate(gate)
    graph.add_action(
        ActionNode(
            action_id="action:app-1:human-submit",
            application_id="app-1",
            action_type="SUBMIT",
            executor=ExecutorType.HUMAN,
            instruction="Review and submit",
            expected_output="receipt",
            requires=(gate.gate_id,),
            priority=100,
            deadline=NOW + timedelta(hours=4),
            idempotency_key="idem:app-1:human-submit",
            metadata={"title": "Example Call", "opportunity_id": "opp-1"},
        )
    )
    graph.add_action(
        ActionNode(
            action_id="action:app-2:verify",
            application_id="app-2",
            action_type="VERIFY_SOURCE",
            executor=ExecutorType.AGENT,
            instruction="Verify official source",
            expected_output="source_evidence",
            priority=80,
            idempotency_key="idem:app-2:verify",
            metadata={"title": "Second Call", "opportunity_id": "opp-2"},
        )
    )
    graph.recompute(NOW)
    runtime = ClosedLoopRuntime(graph)
    dispatcher = AutonomousEventDispatcher(runtime=runtime, router=ExplicitEventRouter())
    return runtime, dispatcher


class RuntimeProjectionSelfHealTests(unittest.TestCase):
    def test_projection_bundle_is_deterministic_and_hides_claim_values(self):
        runtime, dispatcher = _runtime_and_dispatcher()
        evidence = EvidenceRecord(
            evidence_id="ev-1",
            application_id="app-1",
            source_ref="private:drive:ev-1",
            observed_at=NOW,
            fact_key="private_fact",
            fact_value="PRIVATE-SECRET-VALUE",
            temporal_scope=TemporalScope.CURRENT,
            role_scopes=("participant",),
            supports_claim_keys=("eligible_participant",),
        )
        runtime.add_evidence(evidence)
        runtime.add_claim(
            ClaimRecord(
                claim_id="claim-1",
                application_id="app-1",
                claim_key="eligible_participant",
                value="PRIVATE-SECRET-VALUE",
                evidence_ids=("ev-1",),
                temporal_scope=TemporalScope.CURRENT,
                required_role="participant",
            ),
            now=NOW,
        )
        documents = build_projection_documents(
            runtime=runtime,
            dispatcher=dispatcher,
            generated_at=NOW,
            source_revision="github:main@abc",
            watermark="event:100",
        )
        self.assertIn("Human_Now", documents)
        self.assertIn("Agent_Next", documents)
        self.assertIn("Claim_Registry", documents)
        rendered_claim_projection = repr(documents["Claim_Registry"].rows)
        self.assertNotIn("PRIVATE-SECRET-VALUE", rendered_claim_projection)
        self.assertIn("verified", rendered_claim_projection)

    def test_healthy_projection_needs_no_repair(self):
        runtime, dispatcher = _runtime_and_dispatcher()
        expected = build_projection_documents(
            runtime=runtime,
            dispatcher=dispatcher,
            generated_at=NOW,
            source_revision="github:main@abc",
            watermark="event:100",
        )
        plan = build_projection_repair_plan(expected=expected, actual=expected)
        self.assertTrue(plan.healthy)
        self.assertTrue(all(item.status is ProjectionHealthStatus.HEALTHY for item in plan.health))

    def test_row_drift_generates_replace_only_for_derived_surface(self):
        runtime, dispatcher = _runtime_and_dispatcher()
        expected = build_projection_documents(
            runtime=runtime,
            dispatcher=dispatcher,
            generated_at=NOW,
            source_revision="github:main@abc",
            watermark="event:100",
        )
        human = expected["Human_Now"]
        drifted_human = ProjectionDocument(
            surface=human.surface,
            source_revision=human.source_revision,
            watermark=human.watermark,
            generated_at=human.generated_at,
            rows=human.rows + ((999, "STALE"),),
        )
        actual = dict(expected)
        actual["Human_Now"] = drifted_human
        plan = build_projection_repair_plan(expected=expected, actual=actual)
        repairs = [item for item in plan.repairs if item.surface == "Human_Now"]
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0].action, ProjectionRepairAction.REPLACE_DERIVED_ROWS)

    def test_stale_watermark_triggers_repair_even_when_rows_match(self):
        runtime, dispatcher = _runtime_and_dispatcher()
        expected = build_projection_documents(
            runtime=runtime,
            dispatcher=dispatcher,
            generated_at=NOW,
            source_revision="github:main@abc",
            watermark="event:101",
        )
        human = expected["Human_Now"]
        stale = ProjectionDocument(
            surface=human.surface,
            source_revision=human.source_revision,
            watermark="event:100",
            generated_at=human.generated_at,
            rows=human.rows,
        )
        actual = dict(expected)
        actual["Human_Now"] = stale
        plan = build_projection_repair_plan(expected=expected, actual=actual)
        health = next(item for item in plan.health if item.surface == "Human_Now")
        self.assertEqual(health.status, ProjectionHealthStatus.STALE)

    def test_self_heal_refuses_canonical_surfaces(self):
        runtime, dispatcher = _runtime_and_dispatcher()
        base = build_projection_documents(
            runtime=runtime,
            dispatcher=dispatcher,
            generated_at=NOW,
            source_revision="github:main@abc",
            watermark="event:100",
        )
        forbidden = ProjectionDocument(
            surface="Applications",
            source_revision="github:main@abc",
            watermark="event:100",
            generated_at=NOW,
            rows=(("Application ID",),),
        )
        with self.assertRaises(ValueError):
            build_projection_repair_plan(expected={**base, "Applications": forbidden}, actual=base)

    def test_todoist_repair_plan_creates_updates_and_retires_by_runtime_action_id(self):
        runtime, _ = _runtime_and_dispatcher()
        expected = expected_todoist_tasks(runtime=runtime, now=NOW)
        self.assertEqual(len(expected), 1)
        create_and_retire = build_todoist_repair_plan(
            expected=expected,
            actual=(
                ObservedTodoistTask(
                    task_id="task-stale",
                    runtime_action_id="action:stale",
                    content="old",
                    description="old",
                    priority="p1",
                    due=None,
                    labels=("uexchanges", "runtimegraph", "human_now"),
                ),
            ),
        )
        self.assertEqual(
            {item.action for item in create_and_retire},
            {TodoistRepairAction.CREATE, TodoistRepairAction.RETIRE},
        )

        task = expected[0]
        update = build_todoist_repair_plan(
            expected=expected,
            actual=(
                ObservedTodoistTask(
                    task_id="task-live",
                    runtime_action_id=task.runtime_action_id,
                    content="stale content",
                    description=task.description,
                    priority=task.priority,
                    due=task.due,
                    labels=task.labels,
                ),
            ),
        )
        self.assertEqual(len(update), 1)
        self.assertEqual(update[0].action, TodoistRepairAction.UPDATE)


if __name__ == "__main__":
    unittest.main()
