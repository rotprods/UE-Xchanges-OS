from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Mapping

from ..coordination import (
    AgentSession,
    LeaseAction,
    SessionStatus,
    WorkLease,
    decide_lease,
    release_lease,
)
from ..runtime_graph import ActionNode, ActionState, ExecutorType
from .action_handlers import (
    AgentActionRequest,
    HandlerDisposition,
    HandlerRegistry,
    autonomy_allowed,
    ensure_result_scoped,
)
from .closed_loop import ClosedLoopRuntime
from .dispatcher import AutonomousEventDispatcher, DispatchStatus


class AgentExecutionStatus(str, Enum):
    COMPLETED = "completed"
    WAITING = "waiting"
    RETRY_SCHEDULED = "retry_scheduled"
    FAILED = "failed"
    BLOCKED_SAFETY = "blocked_safety"
    BLOCKED_LEASE = "blocked_lease"
    NO_HANDLER = "no_handler"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class AgentExecutionRecord:
    action_id: str
    application_id: str
    status: AgentExecutionStatus
    lease_id: str | None
    fencing_token: str | None
    attempts: int
    evidence_refs: tuple[str, ...] = ()
    dispatch_statuses: tuple[str, ...] = ()
    reason: str = ""
    retry_at: datetime | None = None


@dataclass(frozen=True)
class AgentExecutionCycle:
    started_at: datetime
    finished_at: datetime
    selected_action_ids: tuple[str, ...]
    records: tuple[AgentExecutionRecord, ...]

    @property
    def completed(self) -> tuple[str, ...]:
        return tuple(item.action_id for item in self.records if item.status is AgentExecutionStatus.COMPLETED)

    @property
    def human_frontier_changed(self) -> bool:
        # The executor itself never guesses this. Dispatcher results are applied
        # before completion, and callers rebuild/self-heal the frontier afterwards.
        return any(item.dispatch_statuses for item in self.records)


class AgentFrontierExecutor:
    """Execute only safe reversible AGENT actions from RuntimeGraph.

    The executor is intentionally tool-agnostic: the current ChatGPT/Codex/runtime
    environment supplies handlers that use Gmail/web/Drive/Form Gateway.  The
    kernel owns safety, action selection, action-level lease fencing, retry budget,
    evidence requirements and RuntimeGraph transitions.

    `WorkLease.lease_id` is the fencing token.  A takeover always receives a new
    lease ID, so stale writers cannot author a valid action transition with an old
    token.
    """

    def __init__(
        self,
        *,
        runtime: ClosedLoopRuntime,
        dispatcher: AutonomousEventDispatcher,
        session: AgentSession,
        handlers: HandlerRegistry,
        existing_action_leases: Mapping[str, WorkLease] | None = None,
        max_attempts: int = 3,
        lease_ttl: timedelta = timedelta(minutes=10),
        retry_base: timedelta = timedelta(minutes=5),
    ) -> None:
        if session.status is not SessionStatus.ACTIVE:
            raise ValueError("executor session must be ACTIVE")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if lease_ttl <= timedelta(0):
            raise ValueError("lease_ttl must be positive")
        if retry_base <= timedelta(0):
            raise ValueError("retry_base must be positive")
        self.runtime = runtime
        self.dispatcher = dispatcher
        self.session = session
        self.handlers = handlers
        self.max_attempts = max_attempts
        self.lease_ttl = lease_ttl
        self.retry_base = retry_base
        self.action_leases: dict[str, WorkLease] = dict(existing_action_leases or {})
        self.attempts: dict[str, int] = {}

    def run_cycle(self, *, now: datetime, max_actions: int = 3) -> AgentExecutionCycle:
        _aware(now)
        if max_actions < 1:
            raise ValueError("max_actions must be >= 1")
        self._resume_due_retries(now)
        frontier = self.runtime.graph.agent_frontier(now)
        selected = tuple(action.action_id for action in frontier[:max_actions])
        records: list[AgentExecutionRecord] = []
        cursor = now
        for action_id in selected:
            records.append(self.execute_one(action_id=action_id, now=cursor))
            cursor = cursor + timedelta(microseconds=1)
        return AgentExecutionCycle(now, cursor, selected, tuple(records))

    def execute_one(self, *, action_id: str, now: datetime) -> AgentExecutionRecord:
        _aware(now)
        graph = self.runtime.graph
        graph.recompute(now)
        action = graph.actions[action_id]
        if action.state is not ActionState.READY:
            return self._record(action, AgentExecutionStatus.NOT_READY, None, reason=f"state={action.state.value}")

        allowed, reason = autonomy_allowed(action)
        if not allowed:
            return self._record(action, AgentExecutionStatus.BLOCKED_SAFETY, None, reason=reason)

        handler = self.handlers.resolve(action.action_type)
        if handler is None:
            return self._record(action, AgentExecutionStatus.NO_HANDLER, None, reason="no registered safe handler")

        attempt = self.attempts.get(action_id, 0) + 1
        self.attempts[action_id] = attempt
        lease_decision = self._claim_action_lease(action=action, now=now, attempt=attempt)
        if not lease_decision.allowed or lease_decision.lease is None:
            return self._record(
                action,
                AgentExecutionStatus.BLOCKED_LEASE,
                lease_decision.lease,
                attempts=attempt,
                reason=lease_decision.reason,
            )
        lease = lease_decision.lease
        self.action_leases[action_id] = lease

        graph.claim(action_id, executor=ExecutorType.AGENT, now=now)
        request = AgentActionRequest.from_action(action, observed_at=now)
        try:
            result = handler(request)
            ensure_result_scoped(request, result)
        except RuntimeError as exc:
            return self._handle_retryable_exception(action, lease, now, attempt, str(exc))
        except Exception as exc:  # deterministic handler/scope contract failure
            graph.fail(action_id, executor=ExecutorType.AGENT, now=now, reason=f"HANDLER_CONTRACT_FAILURE:{type(exc).__name__}")
            self._release(action_id, lease, now, "handler contract failure")
            return self._record(
                action,
                AgentExecutionStatus.FAILED,
                lease,
                attempts=attempt,
                reason=f"HANDLER_CONTRACT_FAILURE:{type(exc).__name__}",
            )

        dispatch_results = self.dispatcher.dispatch_batch(result.ingresses)
        statuses = tuple(item.status.value for item in dispatch_results)
        if any(item.status is DispatchStatus.RETRY for item in dispatch_results):
            return self._schedule_retry(action, lease, now, attempt, "DISPATCH_RETRY", statuses)
        if any(item.status in {DispatchStatus.DEAD_LETTER, DispatchStatus.UNROUTED} for item in dispatch_results):
            graph.fail(action_id, executor=ExecutorType.AGENT, now=now, reason="DISPATCH_DEAD_LETTER")
            self._release(action_id, lease, now, "dispatcher rejected handler evidence")
            return self._record(
                action,
                AgentExecutionStatus.FAILED,
                lease,
                attempts=attempt,
                dispatch_statuses=statuses,
                reason="DISPATCH_DEAD_LETTER",
            )

        if result.disposition is HandlerDisposition.SUCCEEDED:
            for ref in result.evidence_refs:
                graph.completed_evidence.add(ref)
            graph.complete(
                action_id,
                executor=ExecutorType.AGENT,
                now=now,
                evidence_ref=result.evidence_refs[0],
            )
            self.attempts.pop(action_id, None)
            self._release(action_id, lease, now, "action completed with durable evidence")
            return self._record(
                action,
                AgentExecutionStatus.COMPLETED,
                lease,
                attempts=attempt,
                evidence_refs=result.evidence_refs,
                dispatch_statuses=statuses,
                reason=result.reason_code or "ACTION_COMPLETED",
            )

        if result.disposition is HandlerDisposition.WAITING:
            graph.wait(
                action_id,
                executor=ExecutorType.AGENT,
                now=now,
                reason=result.reason_code or "WAITING_EXTERNAL_EVIDENCE",
            )
            self._release(action_id, lease, now, "action waiting on external evidence")
            return self._record(
                action,
                AgentExecutionStatus.WAITING,
                lease,
                attempts=attempt,
                evidence_refs=result.evidence_refs,
                dispatch_statuses=statuses,
                reason=result.reason_code or "WAITING_EXTERNAL_EVIDENCE",
            )

        if result.disposition is HandlerDisposition.RETRYABLE or result.retryable:
            return self._schedule_retry(
                action,
                lease,
                now,
                attempt,
                result.reason_code or "RETRYABLE_HANDLER_RESULT",
                statuses,
            )

        graph.fail(
            action_id,
            executor=ExecutorType.AGENT,
            now=now,
            reason=result.reason_code or "HANDLER_FAILED",
        )
        self._release(action_id, lease, now, "handler returned failure")
        return self._record(
            action,
            AgentExecutionStatus.FAILED,
            lease,
            attempts=attempt,
            evidence_refs=result.evidence_refs,
            dispatch_statuses=statuses,
            reason=result.reason_code or "HANDLER_FAILED",
        )

    def _claim_action_lease(self, *, action: ActionNode, now: datetime, attempt: int):
        previous = self.action_leases.get(action.action_id)
        lease_id = _action_lease_id(self.session.session_id, action.action_id, now, attempt)
        return decide_lease(
            existing=previous,
            lease_id=lease_id,
            project_id=self.session.project_id,
            context_id=self.session.context_id,
            resource_type="runtime_action",
            resource_id=action.action_id,
            requester_agent_id=self.session.agent_id,
            requester_session_id=self.session.session_id,
            now=now,
            expires_at=now + self.lease_ttl,
        )

    def _handle_retryable_exception(
        self,
        action: ActionNode,
        lease: WorkLease,
        now: datetime,
        attempt: int,
        reason: str,
    ) -> AgentExecutionRecord:
        return self._schedule_retry(
            action,
            lease,
            now,
            attempt,
            f"RETRYABLE_HANDLER_EXCEPTION:{reason[:160]}",
            (),
        )

    def _schedule_retry(
        self,
        action: ActionNode,
        lease: WorkLease,
        now: datetime,
        attempt: int,
        reason: str,
        dispatch_statuses: tuple[str, ...],
    ) -> AgentExecutionRecord:
        graph = self.runtime.graph
        if attempt >= self.max_attempts:
            graph.fail(action.action_id, executor=ExecutorType.AGENT, now=now, reason="RETRY_BUDGET_EXHAUSTED")
            self._release(action.action_id, lease, now, "retry budget exhausted")
            return self._record(
                action,
                AgentExecutionStatus.FAILED,
                lease,
                attempts=attempt,
                dispatch_statuses=dispatch_statuses,
                reason="RETRY_BUDGET_EXHAUSTED",
            )

        wait_event = graph.wait(
            action.action_id,
            executor=ExecutorType.AGENT,
            now=now,
            reason=reason,
        )
        retry_at = now + self.retry_base * attempt
        waiting = graph.actions[action.action_id]
        graph.actions[action.action_id] = replace(
            waiting,
            metadata={
                **dict(waiting.metadata),
                "retryable": True,
                "retry_at": retry_at.isoformat(),
                "retry_attempt": attempt,
                "wait_event_id": wait_event.event_id,
            },
        )
        self._release(action.action_id, lease, now, "retry scheduled")
        return self._record(
            action,
            AgentExecutionStatus.RETRY_SCHEDULED,
            lease,
            attempts=attempt,
            dispatch_statuses=dispatch_statuses,
            reason=reason,
            retry_at=retry_at,
        )

    def _resume_due_retries(self, now: datetime) -> None:
        graph = self.runtime.graph
        for action_id, action in tuple(graph.actions.items()):
            if action.executor is not ExecutorType.AGENT or action.state is not ActionState.WAITING:
                continue
            if action.metadata.get("retryable") is not True:
                continue
            raw = action.metadata.get("retry_at")
            if not isinstance(raw, str):
                continue
            retry_at = datetime.fromisoformat(raw)
            if retry_at.tzinfo is None or retry_at.utcoffset() is None:
                continue
            if retry_at <= now:
                graph.resume_waiting(action_id, now=now)

    def _release(self, action_id: str, lease: WorkLease, now: datetime, reason: str) -> None:
        released = release_lease(
            lease,
            requester_session_id=self.session.session_id,
            at=now,
            reason=reason,
        )
        self.action_leases[action_id] = released

    def _record(
        self,
        action: ActionNode,
        status: AgentExecutionStatus,
        lease: WorkLease | None,
        *,
        attempts: int | None = None,
        evidence_refs: tuple[str, ...] = (),
        dispatch_statuses: tuple[str, ...] = (),
        reason: str = "",
        retry_at: datetime | None = None,
    ) -> AgentExecutionRecord:
        return AgentExecutionRecord(
            action_id=action.action_id,
            application_id=action.application_id,
            status=status,
            lease_id=lease.lease_id if lease else None,
            fencing_token=lease.lease_id if lease else None,
            attempts=attempts if attempts is not None else self.attempts.get(action.action_id, 0),
            evidence_refs=evidence_refs,
            dispatch_statuses=dispatch_statuses,
            reason=reason,
            retry_at=retry_at,
        )


def _action_lease_id(session_id: str, action_id: str, now: datetime, attempt: int) -> str:
    raw = f"{session_id}|{action_id}|{now.isoformat()}|{attempt}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"LSE-ACTION-{digest}"


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
