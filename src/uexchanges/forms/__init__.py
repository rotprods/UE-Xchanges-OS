"""Typed contracts for the UE-Xchanges form execution boundary.

This package is intentionally browser-agnostic.  Browser/network actuators live
outside the canonical Python core and must consume these contracts rather than
inventing their own submission state.
"""

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

__all__ = [
    "AuthRequirement",
    "FieldOwnership",
    "FieldSensitivity",
    "FormExecutionPlan",
    "FormExecutionState",
    "FormField",
    "FormFieldType",
    "SubmissionAttempt",
    "SubmissionAttemptStatus",
    "SubmissionReceipt",
    "SubmitAuthority",
]
