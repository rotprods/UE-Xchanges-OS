from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from ..runtime_graph import ActionState, ExecutorType
from .closed_loop import ClosedLoopRuntime
from .event_router import ExplicitEventRouter, NormalizedIngress, to_domain_event
from .incremental import RuntimeDelta
from .source_cursor import SourceCursor, SourceCursorStore


class DispatchStatus(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"
    UNROUTED = "unrouted"


@dataclass(frozen=True)
class FrontierSnapshot:
    human: frozenset[str]
    agent: frozenset[str]
    system: frozenset[str]
    waiting: frozenset[str]


@dataclass(frozen=True)
class FrontierChange:
    human_added: tuple[str, ...] = ()
    human_removed: tuple[str, ...] = ()
    agent_added: tuple[str, ...] = ()
    agent_removed: tuple[str, ...] = ()
    system_added: tuple[str, ...] = ()
    system_removed: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeadLetter:
    ingress_key: str
    source_ref: str
    application_hint: str | None
    reason: str
    attempts: int
    observed_at: str


@dataclass(frozen=True)
class DispatchResult:
    status: DispatchStatus
    ingress_key: str
    application_id: str | None
    runtime_delta: RuntimeDelta | None
    frontier_change: FrontierChange
    cursor: SourceCursor | None
    attempts: int
    reason: str = ""


class AutonomousEventDispatcher:
    """At-least-once dispatcher for normalized RG2 events.

    Guarantees:
    - duplicate normalized ingress is a no-op;
    - only explicitly routed applications are mutated;
    - source cursor advances only after a durable applied/duplicate/dead-letter outcome;
    - retryable RuntimeError does not advance the cursor;
    - poison input is isolated after max attempts;
    - no raw email/web/form prose is interpreted here.
    """

    def __init__(
        self,
        *,
        runtime: ClosedLoopRuntime,
        router: ExplicitEventRouter,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.runtime = runtime
        self.router = router
        self.max_attempts = max_attempts
        self.cursors = SourceCursorStore()
        self.seen_ingress_keys: set[str] = set()
        self.retry_attempts: dict[str, int] = {}
        self.dead_letters: list[DeadLetter] = []

    def dispatch(self, ingress: NormalizedIngress) -> DispatchResult:
        key = ingress.ingress_idempotency_key
        before = self._frontier_snapshot(ingress.observed_at)

        if key in self.seen_ingress_keys:
            cursor = self._durable_advance(ingress)
            return DispatchResult(
                DispatchStatus.DUPLICATE,
                key,
                ingress.application_id,
                None,
                self._frontier_change(before, before),
                cursor,
                self.retry_attempts.get(key, 0),
                "normalized ingress already durably processed",
            )

        application_id = self.router.route(ingress)
        if application_id is None:
            return self._dead_letter_result(
                ingress,
                before=before,
                status=DispatchStatus.UNROUTED,
                reason="no explicit application route",
            )

        try:
            event = to_domain_event(ingress, application_id=application_id)
        except (ValueError, TypeError) as exc:
            return self._dead_letter_result(
                ingress,
                before=before,
                status=DispatchStatus.DEAD_LETTER,
                reason=f"invalid normalized event: {exc}",
                application_id=application_id,
            )

        try:
            delta = self.runtime.ingest_event(event)
        except (ValueError, KeyError, TypeError) as exc:
            return self._dead_letter_result(
                ingress,
                before=before,
                status=DispatchStatus.DEAD_LETTER,
                reason=f"deterministic reducer rejection: {exc}",
                application_id=application_id,
            )
        except RuntimeError as exc:
            attempts = self.retry_attempts.get(key, 0) + 1
            self.retry_attempts[key] = attempts
            if attempts < self.max_attempts:
                return DispatchResult(
                    DispatchStatus.RETRY,
                    key,
                    application_id,
                    None,
                    self._frontier_change(before, before),
                    None,
                    attempts,
                    f"retryable runtime failure: {exc}",
                )
            return self._dead_letter_result(
                ingress,
                before=before,
                status=DispatchStatus.DEAD_LETTER,
                reason=f"retry budget exhausted: {exc}",
                application_id=application_id,
                attempts=attempts,
            )

        self.seen_ingress_keys.add(key)
        self.retry_attempts.pop(key, None)
        cursor = self._durable_advance(ingress)
        after = self._frontier_snapshot(ingress.observed_at)
        status = DispatchStatus.DUPLICATE if delta.duplicate else DispatchStatus.APPLIED
        return DispatchResult(
            status,
            key,
            application_id,
            delta,
            self._frontier_change(before, after),
            cursor,
            1,
            "incremental event applied" if not delta.duplicate else "domain event already applied",
        )

    def dispatch_batch(self, ingresses: Iterable[NormalizedIngress]) -> tuple[DispatchResult, ...]:
        ordered = sorted(
            ingresses,
            key=lambda item: (
                item.observed_at,
                item.source_id,
                item.sequence if item.sequence is not None else -1,
                item.source_item_id,
            ),
        )
        return tuple(self.dispatch(item) for item in ordered)

    def snapshot(self) -> dict[str, Any]:
        return {
            "seen_ingress_count": len(self.seen_ingress_keys),
            "retry_attempts": dict(sorted(self.retry_attempts.items())),
            "dead_letters": [
                {
                    "ingress_key": item.ingress_key,
                    "source_ref": item.source_ref,
                    "application_hint": item.application_hint,
                    "reason": item.reason,
                    "attempts": item.attempts,
                    "observed_at": item.observed_at,
                }
                for item in self.dead_letters
            ],
            "source_cursors": self.cursors.snapshot(),
        }

    def _dead_letter_result(
        self,
        ingress: NormalizedIngress,
        *,
        before: FrontierSnapshot,
        status: DispatchStatus,
        reason: str,
        application_id: str | None = None,
        attempts: int | None = None,
    ) -> DispatchResult:
        key = ingress.ingress_idempotency_key
        final_attempts = attempts if attempts is not None else self.retry_attempts.get(key, 0) + 1
        letter = DeadLetter(
            ingress_key=key,
            source_ref=ingress.source_ref,
            application_hint=application_id or ingress.application_id,
            reason=reason,
            attempts=final_attempts,
            observed_at=ingress.observed_at.isoformat(),
        )
        self.dead_letters.append(letter)
        self.seen_ingress_keys.add(key)
        self.retry_attempts.pop(key, None)
        cursor = self._durable_advance(ingress)
        return DispatchResult(
            status,
            key,
            application_id,
            None,
            self._frontier_change(before, before),
            cursor,
            final_attempts,
            reason,
        )

    def _durable_advance(self, ingress: NormalizedIngress) -> SourceCursor:
        return self.cursors.advance(
            source_id=ingress.source_id,
            source_item_id=ingress.source_item_id,
            observed_at=ingress.observed_at,
            sequence=ingress.sequence,
        )

    def _frontier_snapshot(self, now) -> FrontierSnapshot:
        graph = self.runtime.graph
        human = frozenset(action.action_id for action in graph.human_frontier(now))
        agent = frozenset(action.action_id for action in graph.agent_frontier(now))
        system = frozenset(
            action.action_id
            for action in graph.ready_actions(now, ExecutorType.SYSTEM)
        )
        waiting = frozenset(
            action.action_id
            for action in graph.actions.values()
            if action.state is ActionState.WAITING
        )
        return FrontierSnapshot(human, agent, system, waiting)

    @staticmethod
    def _frontier_change(before: FrontierSnapshot, after: FrontierSnapshot) -> FrontierChange:
        return FrontierChange(
            human_added=tuple(sorted(after.human - before.human)),
            human_removed=tuple(sorted(before.human - after.human)),
            agent_added=tuple(sorted(after.agent - before.agent)),
            agent_removed=tuple(sorted(before.agent - after.agent)),
            system_added=tuple(sorted(after.system - before.system)),
            system_removed=tuple(sorted(before.system - after.system)),
        )
