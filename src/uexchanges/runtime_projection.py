from __future__ import annotations

from datetime import datetime
from typing import Any

from .runtime_graph import ActionNode, RuntimeGraph


def atomic_edges(graph: RuntimeGraph) -> list[dict[str, str]]:
    edges: set[tuple[str, str, str]] = set()
    actions_by_application: dict[str, list[ActionNode]] = {}
    for action in graph.actions.values():
        actions_by_application.setdefault(action.application_id, []).append(action)

    for application_id, actions in actions_by_application.items():
        ordered = sorted(actions, key=lambda action: int(action.metadata.get("ordinal", 1)))
        opportunity_id = str(ordered[0].metadata.get("opportunity_id") or "") if ordered else ""
        if opportunity_id:
            edges.add((f"opportunity:{opportunity_id}", "HAS_APPLICATION", f"application:{application_id}"))
        for action in ordered:
            edges.add((f"application:{application_id}", "HAS_ACTION", action.action_id))
            for requirement in action.requires:
                edges.add((requirement, "UNLOCKS", action.action_id))
            for next_action in action.next_actions:
                edges.add((action.action_id, "PRECEDES", next_action))
        if ordered:
            edges.add((f"application:{application_id}", "HAS_NEXT_ACTION", ordered[0].action_id))

    for gate in graph.gates.values():
        edges.add((f"application:{gate.application_id}", "HAS_GATE", gate.gate_id))

    return [
        {"from": source, "type": relation, "to": target, "authority": "derived_runtime_projection"}
        for source, relation, target in sorted(edges)
    ]


def projection_rows_atomic(graph: RuntimeGraph, *, generated_at: datetime) -> dict[str, list[list[Any]]]:
    graph.recompute(generated_at)
    action_rows = [[
        "Action ID", "Application ID", "Opportunity ID", "Title", "Executor",
        "Action Type", "Runtime State", "Ordinal", "Step Count", "Priority",
        "Deadline", "Bucket", "Submit State", "Expected Output", "Requires",
        "Next Actions", "Idempotency Key", "Generated At",
    ]]
    for action in sorted(
        graph.actions.values(),
        key=lambda item: (
            -item.priority,
            item.deadline.isoformat() if item.deadline else "9999",
            item.application_id,
            int(item.metadata.get("ordinal", 1)),
        ),
    ):
        action_rows.append([
            action.action_id,
            action.application_id,
            action.metadata.get("opportunity_id", ""),
            action.metadata.get("title", ""),
            action.executor.value,
            action.action_type,
            action.state.value,
            action.metadata.get("ordinal", 1),
            action.metadata.get("step_count", 1),
            action.priority,
            action.deadline.isoformat() if action.deadline else "",
            action.metadata.get("bucket", ""),
            action.metadata.get("submit_state", ""),
            action.expected_output,
            " | ".join(action.requires),
            " | ".join(action.next_actions),
            action.idempotency_key,
            generated_at.isoformat(),
        ])

    gate_rows = [["Gate ID", "Application ID", "Gate", "Result", "Hard", "Reason", "Evidence Refs"]]
    for gate in sorted(graph.gates.values(), key=lambda item: item.gate_id):
        gate_rows.append([
            gate.gate_id,
            gate.application_id,
            gate.name,
            gate.result.value.upper(),
            gate.hard,
            gate.reason,
            " | ".join(gate.evidence_refs),
        ])

    edge_rows = [["From", "Edge", "To", "Authority"]]
    for edge in atomic_edges(graph):
        edge_rows.append([edge["from"], edge["type"], edge["to"], edge["authority"]])

    frontier_header = [
        "Order", "Action ID", "Application ID", "Opportunity ID", "Title",
        "Action", "Priority", "Deadline", "Bucket", "Expected Output",
    ]
    human_rows = [frontier_header] + [
        _frontier_row(index, action)
        for index, action in enumerate(graph.human_frontier(generated_at), 1)
    ]
    agent_rows = [frontier_header] + [
        _frontier_row(index, action)
        for index, action in enumerate(graph.agent_frontier(generated_at), 1)
    ]
    system_rows = [frontier_header] + [
        _frontier_row(index, action)
        for index, action in enumerate(graph.system_frontier(generated_at), 1)
    ]
    waiting_rows = [frontier_header] + [
        _frontier_row(index, action)
        for index, action in enumerate(
            sorted(
                [action for action in graph.actions.values() if action.state.value == "WAITING"],
                key=lambda item: (-item.priority, item.action_id),
            ),
            1,
        )
    ]
    return {
        "Runtime_Actions": action_rows,
        "Runtime_Gates": gate_rows,
        "Runtime_Edges": edge_rows,
        "Human_Frontier": human_rows,
        "Agent_Frontier": agent_rows,
        "System_Frontier": system_rows,
        "Waiting_Frontier": waiting_rows,
    }


def snapshot_atomic(graph: RuntimeGraph, *, generated_at: datetime, source_revision: str) -> dict[str, Any]:
    base = graph.to_snapshot(generated_at=generated_at, source_revision=source_revision)
    base["edges"] = atomic_edges(graph)
    base["compiler"] = "atomic-runtime-compiler-v1"
    base["counts"] = {
        "applications": len({action.application_id for action in graph.actions.values()}),
        "actions": len(graph.actions),
        "gates": len(graph.gates),
        "human_ready": len(graph.human_frontier(generated_at)),
        "agent_ready": len(graph.agent_frontier(generated_at)),
        "system_ready": len(graph.system_frontier(generated_at)),
        "waiting": len([action for action in graph.actions.values() if action.state.value == "WAITING"]),
    }
    return base


def _frontier_row(index: int, action: ActionNode) -> list[Any]:
    return [
        index,
        action.action_id,
        action.application_id,
        action.metadata.get("opportunity_id", ""),
        action.metadata.get("title", ""),
        action.instruction,
        action.priority,
        action.deadline.isoformat() if action.deadline else "",
        action.metadata.get("bucket", ""),
        action.expected_output,
    ]
