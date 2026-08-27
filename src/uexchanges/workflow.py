from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import AIPolicy, GateResult


class NextAction(str, Enum):
    DUPLICATE_MERGED = "duplicate_merged"
    ARCHIVE_EXPIRED = "archive_expired"
    ARCHIVE_CLOSED = "archive_closed"
    VERIFY_CONFLICT = "verify_conflict"
    BLOCK_INELIGIBLE = "block_ineligible"
    VERIFY_ELIGIBILITY = "verify_eligibility"
    VERIFY_AI_POLICY = "verify_ai_policy"
    BUILD_EVIDENCE = "build_evidence"
    HUMAN_WRITE = "human_write"
    APPLY_NOW = "apply_now"
    QUEUE = "queue"
    TRACK = "track"


@dataclass(frozen=True)
class WorkflowDecision:
    action: NextAction
    decision_code: str
    reason: str


def route_application(
    *,
    eligibility: GateResult,
    ai_policy: AIPolicy,
    execution_priority: float,
    duplicate: bool = False,
    expired: bool = False,
    closed: bool = False,
    conflicting_authoritative_facts: bool = False,
    evidence_gaps: bool = False,
    mandatory_documents_missing: bool = False,
) -> WorkflowDecision:
    """Return the single allowed next route from explicit state.

    The order is intentional: irreversible/blocking conditions are evaluated before
    scoring. Priority cannot override duplicate, expiry, closure, conflicts or hard gates.
    """
    if duplicate:
        return WorkflowDecision(NextAction.DUPLICATE_MERGED, "DUPLICATE_PROVIDER_OR_CANONICAL_KEY", "Canonical opportunity already exists.")
    if expired:
        return WorkflowDecision(NextAction.ARCHIVE_EXPIRED, "BLOCK_DEADLINE", "Application deadline has elapsed.")
    if closed:
        return WorkflowDecision(NextAction.ARCHIVE_CLOSED, "ARCHIVE_CLOSED", "Organiser marks the call closed.")
    if conflicting_authoritative_facts:
        return WorkflowDecision(NextAction.VERIFY_CONFLICT, "VERIFY_CONFLICTING_FACT", "Authoritative facts conflict; submission is blocked until resolved.")
    if eligibility is GateResult.FAIL:
        return WorkflowDecision(NextAction.BLOCK_INELIGIBLE, "BLOCK_ELIGIBILITY", "A confirmed hard eligibility gate failed.")
    if eligibility is GateResult.UNKNOWN:
        return WorkflowDecision(NextAction.VERIFY_ELIGIBILITY, "VERIFY_ELIGIBILITY", "At least one hard eligibility input is unresolved.")
    if ai_policy is AIPolicy.UNKNOWN:
        return WorkflowDecision(NextAction.VERIFY_AI_POLICY, "VERIFY_UNKNOWN_AI_POLICY", "Application-writing policy is unresolved.")
    if evidence_gaps or mandatory_documents_missing:
        return WorkflowDecision(NextAction.BUILD_EVIDENCE, "VERIFY_PRIVATE_EVIDENCE", "Evidence or mandatory document debt remains.")
    if ai_policy is AIPolicy.FINAL_TEXT_PROHIBITED:
        return WorkflowDecision(NextAction.HUMAN_WRITE, "HUMAN_WRITE_AI_PROHIBITED", "AI-written final answers are prohibited by the call.")

    priority = max(0.0, min(100.0, float(execution_priority)))
    if priority >= 80:
        return WorkflowDecision(NextAction.APPLY_NOW, "APPLY_HIGH_FIT_HIGH_URGENCY", "All gates passed and execution priority is at least 80.")
    if priority >= 60:
        return WorkflowDecision(NextAction.QUEUE, "QUEUE_READY", "All gates passed; queue behind higher-priority ready calls.")
    return WorkflowDecision(NextAction.TRACK, "TRACK_READY_LOW_PRIORITY", "All gates passed but expected value/urgency is currently lower.")
