from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from ..models import AIPolicy
from .fingerprint import form_schema_fingerprint
from .models import (
    AuthRequirement,
    FieldOwnership,
    FormExecutionPlan,
    FormExecutionState,
    FormField,
    SubmitAuthority,
)
from .policy import AnswerAuthor, AnswerCandidate, PolicyIssue, validate_candidate


@dataclass(frozen=True)
class CompilationResult:
    plan: FormExecutionPlan
    issues: tuple[PolicyIssue, ...]

    @property
    def ready_for_prefill(self) -> bool:
        return not self.issues and self.plan.ready_for_prefill


def _plan_id(application_id: str, fingerprint: str, source_version: str) -> str:
    raw = f"{application_id}|{fingerprint}|{source_version}".encode("utf-8")
    return f"formplan:{hashlib.sha256(raw).hexdigest()}"


def compile_execution_plan(
    *,
    application_id: str,
    opportunity_id: str,
    canonical_form_url: str,
    provider: str,
    captured_fields: tuple[FormField, ...],
    answers: tuple[AnswerCandidate, ...],
    ai_policy: AIPolicy,
    auth_requirement: AuthRequirement,
    submit_authority: SubmitAuthority,
    allowed_origins: tuple[str, ...],
    created_at: datetime,
    expires_at: datetime,
    source_version: str,
    attachments: tuple[str, ...] = (),
) -> CompilationResult:
    """Compile captured form structure + evidence-backed answers into a safe plan.

    This function never infers unknown facts or application policy. Blocking
    issues remain explicit and the returned plan stays below PREFILL_READY.
    """
    if not captured_fields:
        raise ValueError("captured_fields must not be empty")

    answer_map: dict[str, AnswerCandidate] = {}
    issues: list[PolicyIssue] = []
    for candidate in answers:
        if candidate.field_key in answer_map:
            raise ValueError(f"duplicate answer candidate for {candidate.field_key}")
        answer_map[candidate.field_key] = candidate

    captured_keys = {field.field_key for field in captured_fields}
    for extra_key in sorted(set(answer_map) - captured_keys):
        issues.append(PolicyIssue("answer_without_captured_field", extra_key, "Answer targets a field absent from the captured form schema."))

    compiled_fields: list[FormField] = []
    for field in captured_fields:
        candidate = answer_map.get(field.field_key)
        if field.ownership is FieldOwnership.BLACK:
            if candidate is not None:
                issues.append(PolicyIssue("black_field_answer_forbidden", field.field_key, "BLACK/secret fields cannot receive model-visible answer candidates."))
            issues.append(PolicyIssue("black_field_human_interaction_required", field.field_key, "BLACK/secret field requires human interaction outside the model-visible answer plan."))
            compiled_fields.append(field)
            continue

        if candidate is None:
            if field.required:
                issues.append(PolicyIssue("required_answer_missing", field.field_key, "Required field has no evidence-backed or human-owned answer."))
            compiled_fields.append(field)
            continue

        candidate_issues = validate_candidate(field=field, candidate=candidate, ai_policy=ai_policy)
        issues.extend(candidate_issues)
        if candidate_issues:
            compiled_fields.append(field)
            continue

        editable_by_agent = candidate.ownership in {FieldOwnership.GREEN, FieldOwnership.YELLOW} and candidate.author is not AnswerAuthor.HUMAN
        compiled_fields.append(
            FormField(
                field_key=field.field_key,
                label=field.label,
                field_type=field.field_type,
                required=field.required,
                options=field.options,
                maxlength=field.maxlength,
                answer=candidate.value,
                answer_source=candidate.source,
                evidence_ids=candidate.evidence_ids,
                ownership=candidate.ownership,
                sensitivity=candidate.sensitivity,
                editable_by_agent=editable_by_agent,
            )
        )

    fingerprint = form_schema_fingerprint(
        provider=provider,
        canonical_form_url=canonical_form_url,
        fields=captured_fields,
    )
    state = FormExecutionState.ANSWER_PACK_RESOLVED if not issues else FormExecutionState.FORM_SCHEMA_VERIFIED
    plan = FormExecutionPlan(
        plan_id=_plan_id(application_id, fingerprint, source_version),
        application_id=application_id,
        opportunity_id=opportunity_id,
        canonical_form_url=canonical_form_url,
        provider=provider,
        form_fingerprint=fingerprint,
        fields=tuple(compiled_fields),
        ai_policy=ai_policy,
        auth_requirement=auth_requirement,
        submit_authority=submit_authority,
        allowed_origins=allowed_origins,
        created_at=created_at,
        expires_at=expires_at,
        source_version=source_version,
        attachments=attachments,
        state=state,
    )
    return CompilationResult(plan=plan, issues=tuple(issues))
