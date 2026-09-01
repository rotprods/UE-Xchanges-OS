from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
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
    "SUBMIT", "PAY", "PAYMENT", "TRANSFER", "LOGIN", "AUTH", "PASSWORD",
    "2FA", "CAPTCHA", "RECORD_VIDEO", "RECORD AND EDIT", "APPLICANT_OWNED",
    "HUMAN_FINAL", "HUMAN REVIEW", "PERSONALLY_COMPLETE", "CONFIRM_AVAILABILITY",
    "CONFIRM_TRUE",
)
SYSTEM_TOKENS = (
    "RECOMPUTE_FRONTIER", "PROJECT_FRONTIER", "EMIT_EVENT", "RELEASE_LEASE",
    "TERMINAL_ARCHIVE",
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
            if action.state in {ActionState.DONE, ActionState.RUNNING, ActionState.FAILED, ActionState.WAITING}:
                continue
            state = ActionState.READY if all(self._requirement_satisfied(r) for r in action.requires) else ActionState.BLOCKED
            self.actions[action_id] = replace(action, state=state)

    def ready_actions(self, now: datetime, executor: ExecutorType | None = None) -> list[ActionNode]:
        self.recompute(now)
        ready = [a for a in self.actions.values() if a.state is ActionState.READY and (executor is None or a.executor is executor)]
        return sorted(ready, key=lambda a: (-a.priority, a.deadline or datetime.max.replace(tzinfo=timezone.utc), a.action_id))

    def claim(self, action_id: str, *, executor: ExecutorType, now: datetime) -> RuntimeEvent:
        _aware(now, "now"); self.recompute(now); action = self.actions[action_id]
        if action.executor is not executor: raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state is not ActionState.READY: raise RuntimeError(f"{action_id} is not READY")
        updated = replace(action, state=ActionState.RUNNING); self.actions[action_id] = updated
        return self._event(updated, "CLAIM", ActionState.READY, ActionState.RUNNING, executor, now)

    def complete(self, action_id: str, *, executor: ExecutorType, now: datetime, evidence_ref: str | None = None) -> RuntimeEvent:
        _aware(now, "now"); self.recompute(now); action = self.actions[action_id]
        if action.executor is not executor: raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state is ActionState.DONE: return self.events[-1]
        if action.state not in {ActionState.RUNNING, ActionState.READY}: raise RuntimeError(f"{action_id} cannot complete from {action.state.value}")
        if action.idempotency_key and action.idempotency_key in self.applied_idempotency_keys: return self.events[-1]
        updated = replace(action, state=ActionState.DONE); self.actions[action_id] = updated
        if action.idempotency_key: self.applied_idempotency_keys.add(action.idempotency_key)
        if evidence_ref: self.completed_evidence.add(evidence_ref)
        event = self._event(updated, "COMPLETE", action.state, ActionState.DONE, executor, now, evidence_ref=evidence_ref)
        self.recompute(now); return event

    def wait(self, action_id: str, *, executor: ExecutorType, now: datetime, reason: str) -> RuntimeEvent:
        _aware(now, "now"); action = self.actions[action_id]
        if action.executor is not executor: raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state not in {ActionState.READY, ActionState.RUNNING}: raise RuntimeError(f"{action_id} cannot wait from {action.state.value}")
        updated = replace(action, state=ActionState.WAITING, metadata={**dict(action.metadata), "wait_reason": reason}); self.actions[action_id] = updated
        return self._event(updated, "WAIT", action.state, ActionState.WAITING, executor, now)

    def resume_waiting(self, action_id: str, *, now: datetime) -> ActionNode:
        _aware(now, "now"); action = self.actions[action_id]
        if action.state is not ActionState.WAITING: raise RuntimeError(f"{action_id} is not WAITING")
        self.actions[action_id] = replace(action, state=ActionState.BLOCKED); self.recompute(now); return self.actions[action_id]

    def fail(self, action_id: str, *, executor: ExecutorType, now: datetime, reason: str) -> RuntimeEvent:
        _aware(now, "now"); action = self.actions[action_id]
        if action.executor is not executor: raise PermissionError(f"{action_id} requires {action.executor.value}")
        if action.state not in {ActionState.READY, ActionState.RUNNING, ActionState.WAITING}: raise RuntimeError(f"{action_id} cannot fail from {action.state.value}")
        updated = replace(action, state=ActionState.FAILED, metadata={**dict(action.metadata), "failure_reason": reason}); self.actions[action_id] = updated
        return self._event(updated, "FAIL", action.state, ActionState.FAILED, executor, now)

    def human_frontier(self, now: datetime) -> list[ActionNode]: return self.ready_actions(now, ExecutorType.HUMAN)
    def agent_frontier(self, now: datetime) -> list[ActionNode]: return self.ready_actions(now, ExecutorType.AGENT)
    def system_frontier(self, now: datetime) -> list[ActionNode]: return self.ready_actions(now, ExecutorType.SYSTEM)

    def to_snapshot(self, *, generated_at: datetime, source_revision: str) -> dict[str, Any]:
        _aware(generated_at, "generated_at"); self.recompute(generated_at)
        return {
            "schema_version": "1.0.0", "generated_at": generated_at.isoformat(), "source_revision": source_revision,
            "gates": [{**asdict(g), "result": g.result.value} for g in sorted(self.gates.values(), key=lambda g: g.gate_id)],
            "actions": [{**asdict(a), "executor": a.executor.value, "state": a.state.value, "deadline": a.deadline.isoformat() if a.deadline else None, "metadata": dict(a.metadata)} for a in sorted(self.actions.values(), key=lambda a: a.action_id)],
            "edges": runtime_edges(self),
            "frontiers": {
                "human": [a.action_id for a in self.human_frontier(generated_at)],
                "agent": [a.action_id for a in self.agent_frontier(generated_at)],
                "system": [a.action_id for a in self.system_frontier(generated_at)],
            },
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "RuntimeGraph":
        graph = cls()
        for raw in snapshot.get("gates", []):
            graph.add_gate(GateNode(raw["gate_id"], raw["application_id"], raw["name"], GateResult(raw["result"]), raw.get("reason", ""), tuple(raw.get("evidence_refs", ())), bool(raw.get("hard", True))))
        for raw in snapshot.get("actions", []):
            deadline = raw.get("deadline")
            graph.add_action(ActionNode(
                raw["action_id"], raw["application_id"], raw["action_type"], ExecutorType(raw["executor"]), raw["instruction"], raw["expected_output"],
                tuple(raw.get("requires", ())), tuple(raw.get("produces", ())), tuple(raw.get("next_actions", ())),
                datetime.fromisoformat(deadline) if deadline else None, int(raw.get("priority", 50)), ActionState(raw.get("state", "BLOCKED")),
                raw.get("idempotency_key", ""), raw.get("failure_route"), dict(raw.get("metadata", {})),
            ))
        return graph

    def _event(self, action: ActionNode, transition: str, before: ActionState, after: ActionState, executor: ExecutorType, now: datetime, evidence_ref: str | None = None) -> RuntimeEvent:
        raw = json.dumps([action.action_id, transition, now.isoformat(), action.idempotency_key, evidence_ref], sort_keys=True)
        event = RuntimeEvent("rgevt_" + hashlib.sha256(raw.encode()).hexdigest()[:24], now.isoformat(), action.action_id, transition, before, after, executor, action.idempotency_key, evidence_ref)
        self.events.append(event); return event


def classify_executor(next_action: str) -> ExecutorType:
    token = _normalise(next_action)
    if any(part in token for part in SYSTEM_TOKENS): return ExecutorType.SYSTEM
    if any(part in token for part in HUMAN_ONLY_TOKENS): return ExecutorType.HUMAN
    return ExecutorType.AGENT


def parse_gate_result(value: str | None) -> GateResult:
    token = _normalise(value or "")
    if not token: return GateResult.UNKNOWN
    fail_tokens = ("FAIL", "NOT_ELIGIBLE", "INELIGIBLE", "CLOSED", "DEADLINE_PASSED", "HARD_REQUIREMENT", "TERMINAL")
    unknown_tokens = ("UNKNOWN", "PENDING", "VERIFY", "QUERY", "UNRESOLVED", "MISSING", "TBD", "TO_VERIFY")
    pass_tokens = ("PASS", "CONFIRMED", "VERIFIED", "ELIGIBLE", "LISTED", "PRIVATE_GATE_PASS", "ROUTE_CONFIRMED", "PARTNER_CONFIRMED", "PROFILE_VERIFIED", "PUBLIC_PASS")
    if any(t in token for t in fail_tokens): return GateResult.FAIL
    if any(t in token for t in unknown_tokens): return GateResult.UNKNOWN
    if any(t in token for t in pass_tokens): return GateResult.PASS
    return GateResult.UNKNOWN


def compile_mass_apply_row(row: Mapping[str, Any]) -> RuntimeGraph:
    application_id = _required(row, "Application ID"); opportunity_id = _required(row, "Opportunity ID")
    next_action = str(row.get("Next Action") or "VERIFY_CURRENT_STATE"); deadline = _parse_deadline(row.get("Deadline")); graph = RuntimeGraph()
    gate_specs = (("spain", "Spain Gate", row.get("Spain Gate")), ("role", "Role Gate", row.get("Role Gate")), ("form_ai", "Infopack/Form/AI", row.get("Infopack/Form/AI")))
    gate_ids: list[str] = []
    for suffix, name, raw in gate_specs:
        gate_id = f"gate:{application_id}:{suffix}"; gate_ids.append(gate_id)
        graph.add_gate(GateNode(gate_id, application_id, name, parse_gate_result(str(raw or "")), str(raw or "")))
    submit_state = str(row.get("Submit State") or "").upper()
    if any(t in submit_state for t in ("CLOSED", "HARD_FAIL", "TERMINAL")):
        action_type = "TERMINAL_ARCHIVE"; executor = ExecutorType.SYSTEM; instruction = "Preserve terminal evidence; do not submit."; initial_state = ActionState.BLOCKED
    else:
        action_type = next_action; executor = classify_executor(next_action); instruction = next_action.replace("_", " ").replace(";", " →").strip().title(); initial_state = _initial_action_state(next_action, submit_state)
    action_id = f"action:{application_id}:next"
    graph.add_action(ActionNode(
        action_id, application_id, action_type, executor, instruction, _expected_output(action_type),
        _requirements_for_action(action_type, executor, tuple(gate_ids)), (f"state:{application_id}:advanced",), (), deadline,
        _priority(row), initial_state, stable_idempotency_key(application_id, action_type, submit_state, str(deadline or "")), None,
        {"queue_id": str(row.get("Queue ID") or ""), "opportunity_id": opportunity_id, "title": str(row.get("Title") or ""), "provider": str(row.get("Provider") or ""), "role": str(row.get("Role") or ""), "bucket": str(row.get("Bucket") or ""), "submit_state": str(row.get("Submit State") or ""), "spain_gate_raw": str(row.get("Spain Gate") or ""), "role_gate_raw": str(row.get("Role Gate") or ""), "form_ai_raw": str(row.get("Infopack/Form/AI") or "")}
    ))
    graph.recompute(datetime.now(timezone.utc)); return graph


def compile_mass_apply_rows(rows: Iterable[Mapping[str, Any]]) -> RuntimeGraph:
    return merge_runtime_graphs(compile_mass_apply_row(row) for row in rows)


def merge_runtime_graphs(graphs: Iterable[RuntimeGraph]) -> RuntimeGraph:
    merged = RuntimeGraph()
    for graph in graphs:
        for gate in graph.gates.values():
            if gate.gate_id in merged.gates and merged.gates[gate.gate_id] != gate: raise ValueError(f"conflicting compiled gate: {gate.gate_id}")
            merged.gates[gate.gate_id] = gate
        for action in graph.actions.values():
            if action.action_id in merged.actions: raise ValueError(f"duplicate compiled action: {action.action_id}")
            merged.actions[action.action_id] = action
    return merged


def runtime_edges(graph: RuntimeGraph) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    for action in sorted(graph.actions.values(), key=lambda a: a.action_id):
        opportunity_id = str(action.metadata.get("opportunity_id") or "")
        if opportunity_id: seen.add((f"opportunity:{opportunity_id}", "HAS_APPLICATION", f"application:{action.application_id}"))
        seen.add((f"application:{action.application_id}", "HAS_NEXT_ACTION", action.action_id))
        for requirement in action.requires: seen.add((requirement, "UNLOCKS", action.action_id))
    for gate in sorted(graph.gates.values(), key=lambda g: g.gate_id): seen.add((f"application:{gate.application_id}", "HAS_GATE", gate.gate_id))
    return [{"from": s, "type": t, "to": o, "authority": "derived_runtime_projection", "source_ref": None} for s, t, o in sorted(seen)]


def projection_rows(graph: RuntimeGraph, *, generated_at: datetime) -> dict[str, list[list[Any]]]:
    _aware(generated_at, "generated_at"); graph.recompute(generated_at)
    action_rows = [["Action ID","Application ID","Opportunity ID","Title","Executor","Action Type","Runtime State","Priority","Deadline","Bucket","Submit State","Expected Output","Requires","Idempotency Key","Generated At"]]
    for a in sorted(graph.actions.values(), key=lambda x: (-x.priority, x.action_id)):
        action_rows.append([a.action_id,a.application_id,a.metadata.get("opportunity_id",""),a.metadata.get("title",""),a.executor.value,a.action_type,a.state.value,a.priority,a.deadline.isoformat() if a.deadline else "",a.metadata.get("bucket",""),a.metadata.get("submit_state",""),a.expected_output," | ".join(a.requires),a.idempotency_key,generated_at.isoformat()])
    gate_rows = [["Gate ID","Application ID","Gate","Result","Hard","Reason","Evidence Refs"]] + [[g.gate_id,g.application_id,g.name,g.result.value.upper(),g.hard,g.reason," | ".join(g.evidence_refs)] for g in sorted(graph.gates.values(), key=lambda x: x.gate_id)]
    edge_rows = [["From","Edge","To","Authority"]] + [[e["from"],e["type"],e["to"],e["authority"]] for e in runtime_edges(graph)]
    header = ["Order","Action ID","Application ID","Opportunity ID","Title","Action","Priority","Deadline","Bucket","Expected Output"]
    human_rows = [header] + [_frontier_row(i,a) for i,a in enumerate(graph.human_frontier(generated_at),1)]
    agent_rows = [header] + [_frontier_row(i,a) for i,a in enumerate(graph.agent_frontier(generated_at),1)]
    system_rows = [header] + [_frontier_row(i,a) for i,a in enumerate(graph.system_frontier(generated_at),1)]
    return {"Runtime_Actions":action_rows,"Runtime_Gates":gate_rows,"Runtime_Edges":edge_rows,"Human_Frontier":human_rows,"Agent_Frontier":agent_rows,"System_Frontier":system_rows}


def stable_idempotency_key(*parts: str) -> str:
    raw = json.dumps(parts, ensure_ascii=False, separators=(",", ":")); return "rgidem_" + hashlib.sha256(raw.encode()).hexdigest()


def _requirements_for_action(action_type: str, executor: ExecutorType, gate_ids: tuple[str, ...]) -> tuple[str, ...]:
    token = _normalise(action_type)
    if "TERMINAL_ARCHIVE" in token or executor in {ExecutorType.AGENT, ExecutorType.SYSTEM}: return ()
    if any(t in token for t in ("LOGIN", "AUTH", "CAPTCHA", "2FA")): return ()
    if any(t in token for t in ("PAY", "PAYMENT", "TRANSFER")): return gate_ids[:2]
    if any(t in token for t in ("RECORD", "VIDEO", "HUMAN_FINAL", "HUMAN REVIEW", "PERSONALLY_COMPLETE")) and "SUBMIT" not in token: return gate_ids[:2]
    if "SUBMIT" in token: return gate_ids
    return gate_ids[:2]


def _initial_action_state(next_action: str, submit_state: str) -> ActionState:
    token = _normalise(next_action + " " + submit_state)
    if any(t in token for t in ("WAITING_EXTERNAL", "WAIT_HOST", "WAIT_ORGANISER", "WAIT_REPLY", "HOLD_EXTERNAL")): return ActionState.WAITING
    return ActionState.BLOCKED


def _expected_output(action_type: str) -> str:
    token = _normalise(action_type)
    if "SUBMIT" in token: return "submission_receipt_or_authoritative_confirmation"
    if "PAY" in token or "TRANSFER" in token: return "payment_receipt_and_terms"
    if any(t in token for t in ("VERIFY", "EXTRACT", "CAPTURE", "INGEST", "RETRIEVE", "RESOLVE")): return "source_backed_evidence_and_recomputed_gates"
    if "VIDEO" in token: return "applicant_owned_video_asset"
    if "ARCHIVE" in token: return "terminal_state_preserved_with_evidence"
    return "verified_state_transition_evidence"


def _priority(row: Mapping[str, Any]) -> int:
    bucket = str(row.get("Bucket") or "").upper()
    if bucket.startswith("T0"): return 100
    if bucket.startswith("T1"): return 90
    if bucket.startswith("T2"): return 75
    if bucket.startswith("T3"): return 60
    return 50


def _parse_deadline(raw: Any) -> datetime | None:
    if raw is None: return None
    value = str(raw).strip()
    if not value or value.upper() in {"ASAP", "ROLLING", "UNKNOWN"} or "ROLLING" in value.upper(): return None
    if value.replace(".", "", 1).isdigit(): return None
    value = value.replace(" 23:59:00", "T23:59:00")
    try: parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try: parsed = datetime.fromisoformat(value + "T23:59:00+02:00")
        except ValueError: return None
    if parsed.tzinfo is None or parsed.utcoffset() is None: parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _frontier_row(index: int, action: ActionNode) -> list[Any]:
    return [index,action.action_id,action.application_id,action.metadata.get("opportunity_id",""),action.metadata.get("title",""),action.instruction,action.priority,action.deadline.isoformat() if action.deadline else "",action.metadata.get("bucket",""),action.expected_output]


def _required(row: Mapping[str, Any], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value: raise ValueError(f"missing required row field: {key}")
    return value


def _normalise(value: str) -> str: return (value or "").upper().replace("-", "_")

def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None: raise ValueError(f"{name} must be timezone-aware")
    return value
