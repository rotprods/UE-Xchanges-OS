from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping

from .models import GateResult


class ExecutorType(str, Enum):
    AGENT = "AGENT"
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


class ActionState(str, Enum):
    BLOCKED = "BLOCKED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    DONE = "DONE"
    FAILED = "FAILED"


HUMAN_ONLY_TOKENS = (
    "SUBMIT",
    "PAY",
    "PAYMENT",
    "TRANSFER",
    "LOGIN",
    "AUTH",
    "PASSWORD",
    "2FA",
    "CAPTCHA",
    "RECORD_VIDEO",
    "RECORD AND EDIT",
    "APPLICANT_OWNED",
    "HUMAN_FINAL",
    "HUMAN REVIEW",
    "PERSONALLY_COMPLETE",
    "CONFIRM_AVAILABILITY",
)

SYSTEM_TOKENS = (
    "RECOMPUTE_FRONTIER",
    "PROJECT_FRONTIER",
    "EMIT_EVENT",
    "RELEASE_LEASE",
)


@dataclass(frozen=True)
class GateNode:
    gate_id: str
    application_id: str
    name: str
    result: GateResult
    reason: str = ""
    evidence_refs: tuple[str, ...] = ()
    hard: bool = True

    @property
    def passable(self) -> bool:
        return self.result is GateResult.PASS or not self.hard


@dataclass(frozen=True)
class ActionNode:
    action_id: str
    application_id: str
    action_type: str
    executor: ExecutorType
    instruction: str
    expected_output: str
    requires: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    deadline: datetime | None = None
    priority: int = 50
    state: ActionState = ActionState.BLOCKED
    idempotency_key: str = ""
    failure_route: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.deadline is not None and (
            self.deadline.tzinfo is None or self.deadline.utcoffset() is None
        ):
            raise ValueError("deadline must be timezone-aware")
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    occurred_at: str
    action_id: str
    transition: str
    state_before: ActionState
    state_after: ActionState
    executor: ExecutorType
    idempotency_key: str
    evidence_ref: str | None = None


@dataclass
class RuntimeGraph:
    gates: dict[str, GateNode] = field(default_factory=dict)
    actions: dict[str, ActionNode] = field(default_factory=dict)
    completed_evidence: set[str] = field(default_factory=set)
    applied_idempotency_keys: set[str] = field(default_factory=set)
    events: list[RuntimeEvent] = field(default_factory=list)

    def add_gate(self, gate: GateNode) -> None:
        self.gates[gate.gate_id] = gate

    def add_action(self, action: ActionNode) -> None:
        if action.action_id in self.actions:
            raise ValueError(f"duplicate action_id: {action.action_id}")
        self.actions[action.action_id] = action

    def _requirement_satisfied(self, requirement: str) -> bool:
        if requirement in self.gates:
            return self.gates[requirement].passable
        if requirement in self.actions:
            return self.actions[requirement].state is ActionState.DONE
        return requirement in self.completed_evidence

    def recompute(self, now: datetime) -> None:
        _aware(now, "now")
        for action_id, action in tuple(self.actions.items()):
            if action.state in {
                ActionState.DONE,
                ActionState.RUNNING,
                ActionState.FAILED,
                ActionState.WAITING,
            }:
                continue
            state = (
                ActionState.READY
                if all(self._requirement_satisfied(r) for r in action.requires)
                else ActionState.BLOCKED
            )
            self.actions[action_id] = replace(action, state=state)

    def ready_actions(
        self, now: datetime, executor: ExecutorType | None = None
    ) -> list[ActionNode]:
        self.recompute(now)
        ready = [
            a
            for a in self.actions.values()
            if a.state is ActionState.READY
            and (executor is None or a.executor is executor)
        ]
        return sorted(
            ready,
            key=lambda a: (
                -a.priority,
                a.deadline or datetime.max.replace(tzinfo=timezone.utc),
                a.action_id,
            ),
        )

    def claim(
        self, action_id: str, *, executor: ExecutorType, now: datetime
    ) -> RuntimeEvent:
        _aware(now, "now")
        self.recompute(now)
        action = self.actions[action_id]
        if action.executor is not executor:
            raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state is not ActionState.READY:
            raise RuntimeError(f"{action_id} is not READY")
        updated = replace(action, state=ActionState.RUNNING)
        self.actions[action_id] = updated
        return self._event(
            updated,
            "CLAIM",
            ActionState.READY,
            ActionState.RUNNING,
            executor,
            now,
        )

    def complete(
        self,
        action_id: str,
        *,
        executor: ExecutorType,
        now: datetime,
        evidence_ref: str | None = None,
    ) -> RuntimeEvent:
        _aware(now, "now")
        self.recompute(now)
        action = self.actions[action_id]
        if action.executor is not executor:
            raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state is ActionState.DONE:
            return self.events[-1]
        if action.state not in {ActionState.RUNNING, ActionState.READY}:
            raise RuntimeError(
                f"{action_id} cannot complete from {action.state.value}"
            )
        if (
            action.idempotency_key
            and action.idempotency_key in self.applied_idempotency_keys
        ):
            return self.events[-1]
        updated = replace(action, state=ActionState.DONE)
        self.actions[action_id] = updated
        if action.idempotency_key:
            self.applied_idempotency_keys.add(action.idempotency_key)
        if evidence_ref:
            self.completed_evidence.add(evidence_ref)
        event = self._event(
            updated,
            "COMPLETE",
            action.state,
            ActionState.DONE,
            executor,
            now,
            evidence_ref=evidence_ref,
        )
        self.recompute(now)
        return event

    def wait(
        self,
        action_id: str,
        *,
        executor: ExecutorType,
        now: datetime,
        reason: str,
    ) -> RuntimeEvent:
        _aware(now, "now")
        action = self.actions[action_id]
        if action.executor is not executor:
            raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state not in {ActionState.READY, ActionState.RUNNING}:
            raise RuntimeError(
                f"{action_id} cannot wait from {action.state.value}"
            )
        updated = replace(
            action,
            state=ActionState.WAITING,
            metadata={**dict(action.metadata), "wait_reason": reason},
        )
        self.actions[action_id] = updated
        return self._event(
            updated,
            "WAIT",
            action.state,
            ActionState.WAITING,
            executor,
            now,
        )

    def fail(
        self,
        action_id: str,
        *,
        executor: ExecutorType,
        now: datetime,
        reason: str,
    ) -> RuntimeEvent:
        _aware(now, "now")
        action = self.actions[action_id]
        if action.executor is not executor:
            raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state not in {
            ActionState.READY,
            ActionState.RUNNING,
            ActionState.WAITING,
        }:
            raise RuntimeError(
                f"{action_id} cannot fail from {action.state.value}"
            )
        updated = replace(
            action,
            state=ActionState.FAILED,
            metadata={**dict(action.metadata), "failure_reason": reason},
        )
        self.actions[action_id] = updated
        return self._event(
            updated,
            "FAIL",
            action.state,
            ActionState.FAILED,
            executor,
            now,
        )

    def human_frontier(self, now: datetime) -> list[ActionNode]:
        return self.ready_actions(now, ExecutorType.HUMAN)

    def agent_frontier(self, now: datetime) -> list[ActionNode]:
        return self.ready_actions(now, ExecutorType.AGENT)

    def _event(
        self,
        action: ActionNode,
        transition: str,
        before: ActionState,
        after: ActionState,
        executor: ExecutorType,
        now: datetime,
        evidence_ref: str | None = None,
    ) -> RuntimeEvent:
        raw = json.dumps(
            [
                action.action_id,
                transition,
                now.isoformat(),
                action.idempotency_key,
                evidence_ref,
            ],
            sort_keys=True,
        )
        event = RuntimeEvent(
            event_id="rgevt_" + hashlib.sha256(raw.encode()).hexdigest()[:24],
            occurred_at=now.isoformat(),
            action_id=action.action_id,
            transition=transition,
            state_before=before,
            state_after=after,
            executor=executor,
            idempotency_key=action.idempotency_key,
            evidence_ref=evidence_ref,
        )
        self.events.append(event)
        return event


def classify_executor(next_action: str) -> ExecutorType:
    token = (next_action or "").upper().replace("-", "_")
    if any(part in token for part in SYSTEM_TOKENS):
        return ExecutorType.SYSTEM
    if any(part in token for part in HUMAN_ONLY_TOKENS):
        return ExecutorType.HUMAN
    return ExecutorType.AGENT


def parse_gate_result(value: str | None) -> GateResult:
    token = (value or "").strip().upper()
    if not token:
        return GateResult.UNKNOWN
    fail_tokens = (
        "FAIL",
        "NOT_ELIGIBLE",
        "INELIGIBLE",
        "CLOSED",
        "DEADLINE_PASSED",
        "HARD_REQUIREMENT",
    )
    unknown_tokens = (
        "UNKNOWN",
        "PENDING",
        "VERIFY",
        "QUERY",
        "UNRESOLVED",
        "MISSING",
        "TBD",
    )
    pass_tokens = (
        "PASS",
        "CONFIRMED",
        "VERIFIED",
        "ELIGIBLE",
        "PRIVATE_GATE_PASS",
    )
    if any(t in token for t in fail_tokens):
        return GateResult.FAIL
    if any(t in token for t in unknown_tokens):
        return GateResult.UNKNOWN
    if any(t in token for t in pass_tokens):
        return GateResult.PASS
    return GateResult.UNKNOWN


def compile_mass_apply_row(row: Mapping[str, Any]) -> RuntimeGraph:
    """Compile one Mass_Apply_Queue row into a minimal executable subgraph."""
    application_id = _required(row, "Application ID")
    opportunity_id = _required(row, "Opportunity ID")
    next_action = str(row.get("Next Action") or "VERIFY_CURRENT_STATE")
    deadline = _parse_deadline(row.get("Deadline"))

    graph = RuntimeGraph()
    gate_specs = (
        ("spain", "Spain Gate", row.get("Spain Gate")),
        ("role", "Role Gate", row.get("Role Gate")),
        ("form_ai", "Infopack/Form/AI", row.get("Infopack/Form/AI")),
    )
    gate_ids: list[str] = []
    for suffix, name, raw in gate_specs:
        gate_id = f"gate:{application_id}:{suffix}"
        gate_ids.append(gate_id)
        graph.add_gate(
            GateNode(
                gate_id=gate_id,
                application_id=application_id,
                name=name,
                result=parse_gate_result(str(raw or "")),
                reason=str(raw or ""),
            )
        )

    submit_state = str(row.get("Submit State") or "").upper()
    if any(t in submit_state for t in ("CLOSED", "HARD_FAIL", "TERMINAL")):
        action_type = "TERMINAL_ARCHIVE"
        executor = ExecutorType.SYSTEM
        instruction = "Preserve terminal evidence; do not submit."
    else:
        action_type = next_action
        executor = classify_executor(next_action)
        instruction = next_action.replace("_", " ").strip().title()

    action_id = f"action:{application_id}:next"
    graph.add_action(
        ActionNode(
            action_id=action_id,
            application_id=application_id,
            action_type=action_type,
            executor=executor,
            instruction=instruction,
            expected_output=_expected_output(action_type),
            requires=tuple(gate_ids),
            produces=(f"state:{application_id}:advanced",),
            deadline=deadline,
            priority=_priority(row),
            idempotency_key=stable_idempotency_key(
                application_id,
                action_type,
                submit_state,
                str(deadline or ""),
            ),
            metadata={
                "opportunity_id": opportunity_id,
                "title": str(row.get("Title") or ""),
                "provider": str(row.get("Provider") or ""),
                "bucket": str(row.get("Bucket") or ""),
                "submit_state": str(row.get("Submit State") or ""),
            },
        )
    )
    graph.recompute(datetime.now(timezone.utc))
    return graph


def merge_runtime_graphs(graphs: Iterable[RuntimeGraph]) -> RuntimeGraph:
    merged = RuntimeGraph()
    for graph in graphs:
        for gate in graph.gates.values():
            merged.gates[gate.gate_id] = gate
        for action in graph.actions.values():
            if action.action_id in merged.actions:
                raise ValueError(f"duplicate compiled action: {action.action_id}")
            merged.actions[action.action_id] = action
    return merged


def stable_idempotency_key(*parts: str) -> str:
    raw = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return "rgidem_" + hashlib.sha256(raw.encode()).hexdigest()


def _expected_output(action_type: str) -> str:
    token = action_type.upper()
    if "SUBMIT" in token:
        return "submission_receipt_or_authoritative_confirmation"
    if "PAY" in token or "TRANSFER" in token:
        return "payment_receipt_and_terms"
    if any(t in token for t in ("VERIFY", "EXTRACT", "CAPTURE", "INGEST")):
        return "source_backed_evidence_and_recomputed_gates"
    if "VIDEO" in token:
        return "applicant_owned_video_asset"
    return "verified_state_transition_evidence"


def _priority(row: Mapping[str, Any]) -> int:
    bucket = str(row.get("Bucket") or "").upper()
    if bucket.startswith("T0"):
        return 100
    if bucket.startswith("T1"):
        return 90
    if bucket.startswith("T2"):
        return 75
    if bucket.startswith("T3"):
        return 60
    return 50


def _parse_deadline(raw: Any) -> datetime | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value or value.upper() in {"ASAP", "ROLLING", "UNKNOWN"}:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value + "T23:59:00+02:00")
        except ValueError:
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _required(row: Mapping[str, Any], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"missing required row field: {key}")
    return value


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value
