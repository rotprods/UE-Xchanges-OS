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
from .normalization import normalize_answer
from .policy import AnswerAuthor, AnswerCandidate, PolicyIssue, validate_candidate
from .provider_capability import (
    PrefillPromotionDecision,
    ProviderCapabilityManifest,
    evaluate_prefill_promotion,
)
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
from .runtime_attestation import (
    AttestationStatus,
    AttestationVerification,
    AuthenticatedInspectClaims,
    MAX_INSPECT_TTL_SECONDS,
    MAX_RUNTIME_TTL_SECONDS,
    RuntimeAttestationClaims,
    issue_authenticated_inspect_evidence,
    issue_runtime_attestation,
    verify_authenticated_inspect_evidence,
    verify_runtime_attestation,
)

__all__ = [
    "AnswerAuthor",
    "AnswerCandidate",
    "ApprovalAction",
    "ApprovalClaims",
    "ApprovalStatus",
    "ApprovalVerification",
    "AttestationStatus",
    "AttestationVerification",
    "AuthenticatedInspectClaims",
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
    "MAX_INSPECT_TTL_SECONDS",
    "MAX_RUNTIME_TTL_SECONDS",
    "PolicyIssue",
    "PrefillPromotionDecision",
    "ProviderCapabilityManifest",
    "RuntimeAttestationClaims",
    "SubmissionAttempt",
    "SubmissionAttemptStatus",
    "SubmissionReceipt",
    "SubmitAuthority",
    "answer_pack_hash",
    "build_submission_attempt",
    "canonicalize_form_url",
    "compile_execution_plan",
    "evaluate_duplicate_guard",
    "evaluate_prefill_promotion",
    "execution_plan_hash",
    "form_schema_fingerprint",
    "issue_approval_token",
    "issue_authenticated_inspect_evidence",
    "issue_runtime_attestation",
    "normalize_answer",
    "reconcile_receipt",
    "submission_key",
    "validate_candidate",
    "verify_approval_token",
    "verify_authenticated_inspect_evidence",
    "verify_runtime_attestation",
]
