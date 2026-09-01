"""Typed contracts for the UE-Xchanges form execution boundary.

This package is intentionally browser-agnostic. Browser/network actuators live
outside the canonical Python core and must consume these contracts rather than
inventing their own submission state.
"""

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

__all__ = [
    "AnswerAuthor",
    "AnswerCandidate",
    "AuthRequirement",
    "CompilationResult",
    "FieldOwnership",
    "FieldSensitivity",
    "FormExecutionPlan",
    "FormExecutionState",
    "FormField",
    "FormFieldType",
    "PolicyIssue",
    "SubmissionAttempt",
    "SubmissionAttemptStatus",
    "SubmissionReceipt",
    "SubmitAuthority",
    "canonicalize_form_url",
    "compile_execution_plan",
    "form_schema_fingerprint",
    "validate_candidate",
]
