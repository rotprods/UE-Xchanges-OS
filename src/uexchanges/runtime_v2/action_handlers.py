from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Protocol

from ..runtime_graph import ActionNode, ExecutorType
from .event_router import NormalizedIngress


SAFE_AGENT_PREFIXES = (
    "VERIFY_",
    "CAPTURE_",
    "INGEST_",
    "SCAN_",
    "PREPARE_",
    "EXTRACT_",
    "RECONCILE_",
    "CHECK_",
    "RESOLVE_",
)

# Fail closed even if an upstream compiler accidentally classified one of these
# actions as AGENT.  RG2.3 does not own irreversible or identity-bearing actions.
FORBIDDEN_AUTONOMY_TOKENS = (
    "PAY",
    "PAYMENT",
    "TRANSFER",
    "PURCHASE",
    "BOOK_TRAVEL",
    "LOGIN",
    "AUTH",
    "PASSWORD",
    "OTP",
    "2FA",
    "CAPTCHA",
    "COOKIE",
    "PRIVATE_FIELD",
    "SENSITIVE_FIELD",
    "HUMAN_FINAL",
    "APPLICANT_OWNED",
    "RECORD_VIDEO",
    "VIDEO_RECORD",
    "SUBMIT",
    "SEND_EMAIL",
    "SEND_MESSAGE",
    "REPLY_EMAIL",
    "EXTERNAL_PREFILL",
)


class HandlerDisposition(str, Enum):
    SUCCEEDED = "succeeded"
    WAITING = "waiting"
    RETRYABLE = "retryable"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentActionRequest:
    action_id: str
    application_id: str
    action_type: str
    instruction: str
    expected_output: str
    priority: int
    observed_at: datetime
    metadata: dict[str, object]

    @classmethod
    def from_action(cls, action: ActionNode, *, observed_at: datetime) -> "AgentActionRequest":
        _aware(observed_at)
        return cls(
            action_id=action.action_id,
            application_id=action.application_id,
            action_type=action.action_type,
            instruction=action.instruction,
            expected_output=action.expected_output,
            priority=action.priority,
            observed_at=observed_at,
            metadata=dict(action.metadata),
        )


@dataclass(frozen=True)
class AgentActionResult:
    disposition: HandlerDisposition
    observed_at: datetime
    evidence_refs: tuple[str, ...] = ()
    ingresses: tuple[NormalizedIngress, ...] = ()
    reason_code: str = ""
    retryable: bool = False

    def __post_init__(self) -> None:
        _aware(self.observed_at)
        if self.reason_code:
            if "\n" in self.reason_code or "\r" in self.reason_code:
                raise ValueError("reason_code must be single-line")
            if len(self.reason_code) > 240:
                raise ValueError("reason_code exceeds 240 characters")
        if self.disposition is HandlerDisposition.SUCCEEDED and not self.evidence_refs:
            raise ValueError("successful agent action requires durable evidence_refs")
        if self.disposition is HandlerDisposition.RETRYABLE and not self.retryable:
            raise ValueError("RETRYABLE disposition requires retryable=True")


class AgentActionHandler(Protocol):
    def __call__(self, request: AgentActionRequest) -> AgentActionResult: ...


class HandlerRegistry:
    """Small exact/prefix handler registry.

    Tool-specific implementations live outside the pure runtime kernel.  This
    registry only maps already-safe action types to handlers supplied by the
    current agent/tool environment.
    """

    def __init__(self) -> None:
        self._exact: dict[str, AgentActionHandler] = {}
        self._prefix: list[tuple[str, AgentActionHandler]] = []

    def register_exact(self, action_type: str, handler: AgentActionHandler) -> None:
        token = _token(action_type)
        if token in self._exact:
            raise ValueError(f"duplicate exact handler: {token}")
        self._exact[token] = handler

    def register_prefix(self, prefix: str, handler: AgentActionHandler) -> None:
        token = _token(prefix)
        if any(existing == token for existing, _ in self._prefix):
            raise ValueError(f"duplicate prefix handler: {token}")
        self._prefix.append((token, handler))
        self._prefix.sort(key=lambda item: len(item[0]), reverse=True)

    def resolve(self, action_type: str) -> AgentActionHandler | None:
        token = _token(action_type)
        if token in self._exact:
            return self._exact[token]
        for prefix, handler in self._prefix:
            if token.startswith(prefix):
                return handler
        return None


def autonomy_allowed(action: ActionNode) -> tuple[bool, str]:
    """Return whether RG2.3 may execute this action without human authority."""
    if action.executor is not ExecutorType.AGENT:
        return False, f"executor={action.executor.value} is not AGENT"
    combined = _token(f"{action.action_type} {action.instruction}")
    forbidden = next((item for item in FORBIDDEN_AUTONOMY_TOKENS if item in combined), None)
    if forbidden:
        return False, f"forbidden autonomy token: {forbidden}"
    action_token = _token(action.action_type)
    if not any(action_token.startswith(prefix) for prefix in SAFE_AGENT_PREFIXES):
        if action.metadata.get("autonomy_safe") is not True:
            return False, "action family is not explicitly autonomy-safe"
    return True, "reversible evidence-backed agent action"


def ensure_result_scoped(request: AgentActionRequest, result: AgentActionResult) -> None:
    """Prevent one handler result from mutating another application subgraph."""
    for ingress in result.ingresses:
        if ingress.application_id is not None and ingress.application_id != request.application_id:
            raise ValueError("handler ingress belongs to a different application")
    for ref in result.evidence_refs:
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("evidence_refs must contain non-empty stable references")


def static_handler(result: AgentActionResult) -> Callable[[AgentActionRequest], AgentActionResult]:
    """Testing/simulation helper; production tool agents provide real handlers."""
    def _handler(_: AgentActionRequest) -> AgentActionResult:
        return result

    return _handler


def _token(value: str) -> str:
    return "_".join(value.upper().replace(";", " ").replace("→", " ").split())


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
