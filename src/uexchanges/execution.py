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


class ApplicationRoute(str, Enum):
    EMAIL = "email"
    FORM = "form"
    EMAIL_THEN_FORM = "email_then_form"
    FORM_THEN_EMAIL = "form_then_email"
    UNKNOWN = "unknown"


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
    SEND_EMAIL_CANDIDATURE = "send_email_candidature"
    COMPLETE_FORM = "complete_form"
    RECONCILE_OUTBOUND_EFFECT = "reconcile_outbound_effect"
    BLOCK_DUPLICATE_OUTREACH = "block_duplicate_outreach"
    FIX_SIGNATURE = "fix_signature"
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


@dataclass(frozen=True)
class RouteDecision:
    route: ApplicationRoute
    action: ExecutionAction
    reason: str


@dataclass(frozen=True)
class OutboundPreflightDecision:
    allowed: bool
    action: ExecutionAction
    reasons: tuple[str, ...]


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def decide_application_route(
    *,
    email_candidature_authorized: bool = False,
    form_required: bool = False,
    email_required: bool = False,
    explicit_order: str | None = None,
) -> RouteDecision:
    """Choose the lowest-friction authorised route without inventing provider rules.

    `explicit_order` may be `email_then_form` or `form_then_email` only when the
    provider actually specifies that order.
    """
    if explicit_order not in {None, "email_then_form", "form_then_email"}:
        raise ValueError("explicit_order must be email_then_form or form_then_email")

    if explicit_order == "email_then_form":
        if not (email_required and form_required):
            raise ValueError("email_then_form requires both email_required and form_required")
        return RouteDecision(
            ApplicationRoute.EMAIL_THEN_FORM,
            ExecutionAction.SEND_EMAIL_CANDIDATURE,
            "The provider requires email first and form second; follow the stated order.",
        )
    if explicit_order == "form_then_email":
        if not (email_required and form_required):
            raise ValueError("form_then_email requires both email_required and form_required")
        return RouteDecision(
            ApplicationRoute.FORM_THEN_EMAIL,
            ExecutionAction.COMPLETE_FORM,
            "The provider requires form first and email second; follow the stated order.",
        )

    if form_required and email_required:
        return RouteDecision(
            ApplicationRoute.UNKNOWN,
            ExecutionAction.RESOLVE_CONTACT_ROUTE,
            "Both routes are required but their order is unresolved; verify only the blocking route detail.",
        )
    if form_required:
        return RouteDecision(
            ApplicationRoute.FORM,
            ExecutionAction.COMPLETE_FORM,
            "The provider requires the form; do not replace it with preliminary outreach.",
        )
    if email_required or email_candidature_authorized:
        return RouteDecision(
            ApplicationRoute.EMAIL,
            ExecutionAction.SEND_EMAIL_CANDIDATURE,
            "A complete candidature by email is authorised; use it directly instead of a route-query.",
        )
    return RouteDecision(
        ApplicationRoute.UNKNOWN,
        ExecutionAction.RESOLVE_CONTACT_ROUTE,
        "No authorised application route is established yet.",
    )


def evaluate_outbound_preflight(
    *,
    duplicate_initial_contact: bool = False,
    unknown_previous_send_outcome: bool = False,
    signature_count: int = 1,
    unresolved_blocking_questions: int = 0,
    asks_already_answered_questions: bool = False,
    contains_internal_process_jargon: bool = False,
    ai_policy: AIPolicy = AIPolicy.UNKNOWN,
    applicant_owned_text: bool = True,
) -> OutboundPreflightDecision:
    """Fail closed before organiser-facing email.

    This does not send anything. It enforces the durable outreach lessons that
    historically failed when multiple agents operated on the same call.
    """
    if signature_count < 0 or unresolved_blocking_questions < 0:
        raise ValueError("counts must be non-negative")

    reasons: list[str] = []
    if duplicate_initial_contact:
        reasons.append("An initial contact/candidature already exists for this call identity.")
        return OutboundPreflightDecision(False, ExecutionAction.BLOCK_DUPLICATE_OUTREACH, tuple(reasons))
    if unknown_previous_send_outcome:
        reasons.append("A previous send outcome is unknown; reconcile provider/Gmail evidence before retrying.")
        return OutboundPreflightDecision(False, ExecutionAction.RECONCILE_OUTBOUND_EFFECT, tuple(reasons))
    if signature_count != 1:
        reasons.append("The canonical Erasmus signature must appear exactly once.")
        return OutboundPreflightDecision(False, ExecutionAction.FIX_SIGNATURE, tuple(reasons))
    if asks_already_answered_questions:
        reasons.append("The draft repeats questions already resolved by existing evidence.")
    if contains_internal_process_jargon:
        reasons.append("The draft exposes internal orchestration/process jargon irrelevant to the recipient.")
    if unresolved_blocking_questions > 1:
        reasons.append("More than one unresolved blocking question remains; reduce outreach to the minimum needed to apply.")
    if ai_policy in {AIPolicy.ASSIST_ONLY, AIPolicy.FINAL_TEXT_PROHIBITED} and not applicant_owned_text:
        reasons.append("The route requires applicant-owned wording under the current AI/application policy.")

    if reasons:
        return OutboundPreflightDecision(False, ExecutionAction.HUMAN_REVIEW, tuple(reasons))
    return OutboundPreflightDecision(
        True,
        ExecutionAction.SEND_EMAIL_CANDIDATURE,
        ("Outbound preflight passed: unique contact, one signature, no repeated questions and policy-compatible wording.",),
    )


def evaluate_communication(
    *,
    sent_at: datetime,
    now: datetime,
    reply_received: bool = False,
    bounced: bool = False,
    deadline: datetime | None = None,
    follow_up_after_hours: float = 120.0,
    escalate_within_hours: float = 24.0,
) -> CommunicationDecision:
    """Route an outbound verification/relationship message without inventing outcomes.

    The default follow-up window is five days. Real deadline pressure can still
    escalate earlier, but ordinary silence must not generate daily organiser mail.
    """
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
            "The reply SLA elapsed; send at most one concise follow-up or use another authoritative route if still useful.",
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
    form_required: bool = True,
) -> ExecutionGateDecision:
    """Choose the one mandatory next action for a candidate application.

    `form_captured` means the complete reachable form has been captured. Email-only
    routes set `form_required=False` and are not blocked by a nonexistent form.
    """
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
    if form_required and not form_captured:
        return ExecutionGateDecision(
            "form_missing",
            ExecutionAction.CAPTURE_FORM,
            False,
            ("The complete current application form/questions are not captured.",),
        )
    if ai_policy is AIPolicy.UNKNOWN and not human_owned_final_text:
        return ExecutionGateDecision(
            "ai_policy_unknown_generated_text_blocked",
            ExecutionAction.RESOLVE_AI_POLICY,
            False,
            ("Application-writing policy is unknown; generated final-answer prose remains disabled unless the applicant independently owns the final wording.",),
        )
    if ai_policy in {AIPolicy.ASSIST_ONLY, AIPolicy.FINAL_TEXT_PROHIBITED} and not human_owned_final_text:
        return ExecutionGateDecision(
            "human_write_required",
            ExecutionAction.HUMAN_WRITE_REQUIRED,
            False,
            ("The current application policy requires applicant-owned final wording.",),
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
