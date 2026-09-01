from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from .projections import ProjectedTodoistTask, ProjectionDocument


DERIVED_SURFACES = frozenset(
    {
        "Command_Center",
        "Human_Now",
        "Agent_Next",
        "Claim_Registry",
        "Dispatcher_State",
        "Source_Cursors",
        "Dead_Letters",
    }
)

CANONICAL_SURFACES = frozenset(
    {
        "Opportunities",
        "Applications",
        "Mass_Apply_Queue",
        "Execution_Log",
        "Agent_Event_Bus",
        "Agent_Sessions",
        "Work_Leases",
        "Autofill_Profile",
        "Human_Gates",
    }
)


class ProjectionHealthStatus(str, Enum):
    HEALTHY = "healthy"
    MISSING = "missing"
    DRIFTED = "drifted"
    STALE = "stale"


class ProjectionRepairAction(str, Enum):
    CREATE_DERIVED_SURFACE = "create_derived_surface"
    REPLACE_DERIVED_ROWS = "replace_derived_rows"


class TodoistRepairAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    RETIRE = "retire"


@dataclass(frozen=True)
class ProjectionHealth:
    surface: str
    status: ProjectionHealthStatus
    expected_fingerprint: str
    actual_fingerprint: str | None
    reason: str


@dataclass(frozen=True)
class ProjectionRepair:
    surface: str
    action: ProjectionRepairAction
    expected_fingerprint: str
    expected_row_count: int
    source_revision: str
    watermark: str


@dataclass(frozen=True)
class ProjectionRepairPlan:
    health: tuple[ProjectionHealth, ...]
    repairs: tuple[ProjectionRepair, ...]

    @property
    def healthy(self) -> bool:
        return not self.repairs


@dataclass(frozen=True)
class ObservedTodoistTask:
    task_id: str
    runtime_action_id: str
    content: str
    description: str
    priority: str
    due: str | None
    labels: tuple[str, ...]


@dataclass(frozen=True)
class TodoistRepair:
    action: TodoistRepairAction
    runtime_action_id: str
    task_id: str | None
    expected: ProjectedTodoistTask | None
    reason: str


def projection_fingerprint(document: ProjectionDocument) -> str:
    payload = {
        "surface": document.surface,
        "rows": _jsonable(document.rows),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def assess_projection(
    *,
    expected: ProjectionDocument,
    actual: ProjectionDocument | None,
) -> ProjectionHealth:
    _assert_derived(expected.surface)
    expected_fp = projection_fingerprint(expected)
    if actual is None:
        return ProjectionHealth(
            expected.surface,
            ProjectionHealthStatus.MISSING,
            expected_fp,
            None,
            "Derived projection is missing.",
        )
    if actual.surface != expected.surface:
        raise ValueError("expected/actual projection surfaces differ")
    actual_fp = projection_fingerprint(actual)
    if actual.source_revision != expected.source_revision or actual.watermark != expected.watermark:
        return ProjectionHealth(
            expected.surface,
            ProjectionHealthStatus.STALE,
            expected_fp,
            actual_fp,
            "Projection revision/watermark is stale relative to RuntimeGraph authority inputs.",
        )
    if actual_fp != expected_fp:
        return ProjectionHealth(
            expected.surface,
            ProjectionHealthStatus.DRIFTED,
            expected_fp,
            actual_fp,
            "Projection rows differ from the deterministic expected read model.",
        )
    return ProjectionHealth(
        expected.surface,
        ProjectionHealthStatus.HEALTHY,
        expected_fp,
        actual_fp,
        "Projection matches expected rows and authority watermark.",
    )


def build_projection_repair_plan(
    *,
    expected: Mapping[str, ProjectionDocument],
    actual: Mapping[str, ProjectionDocument],
) -> ProjectionRepairPlan:
    health_items: list[ProjectionHealth] = []
    repairs: list[ProjectionRepair] = []
    for surface in sorted(expected):
        _assert_derived(surface)
        expected_doc = expected[surface]
        item = assess_projection(expected=expected_doc, actual=actual.get(surface))
        health_items.append(item)
        if item.status is ProjectionHealthStatus.HEALTHY:
            continue
        action = (
            ProjectionRepairAction.CREATE_DERIVED_SURFACE
            if item.status is ProjectionHealthStatus.MISSING
            else ProjectionRepairAction.REPLACE_DERIVED_ROWS
        )
        repairs.append(
            ProjectionRepair(
                surface=surface,
                action=action,
                expected_fingerprint=item.expected_fingerprint,
                expected_row_count=len(expected_doc.rows),
                source_revision=expected_doc.source_revision,
                watermark=expected_doc.watermark,
            )
        )
    return ProjectionRepairPlan(tuple(health_items), tuple(repairs))


def build_todoist_repair_plan(
    *,
    expected: Iterable[ProjectedTodoistTask],
    actual: Iterable[ObservedTodoistTask],
) -> tuple[TodoistRepair, ...]:
    expected_by_id = {task.runtime_action_id: task for task in expected}
    actual_by_id: dict[str, ObservedTodoistTask] = {}
    for task in actual:
        if task.runtime_action_id in actual_by_id:
            raise ValueError(f"duplicate Todoist runtime_action_id: {task.runtime_action_id}")
        actual_by_id[task.runtime_action_id] = task

    repairs: list[TodoistRepair] = []
    for runtime_action_id, task in sorted(expected_by_id.items()):
        observed = actual_by_id.get(runtime_action_id)
        if observed is None:
            repairs.append(
                TodoistRepair(
                    TodoistRepairAction.CREATE,
                    runtime_action_id,
                    None,
                    task,
                    "READY human runtime action has no Todoist projection.",
                )
            )
            continue
        if not _todoist_matches(task, observed):
            repairs.append(
                TodoistRepair(
                    TodoistRepairAction.UPDATE,
                    runtime_action_id,
                    observed.task_id,
                    task,
                    "Todoist projection drifted from current Human Frontier.",
                )
            )

    for runtime_action_id, observed in sorted(actual_by_id.items()):
        if runtime_action_id not in expected_by_id:
            repairs.append(
                TodoistRepair(
                    TodoistRepairAction.RETIRE,
                    runtime_action_id,
                    observed.task_id,
                    None,
                    "Todoist human task is stale because the runtime action is no longer READY.",
                )
            )
    return tuple(repairs)


def _todoist_matches(expected: ProjectedTodoistTask, actual: ObservedTodoistTask) -> bool:
    return (
        expected.content == actual.content
        and expected.description == actual.description
        and expected.priority == actual.priority
        and expected.due == actual.due
        and tuple(expected.labels) == tuple(actual.labels)
    )


def _assert_derived(surface: str) -> None:
    if surface in CANONICAL_SURFACES:
        raise ValueError(f"self-heal is forbidden on canonical surface: {surface}")
    if surface not in DERIVED_SURFACES:
        raise ValueError(f"surface is not registered as derived: {surface}")


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
