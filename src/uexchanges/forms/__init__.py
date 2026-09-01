"""Typed contracts for the UE-Xchanges form execution boundary.

This package is intentionally browser-agnostic. Browser/network actuators live
outside the canonical Python core and must consume these contracts rather than
inventing their own submission state.
"""

from .approval import (
    ApprovalAction,
    ApprovalClaims,
    ApprovalStatus,
    ApprovalVerification,
    MAX_APPROVAL_TTL_SECONDS,
    issue_approval_token,
    verify_approval_token,
)
from .compiler import CompilationResult, compile_execution_plan
from .fingerprint import canonicalize_form_url, form_schema_fingerprint
from .models import (
    AuthRequirement,
    FieldOwnership,
    FieldSensitivity,
    FormExecutionPlan,
    FormExecutionState,
    FormField,
    FormFieldType,
    SubmissionAttempt,
    SubmissionAttemptStatus,
    SubmissionReceipt,
    SubmitAuthority,
)
from .policy import AnswerAuthor, AnswerCandidate, PolicyIssue, validate_candidate
from .receipts import (
    DuplicateDecision,
    DuplicateDisposition,
    answer_pack_hash,
    build_submission_attempt,
    evaluate_duplicate_guard,
    execution_plan_hash,
    reconcile_receipt,
    submission_key,
)

__all__ = [
    "AnswerAuthor",
    "AnswerCandidate",
    "ApprovalAction",
    "ApprovalClaims",
    "ApprovalStatus",
    "ApprovalVerification",
    "AuthRequirement",
    "CompilationResult",
    "DuplicateDecision",
    "DuplicateDisposition",
    "FieldOwnership",
    "FieldSensitivity",
    "FormExecutionPlan",
    "FormExecutionState",
    "FormField",
    "FormFieldType",
    "MAX_APPROVAL_TTL_SECONDS",
    "PolicyIssue",
    "SubmissionAttempt",
    "SubmissionAttemptStatus",
    "SubmissionReceipt",
    "SubmitAuthority",
    "answer_pack_hash",
    "build_submission_attempt",
    "canonicalize_form_url",
    "compile_execution_plan",
    "evaluate_duplicate_guard",
    "execution_plan_hash",
    "form_schema_fingerprint",
    "issue_approval_token",
    "reconcile_receipt",
    "submission_key",
    "validate_candidate",
    "verify_approval_token",
]
