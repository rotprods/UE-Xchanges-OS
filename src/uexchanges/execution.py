from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .models import AIPolicy, GateResult


class CommunicationState(str, Enum):
    SENT_WAITING = "sent_waiting"
    REPLY_RECEIVED = "reply_received"
    BOUNCED = "bounced"
    FOLLOW_UP_DUE = "follow_up_due"
    DEADLINE_CRITICAL_NO_REPLY = "deadline_critical_no_reply"
    DEADLINE_PASSED_NO_REPLY = "deadline_passed_no_reply"


class SubmissionState(str, Enum):
    PRE_DEADLINE = "pre_deadline"
    SUBMITTED_CONFIRMED = "submitted_confirmed"
    SUBMITTED_UNVERIFIED = "submitted_unverified"
    DEADLINE_PASSED_RECEIPT_UNKNOWN = "deadline_passed_receipt_unknown"
    CLOSED_NOT_SUBMITTED = "closed_not_submitted"
    WITHDRAWN = "withdrawn"


class ExecutionAction(str, Enum):
    WAIT_REPLY = "wait_reply"
    INGEST_REPLY = "ingest_reply"
    RESOLVE_CONTACT_ROUTE = "resolve_contact_route"
    FOLLOW_UP = "follow_up"
    ESCALATE_DIRECT_ROUTE = "escalate_direct_route"
    VERIFY_ELIGIBILITY = "verify_eligibility"
    RESOLVE_PRIVATE_GATES = "resolve_private_gates"
    CAPTURE_FORM = "capture_form"
    RESOLVE_AI_POLICY = "resolve_ai_policy"
    HUMAN_WRITE_REQUIRED = "human_write_required"
    BUILD_ASSETS = "build_assets"
    HUMAN_REVIEW = "human_review"
    SUBMIT = "submit"
    VERIFY_RECEIPT = "verify_receipt"
    RECORD_SUBMITTED = "record_submitted"
    CLOSE_NOT_SUBMITTED = "close_not_submitted"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class CommunicationDecision:
    state: CommunicationState
    action: ExecutionAction
    reason: str


@dataclass(frozen=True)
class SubmissionDecision:
    state: SubmissionState
    action: ExecutionAction
    reason: str


@dataclass(frozen=True)
class ExecutionGateDecision:
    status: str
    action: ExecutionAction
    ready_to_submit: bool
    reasons: tuple[str, ...]


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def evaluate_communication(
    *,
    sent_at: datetime,
    now: datetime,
    reply_received: bool = False,
    bounced: bool = False,
    deadline: datetime | None = None,
    follow_up_after_hours: float = 24.0,
    escalate_within_hours: float = 24.0,
) -> CommunicationDecision:
    """Route an outbound verification/relationship message without inventing outcomes."""
    sent_at = _require_aware(sent_at, "sent_at")
    now = _require_aware(now, "now")
    if deadline is not None:
        deadline = _require_aware(deadline, "deadline")
    if follow_up_after_hours < 0 or escalate_within_hours < 0:
        raise ValueError("SLA hours must be non-negative")
    if reply_received and bounced:
        raise ValueError("A message cannot be both replied-to and bounced")

    if reply_received:
        return CommunicationDecision(
            CommunicationState.REPLY_RECEIVED,
            ExecutionAction.INGEST_REPLY,
            "A reply exists; extract source-backed facts and re-evaluate the affected gates.",
        )
    if bounced:
        return CommunicationDecision(
            CommunicationState.BOUNCED,
            ExecutionAction.RESOLVE_CONTACT_ROUTE,
            "Delivery failed; find an authoritative alternative contact route.",
        )

    if deadline is not None:
        seconds_to_deadline = (deadline - now).total_seconds()
        if seconds_to_deadline <= 0:
            return CommunicationDecision(
                CommunicationState.DEADLINE_PASSED_NO_REPLY,
                ExecutionAction.NO_ACTION,
                "The deadline passed without a reply. This is not a rejection and does not prove that an application was or was not submitted.",
            )
        if seconds_to_deadline <= escalate_within_hours * 3600:
            return CommunicationDecision(
                CommunicationState.DEADLINE_CRITICAL_NO_REPLY,
                ExecutionAction.ESCALATE_DIRECT_ROUTE,
                "The reply SLA is dominated by the application deadline; use the best legitimate direct route without bypassing hard gates.",
            )

    elapsed_hours = (now - sent_at).total_seconds() / 3600
    if elapsed_hours >= follow_up_after_hours:
        return CommunicationDecision(
            CommunicationState.FOLLOW_UP_DUE,
            ExecutionAction.FOLLOW_UP,
            "The reply SLA elapsed; send one concise follow-up or use another authoritative contact route.",
        )
    return CommunicationDecision(
        CommunicationState.SENT_WAITING,
        ExecutionAction.WAIT_REPLY,
        "The message is inside the reply SLA; avoid duplicate outreach.",
    )


def resolve_submission_state(
    *,
    deadline: datetime,
    now: datetime,
    receipt_ref: str | None = None,
    applicant_confirms_submitted: bool = False,
    explicit_not_submitted: bool = False,
    withdrawn: bool = False,
) -> SubmissionDecision:
    """Resolve submission state from evidence; missing receipts never become guessed outcomes."""
    deadline = _require_aware(deadline, "deadline")
    now = _require_aware(now, "now")
    positive_signals = bool(receipt_ref) or applicant_confirms_submitted
    if positive_signals and (explicit_not_submitted or withdrawn):
        raise ValueError("Conflicting submission evidence")
    if explicit_not_submitted and withdrawn:
        raise ValueError("Use either explicit_not_submitted or withdrawn")

    if receipt_ref:
        return SubmissionDecision(
            SubmissionState.SUBMITTED_CONFIRMED,
            ExecutionAction.RECORD_SUBMITTED,
            "A receipt/reference confirms submission.",
        )
    if applicant_confirms_submitted:
        return SubmissionDecision(
            SubmissionState.SUBMITTED_UNVERIFIED,
            ExecutionAction.VERIFY_RECEIPT,
            "The applicant reports submission, but the receipt/reference is not yet stored.",
        )
    if explicit_not_submitted:
        return SubmissionDecision(
            SubmissionState.CLOSED_NOT_SUBMITTED,
            ExecutionAction.CLOSE_NOT_SUBMITTED,
            "The applicant explicitly confirms that no submission occurred.",
        )
    if withdrawn:
        return SubmissionDecision(
            SubmissionState.WITHDRAWN,
            ExecutionAction.NO_ACTION,
            "The application was explicitly withdrawn.",
        )
    if now >= deadline:
        return SubmissionDecision(
            SubmissionState.DEADLINE_PASSED_RECEIPT_UNKNOWN,
            ExecutionAction.VERIFY_RECEIPT,
            "The deadline passed and submission evidence is absent. Preserve ambiguity until the applicant or portal supplies authoritative evidence.",
        )
    return SubmissionDecision(
        SubmissionState.PRE_DEADLINE,
        ExecutionAction.NO_ACTION,
        "The deadline is open and no submission evidence exists yet.",
    )


def evaluate_execution_gate(
    *,
    eligibility: GateResult,
    ai_policy: AIPolicy,
    private_gates_resolved: bool,
    form_captured: bool,
    mandatory_assets_ready: bool,
    human_review_complete: bool,
    human_owned_final_text: bool,
    now: datetime,
    deadline: datetime | None = None,
) -> ExecutionGateDecision:
    """Choose the one mandatory next action for a candidate application."""
    now = _require_aware(now, "now")
    if deadline is not None:
        deadline = _require_aware(deadline, "deadline")
        if now >= deadline:
            return ExecutionGateDecision(
                "deadline_passed",
                ExecutionAction.VERIFY_RECEIPT,
                False,
                ("Deadline has passed; resolve submission evidence before assigning a terminal state.",),
            )

    if eligibility is GateResult.FAIL:
        return ExecutionGateDecision(
            "blocked_ineligible",
            ExecutionAction.NO_ACTION,
            False,
            ("A confirmed hard eligibility gate failed.",),
        )
    if eligibility is GateResult.UNKNOWN:
        return ExecutionGateDecision(
            "eligibility_unknown",
            ExecutionAction.VERIFY_ELIGIBILITY,
            False,
            ("Eligibility contains unresolved verification debt.",),
        )
    if not private_gates_resolved:
        return ExecutionGateDecision(
            "private_gates_pending",
            ExecutionAction.RESOLVE_PRIVATE_GATES,
            False,
            ("Private residence, availability, sensitive-profile or comparable gates remain unresolved.",),
        )
    if not form_captured:
        return ExecutionGateDecision(
            "form_missing",
            ExecutionAction.CAPTURE_FORM,
            False,
            ("The current application form/questions are not captured.",),
        )
    if ai_policy is AIPolicy.UNKNOWN:
        return ExecutionGateDecision(
            "ai_policy_unknown",
            ExecutionAction.RESOLVE_AI_POLICY,
            False,
            ("Application-writing policy is unknown; final-answer generation remains disabled.",),
        )
    if ai_policy is AIPolicy.FINAL_TEXT_PROHIBITED and not human_owned_final_text:
        return ExecutionGateDecision(
            "human_write_required",
            ExecutionAction.HUMAN_WRITE_REQUIRED,
            False,
            ("The call prohibits AI-written final text; the applicant must author the final wording.",),
        )
    if not mandatory_assets_ready:
        return ExecutionGateDecision(
            "assets_missing",
            ExecutionAction.BUILD_ASSETS,
            False,
            ("One or more mandatory assets/documents are missing.",),
        )
    if not human_review_complete:
        return ExecutionGateDecision(
            "human_review_pending",
            ExecutionAction.HUMAN_REVIEW,
            False,
            ("A human must verify facts, tone, consent and commitment before submission.",),
        )
    return ExecutionGateDecision(
        "ready_to_submit",
        ExecutionAction.SUBMIT,
        True,
        ("All known deterministic and human-review gates pass.",),
    )
