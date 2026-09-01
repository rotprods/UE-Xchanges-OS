from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .runtime_graph import ActionNode, RuntimeGraph


@dataclass(frozen=True)
class HumanCommandCard:
    order: int
    action_id: str
    application_id: str
    title: str
    instruction: str
    expected_output: str
    estimated_minutes: int
    priority: int
    deadline: datetime | None
    risk: str


def build_human_command_center(
    graph: RuntimeGraph,
    *,
    now: datetime,
    max_items: int = 5,
) -> tuple[HumanCommandCard, ...]:
    """Compress graph complexity into only immediately executable human micro-actions."""
    if max_items < 1:
        raise ValueError("max_items must be positive")
    cards: list[HumanCommandCard] = []
    for index, action in enumerate(graph.human_frontier(now)[:max_items], start=1):
        cards.append(
            HumanCommandCard(
                order=index,
                action_id=action.action_id,
                application_id=action.application_id,
                title=str(action.metadata.get("title") or action.application_id),
                instruction=_human_instruction(action),
                expected_output=action.expected_output,
                estimated_minutes=_estimate_minutes(action),
                priority=action.priority,
                deadline=action.deadline,
                risk=_risk(action, now),
            )
        )
    return tuple(cards)


def command_center_rows(cards: tuple[HumanCommandCard, ...]) -> list[dict[str, Any]]:
    return [
        {
            "Order": card.order,
            "Application ID": card.application_id,
            "Title": card.title,
            "Action": card.instruction,
            "Estimated Minutes": card.estimated_minutes,
            "Priority": card.priority,
            "Deadline": card.deadline.isoformat() if card.deadline else "",
            "Risk": card.risk,
            "Expected Output": card.expected_output,
            "Runtime Action ID": card.action_id,
        }
        for card in cards
    ]


def _human_instruction(action: ActionNode) -> str:
    token = action.action_type.upper()
    if "PAY" in token or "TRANSFER" in token:
        return "Revisar condiciones y realizar el pago solo si decides conservar la plaza."
    if "LOGIN" in token or "AUTH" in token:
        return "Abrir el portal y completar personalmente el inicio de sesión/autenticación."
    if "VIDEO" in token or "RECORD" in token:
        return "Grabar y aprobar personalmente el vídeo requerido."
    if "SUBMIT" in token:
        return "Revisar la candidatura final y realizar personalmente el envío; conservar el recibo."
    if "HUMAN_FINAL" in token or "HUMAN_REVIEW" in token or "REVIEW" in token:
        return "Revisar y confirmar personalmente el contenido final antes de continuar."
    return action.instruction


def _estimate_minutes(action: ActionNode) -> int:
    token = action.action_type.upper()
    if "VIDEO" in token or "RECORD" in token:
        return 10
    if "PAY" in token or "TRANSFER" in token:
        return 3
    if "LOGIN" in token or "AUTH" in token:
        return 2
    if "SUBMIT" in token:
        return 4
    return 3


def _risk(action: ActionNode, now: datetime) -> str:
    if action.deadline is None:
        return "NORMAL"
    remaining = (action.deadline - now).total_seconds()
    if remaining <= 0:
        return "DEADLINE_PASSED_VERIFY_OVERRIDE"
    if remaining <= 24 * 3600:
        return "CRITICAL_24H"
    if remaining <= 72 * 3600:
        return "HIGH_72H"
    return "NORMAL"
