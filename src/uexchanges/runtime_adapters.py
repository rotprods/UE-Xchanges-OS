from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Iterable, Mapping

from .coordination import (
    AgentEvent,
    AgentSession,
    EventApplyDecision,
    WorkLease,
    create_agent_event,
    evaluate_event_application,
)
from .models import GateResult
from .runtime_graph import ActionNode, ExecutorType, GateNode, RuntimeGraph


@dataclass(frozen=True)
class EvidenceSignal:
    application_id: str
    gate_name: str
    result: GateResult
    reason: str
    source_ref: str
    source_version: str


@dataclass(frozen=True)
class RuntimeMutationAuthorization:
    allowed: bool
    reason: str
    event: AgentEvent
    decision: EventApplyDecision


def apply_evidence_signal(graph: RuntimeGraph, signal: EvidenceSignal) -> GateNode:
    """Apply normalized external evidence to one existing gate without guessing NLP facts."""
    candidates = [
        gate
        for gate in graph.gates.values()
        if gate.application_id == signal.application_id
        and gate.name.casefold() == signal.gate_name.casefold()
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one gate for {signal.application_id}/{signal.gate_name}; got {len(candidates)}"
        )
    current = candidates[0]
    evidence_refs = tuple(dict.fromkeys((*current.evidence_refs, signal.source_ref)))
    updated = replace(
        current,
        result=signal.result,
        reason=signal.reason,
        evidence_refs=evidence_refs,
    )
    graph.gates[current.gate_id] = updated
    return updated


def todoist_human_projection(
    graph: RuntimeGraph,
    *,
    now: datetime,
    project_id: str,
    parent_id: str | None = None,
    max_items: int = 25,
) -> list[dict[str, Any]]:
    """Project only the READY human frontier; never mirror the complete CRM corpus."""
    tasks: list[dict[str, Any]] = []
    for action in graph.human_frontier(now)[:max_items]:
        title = str(action.metadata.get("title") or action.application_id)
        task: dict[str, Any] = {
            "content": f"RG · {title} — {action.instruction}",
            "description": (
                f"Runtime action `{action.action_id}`. Expected output: {action.expected_output}. "
                f"Source projection only; completion is not submission evidence."
            ),
            "priority": _todoist_priority(action.priority),
            "labels": ["uexchanges", "runtimegraph", "human_now"],
            "projectId": project_id,
        }
        if parent_id:
            task["parentId"] = parent_id
        if action.deadline is not None:
            task["dueString"] = action.deadline.isoformat()
        tasks.append(task)
    return tasks


def runtime_event_for_action(
    *,
    action: ActionNode,
    session: AgentSession,
    lease: WorkLease,
    now: datetime,
    operation: str,
    authoritative_source_version: str,
    state_before: str | None = None,
    state_after: str | None = None,
    source_ref: str | None = None,
    correlation_id: str | None = None,
) -> AgentEvent:
    """Build a coordination event for a runtime mutation under an exact action lease."""
    return create_agent_event(
        occurred_at=now,
        project_id=session.project_id,
        context_id=session.context_id,
        session_id=session.session_id,
        agent_id=session.agent_id,
        event_type="RUNTIME_ACTION_MUTATED",
        entity_type="runtime_action",
        entity_id=action.action_id,
        operation=operation,
        authoritative_source_version=authoritative_source_version,
        state_before=state_before,
        state_after=state_after,
        payload={
            "application_id": action.application_id,
            "executor": action.executor.value,
            "action_type": action.action_type,
        },
        source_ref=source_ref,
        correlation_id=correlation_id,
        lease_id=lease.lease_id,
        writer_version="runtimegraph-v1.0.0",
    )


def authorize_runtime_mutation(
    *,
    action: ActionNode,
    session: AgentSession,
    lease: WorkLease,
    now: datetime,
    operation: str,
    authoritative_source_version: str,
    seen_idempotency_keys: Iterable[str] = (),
    state_before: str | None = None,
    state_after: str | None = None,
    source_ref: str | None = None,
    correlation_id: str | None = None,
) -> RuntimeMutationAuthorization:
    event = runtime_event_for_action(
        action=action,
        session=session,
        lease=lease,
        now=now,
        operation=operation,
        authoritative_source_version=authoritative_source_version,
        state_before=state_before,
        state_after=state_after,
        source_ref=source_ref,
        correlation_id=correlation_id,
    )
    decision = evaluate_event_application(
        event=event,
        seen_idempotency_keys=set(seen_idempotency_keys),
        lease=lease,
        now=now,
        mutating=True,
    )
    return RuntimeMutationAuthorization(
        allowed=decision.allowed,
        reason=decision.reason,
        event=event,
        decision=decision,
    )


def gmail_signal(
    *,
    application_id: str,
    gate_name: str,
    result: GateResult,
    reason: str,
    message_id: str,
    message_timestamp: str,
) -> EvidenceSignal:
    """Normalize a fact already extracted from a Gmail message.

    This function deliberately does not infer eligibility from raw prose. The caller must
    supply the evidence-backed result after reading the full thread.
    """
    if not message_id.strip():
        raise ValueError("message_id is required")
    return EvidenceSignal(
        application_id=application_id,
        gate_name=gate_name,
        result=result,
        reason=reason,
        source_ref=f"gmail:{message_id}",
        source_version=f"gmail:{message_id}:{message_timestamp}",
    )


def _todoist_priority(priority: int) -> str:
    if priority >= 90:
        return "p1"
    if priority >= 75:
        return "p2"
    if priority >= 60:
        return "p3"
    return "p4"
