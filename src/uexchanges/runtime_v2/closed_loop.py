from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..human_command_center import HumanCommandCard, build_human_command_center
from ..runtime_graph import ActionNode, RuntimeGraph
from .evidence_claims import ClaimDecision, EvidenceClaimRegistry
from .incremental import IncrementalRuntimeReducer, RuntimeDelta
from .models import ClaimRecord, EvidenceRecord, RuntimeDomainEvent


@dataclass(frozen=True)
class ClosedLoopState:
    last_event_id: str | None
    human_ready: int
    agent_ready: int
    system_ready: int
    waiting: int


class ClosedLoopRuntime:
    """Small facade connecting evidence, incremental graph reduction and frontiers."""

    def __init__(self, graph: RuntimeGraph) -> None:
        self.graph = graph
        self.reducer = IncrementalRuntimeReducer()
        self.claims = EvidenceClaimRegistry()

    def ingest_event(self, event: RuntimeDomainEvent) -> RuntimeDelta:
        return self.reducer.apply(self.graph, event)

    def add_evidence(self, evidence: EvidenceRecord) -> None:
        self.claims.add_evidence(evidence)

    def add_claim(self, claim: ClaimRecord, *, now: datetime | None = None) -> ClaimDecision:
        return self.claims.add_claim(claim, now=now)

    def human_frontier(self, *, now: datetime, max_items: int = 5) -> tuple[HumanCommandCard, ...]:
        return build_human_command_center(self.graph, now=now, max_items=max_items)

    def agent_frontier(self, *, now: datetime, max_items: int = 50) -> tuple[ActionNode, ...]:
        return tuple(self.graph.agent_frontier(now)[:max_items])

    def state(self, *, now: datetime) -> ClosedLoopState:
        human = self.graph.human_frontier(now)
        agent = self.graph.agent_frontier(now)
        system = self.graph.ready_actions(now, executor=None)
        system_count = sum(1 for action in system if action.executor.value == "SYSTEM")
        waiting = sum(1 for action in self.graph.actions.values() if action.state.value == "WAITING")
        return ClosedLoopState(
            self.reducer.last_event_id,
            len(human),
            len(agent),
            system_count,
            waiting,
        )
