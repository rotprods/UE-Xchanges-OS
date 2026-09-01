from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from ..models import GateResult
from ..runtime_graph import ActionState, ExecutorType, RuntimeGraph
from .models import RuntimeDomainEvent, RuntimeEventKind


@dataclass(frozen=True)
class RuntimeDelta:
    event_id: str
    application_id: str
    duplicate: bool
    changed_gates: tuple[str, ...] = ()
    changed_actions: tuple[str, ...] = ()
    evidence_refs_added: tuple[str, ...] = ()


class IncrementalRuntimeReducer:
    """Apply normalized domain events to only the affected application subgraph."""

    def __init__(self) -> None:
        self.seen_idempotency_keys: set[str] = set()
        self.application_revisions: dict[str, int] = {}
        self.last_event_id: str | None = None

    def apply(self, graph: RuntimeGraph, event: RuntimeDomainEvent) -> RuntimeDelta:
        if event.idempotency_key in self.seen_idempotency_keys:
            return RuntimeDelta(event.event_id, event.application_id, True)

        changed_gates: list[str] = []
        changed_actions: list[str] = []
        evidence_added: list[str] = []

        if event.kind is RuntimeEventKind.GATE_RESOLVED:
            gate_name = _required_payload(event, "gate_name")
            result = GateResult(str(_required_payload(event, "result")).lower())
            reason = str(event.payload.get("reason") or event.source_ref)
            candidates = [
                gate
                for gate in graph.gates.values()
                if gate.application_id == event.application_id
                and gate.name.casefold() == str(gate_name).casefold()
            ]
            if len(candidates) != 1:
                raise ValueError(
                    f"expected one gate for {event.application_id}/{gate_name}; got {len(candidates)}"
                )
            gate = candidates[0]
            refs = tuple(dict.fromkeys((*gate.evidence_refs, event.source_ref)))
            graph.gates[gate.gate_id] = replace(
                gate,
                result=result,
                reason=reason,
                evidence_refs=refs,
            )
            changed_gates.append(gate.gate_id)

        elif event.kind is RuntimeEventKind.EVIDENCE_ADDED:
            evidence_ref = str(event.payload.get("evidence_ref") or event.source_ref)
            graph.completed_evidence.add(evidence_ref)
            evidence_added.append(evidence_ref)

        elif event.kind is RuntimeEventKind.ACTION_COMPLETED:
            action_id = str(_required_payload(event, "action_id"))
            action = graph.actions[action_id]
            if action.application_id != event.application_id:
                raise ValueError("action belongs to a different application")
            executor = ExecutorType(str(_required_payload(event, "executor")).upper())
            evidence_ref = str(event.payload.get("evidence_ref") or event.source_ref)
            graph.complete(
                action_id,
                executor=executor,
                now=event.occurred_at,
                evidence_ref=evidence_ref,
            )
            changed_actions.append(action_id)
            evidence_added.append(evidence_ref)

        elif event.kind is RuntimeEventKind.DEADLINE_UPDATED:
            deadline = _parse_datetime(_required_payload(event, "deadline"))
            for action_id, action in tuple(graph.actions.items()):
                if action.application_id != event.application_id:
                    continue
                graph.actions[action_id] = replace(action, deadline=deadline)
                changed_actions.append(action_id)

        elif event.kind is RuntimeEventKind.RECEIPT_CONFIRMED:
            receipt_ref = str(_required_payload(event, "receipt_ref"))
            graph.completed_evidence.add(receipt_ref)
            evidence_added.append(receipt_ref)
            action_id = event.payload.get("verification_action_id")
            if action_id:
                action = graph.actions[str(action_id)]
                if action.application_id != event.application_id:
                    raise ValueError("receipt verification action belongs to another application")
                executor = ExecutorType(str(event.payload.get("executor") or "AGENT").upper())
                if action.state in {ActionState.READY, ActionState.RUNNING}:
                    graph.complete(
                        str(action_id),
                        executor=executor,
                        now=event.occurred_at,
                        evidence_ref=receipt_ref,
                    )
                    changed_actions.append(str(action_id))

        elif event.kind is RuntimeEventKind.OUTCOME_RECORDED:
            evidence_ref = str(event.payload.get("evidence_ref") or event.source_ref)
            graph.completed_evidence.add(evidence_ref)
            evidence_added.append(evidence_ref)

        else:
            raise ValueError(f"unsupported event kind: {event.kind.value}")

        graph.recompute(event.occurred_at)
        self.seen_idempotency_keys.add(event.idempotency_key)
        self.application_revisions[event.application_id] = (
            self.application_revisions.get(event.application_id, 0) + 1
        )
        self.last_event_id = event.event_id
        return RuntimeDelta(
            event.event_id,
            event.application_id,
            False,
            tuple(changed_gates),
            tuple(changed_actions),
            tuple(evidence_added),
        )

    def revision(self, application_id: str) -> int:
        return self.application_revisions.get(application_id, 0)


def _required_payload(event: RuntimeDomainEvent, key: str):
    if key not in event.payload or event.payload[key] in (None, ""):
        raise ValueError(f"{event.kind.value} requires payload.{key}")
    return event.payload[key]


def _parse_datetime(value) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("deadline must be timezone-aware")
    return parsed
