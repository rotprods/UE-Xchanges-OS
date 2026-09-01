from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from ..human_command_center import command_center_rows
from ..runtime_graph import ActionNode
from .closed_loop import ClosedLoopRuntime
from .dispatcher import AutonomousEventDispatcher


@dataclass(frozen=True)
class ProjectionDocument:
    surface: str
    source_revision: str
    watermark: str
    generated_at: datetime
    rows: tuple[tuple[Any, ...], ...]

    def __post_init__(self) -> None:
        if not self.surface.strip() or not self.source_revision.strip() or not self.watermark.strip():
            raise ValueError("surface/source_revision/watermark must be non-empty")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if not self.rows:
            raise ValueError("projection rows must include at least a header")


@dataclass(frozen=True)
class ProjectedTodoistTask:
    runtime_action_id: str
    content: str
    description: str
    priority: str
    due: str | None
    labels: tuple[str, ...]


def build_projection_documents(
    *,
    runtime: ClosedLoopRuntime,
    dispatcher: AutonomousEventDispatcher,
    generated_at: datetime,
    source_revision: str,
    watermark: str,
    max_human: int = 5,
    max_agent: int = 100,
) -> dict[str, ProjectionDocument]:
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("generated_at must be timezone-aware")
    cards = runtime.human_frontier(now=generated_at, max_items=max_human)
    human_dict_rows = command_center_rows(cards)
    human_rows = _dict_rows(
        human_dict_rows,
        (
            "Order",
            "Application ID",
            "Title",
            "Action",
            "Estimated Minutes",
            "Priority",
            "Deadline",
            "Risk",
            "Expected Output",
            "Runtime Action ID",
        ),
    )

    agent_actions = runtime.agent_frontier(now=generated_at, max_items=max_agent)
    agent_rows: list[tuple[Any, ...]] = [
        (
            "Order",
            "Action ID",
            "Application ID",
            "Title",
            "Action Type",
            "Instruction",
            "Priority",
            "Deadline",
            "Expected Output",
            "State",
        )
    ]
    for index, action in enumerate(agent_actions, start=1):
        agent_rows.append(_agent_row(index, action))

    claim_rows: list[tuple[Any, ...]] = [
        (
            "Claim ID",
            "Application ID",
            "Claim Key",
            "Status",
            "Temporal Scope",
            "Required Role",
            "Evidence IDs",
            "Reason",
        )
    ]
    for claim_id, claim in sorted(runtime.claims.claims.items()):
        decision = runtime.claims.decisions.get(claim_id)
        claim_rows.append(
            (
                claim.claim_id,
                claim.application_id,
                claim.claim_key,
                decision.status.value if decision else "unverified",
                claim.temporal_scope.value,
                claim.required_role,
                " | ".join(claim.evidence_ids),
                decision.reason if decision else "No decision persisted.",
            )
        )

    dispatcher_snapshot = dispatcher.snapshot()
    dispatcher_rows: list[tuple[Any, ...]] = [
        ("Key", "Value"),
        ("source_revision", source_revision),
        ("watermark", watermark),
        ("seen_ingress_count", dispatcher_snapshot["seen_ingress_count"]),
        ("retrying_ingress_count", len(dispatcher_snapshot["retry_attempts"])),
        ("dead_letter_count", len(dispatcher_snapshot["dead_letters"])),
        ("human_ready", len(runtime.graph.human_frontier(generated_at))),
        ("agent_ready", len(runtime.graph.agent_frontier(generated_at))),
        ("system_ready", len(runtime.graph.system_frontier(generated_at))),
    ]

    cursor_rows: list[tuple[Any, ...]] = [
        (
            "Source ID",
            "High Watermark",
            "Last Source Item ID",
            "Last Observed At",
            "Revision",
        )
    ]
    for source_id, cursor in sorted(dispatcher_snapshot["source_cursors"].items()):
        cursor_rows.append(
            (
                source_id,
                cursor["high_watermark"],
                cursor["last_source_item_id"] or "",
                cursor["last_observed_at"] or "",
                cursor["revision"],
            )
        )

    dead_rows: list[tuple[Any, ...]] = [
        (
            "Ingress Key",
            "Source Ref",
            "Application Hint",
            "Reason",
            "Attempts",
            "Observed At",
        )
    ]
    for item in dispatcher_snapshot["dead_letters"]:
        dead_rows.append(
            (
                item["ingress_key"],
                item["source_ref"],
                item["application_hint"] or "",
                item["reason"],
                item["attempts"],
                item["observed_at"],
            )
        )

    command_rows: list[tuple[Any, ...]] = [
        ("RuntimeGraph V2 Command Center",),
        ("Authority", "DERIVED_ONLY"),
        ("Source Revision", source_revision),
        ("Watermark", watermark),
        ("Generated At", generated_at.isoformat()),
        ("Human Ready", len(cards)),
        ("Agent Ready", len(agent_actions)),
        ("Dead Letters", len(dispatcher_snapshot["dead_letters"])),
        ("Confirmed Receipt Evidence Refs", _receipt_ref_count(runtime)),
    ]

    return {
        surface: ProjectionDocument(
            surface=surface,
            source_revision=source_revision,
            watermark=watermark,
            generated_at=generated_at,
            rows=tuple(rows),
        )
        for surface, rows in {
            "Command_Center": command_rows,
            "Human_Now": human_rows,
            "Agent_Next": agent_rows,
            "Claim_Registry": claim_rows,
            "Dispatcher_State": dispatcher_rows,
            "Source_Cursors": cursor_rows,
            "Dead_Letters": dead_rows,
        }.items()
    }


def expected_todoist_tasks(
    *,
    runtime: ClosedLoopRuntime,
    now: datetime,
    max_items: int = 5,
) -> tuple[ProjectedTodoistTask, ...]:
    cards = runtime.human_frontier(now=now, max_items=max_items)
    output: list[ProjectedTodoistTask] = []
    for card in cards:
        output.append(
            ProjectedTodoistTask(
                runtime_action_id=card.action_id,
                content=f"RG HUMAN — {card.title}: {card.instruction}",
                description=(
                    f"Runtime action `{card.action_id}` for `{card.application_id}`. "
                    f"Expected evidence: {card.expected_output}. Todoist completion is never receipt/submission proof."
                ),
                priority=_todoist_priority(card.priority),
                due=card.deadline.isoformat() if card.deadline else None,
                labels=("uexchanges", "runtimegraph", "human_now"),
            )
        )
    return tuple(output)


def _dict_rows(records: Iterable[Mapping[str, Any]], header: tuple[str, ...]) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = [header]
    for record in records:
        rows.append(tuple(record.get(key, "") for key in header))
    return rows


def _agent_row(index: int, action: ActionNode) -> tuple[Any, ...]:
    return (
        index,
        action.action_id,
        action.application_id,
        str(action.metadata.get("title") or action.application_id),
        action.action_type,
        action.instruction,
        action.priority,
        action.deadline.isoformat() if action.deadline else "",
        action.expected_output,
        action.state.value,
    )


def _receipt_ref_count(runtime: ClosedLoopRuntime) -> int:
    return sum(1 for ref in runtime.graph.completed_evidence if str(ref).startswith("receipt:"))


def _todoist_priority(priority: int) -> str:
    if priority >= 90:
        return "p1"
    if priority >= 75:
        return "p2"
    if priority >= 60:
        return "p3"
    return "p4"
