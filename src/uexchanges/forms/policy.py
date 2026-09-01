from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..models import AIPolicy
from .models import FieldOwnership, FieldSensitivity, FormField, FormFieldType


class AnswerAuthor(str, Enum):
    VERIFIED_FACT = "verified_fact"
    AGENT = "agent"
    HUMAN = "human"


@dataclass(frozen=True)
class AnswerCandidate:
    field_key: str
    value: Any
    source: str
    evidence_ids: tuple[str, ...]
    ownership: FieldOwnership
    sensitivity: FieldSensitivity
    author: AnswerAuthor
    human_confirmed: bool = False

    def __post_init__(self) -> None:
        if not self.field_key.strip() or not self.source.strip():
            raise ValueError("answer candidate field_key/source must be non-empty")
        if self.ownership is FieldOwnership.BLACK:
            raise ValueError("BLACK fields cannot have an AnswerCandidate")
        if self.sensitivity is FieldSensitivity.SECRET:
            raise ValueError("SECRET values cannot enter model-visible AnswerCandidate contracts")


@dataclass(frozen=True)
class PolicyIssue:
    code: str
    field_key: str
    reason: str
    blocking: bool = True


def validate_candidate(*, field: FormField, candidate: AnswerCandidate, ai_policy: AIPolicy) -> tuple[PolicyIssue, ...]:
    issues: list[PolicyIssue] = []
    if field.field_key != candidate.field_key:
        issues.append(PolicyIssue("field_key_mismatch", field.field_key, "Candidate does not target this field."))
        return tuple(issues)

    if candidate.ownership is FieldOwnership.GREEN:
        if candidate.author is not AnswerAuthor.VERIFIED_FACT:
            issues.append(PolicyIssue("green_requires_verified_fact", field.field_key, "GREEN fields must come from verified factual evidence."))
        if not candidate.evidence_ids:
            issues.append(PolicyIssue("green_requires_evidence", field.field_key, "GREEN factual prefill requires evidence IDs."))

    if candidate.ownership is FieldOwnership.YELLOW and candidate.author is AnswerAuthor.AGENT:
        if ai_policy is AIPolicy.UNKNOWN:
            issues.append(PolicyIssue("ai_policy_unknown", field.field_key, "AI-authored narrative is blocked while application AI policy is unknown."))
        elif ai_policy is AIPolicy.FINAL_TEXT_PROHIBITED:
            issues.append(PolicyIssue("ai_final_text_prohibited", field.field_key, "AI-authored final wording is prohibited for this application."))

    if candidate.ownership is FieldOwnership.RED:
        if candidate.author is not AnswerAuthor.HUMAN or not candidate.human_confirmed:
            issues.append(PolicyIssue("red_requires_human_confirmation", field.field_key, "RED fields require explicit human-provided or human-confirmed values."))

    if candidate.ownership is FieldOwnership.UNRESOLVED:
        issues.append(PolicyIssue("ownership_unresolved", field.field_key, "Field ownership is unresolved."))

    if field.field_type in {FormFieldType.SELECT, FormFieldType.RADIO} and candidate.value not in field.options:
        issues.append(PolicyIssue("invalid_option", field.field_key, "Candidate value is not one of the captured form options."))

    if field.maxlength is not None and isinstance(candidate.value, str) and len(candidate.value) > field.maxlength:
        issues.append(PolicyIssue("maxlength_exceeded", field.field_key, "Candidate value exceeds captured maxlength."))

    return tuple(issues)
