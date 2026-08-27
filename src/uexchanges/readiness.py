from __future__ import annotations
from dataclasses import dataclass
from .models import AIPolicy, GateResult
from .personalization import CriterionMatch

@dataclass(frozen=True)
class ApplicationReadiness:
    status: str
    reasons: tuple[str, ...]
    final_text_generation_allowed: bool

def evaluate_application_readiness(*, eligibility: GateResult, ai_policy: AIPolicy,
                                   criterion_matches: list[CriterionMatch],
                                   mandatory_documents_missing: list[str] | None = None,
                                   duplicate_already_submitted: bool = False) -> ApplicationReadiness:
    reasons=[]
    missing_docs=mandatory_documents_missing or []
    if duplicate_already_submitted: reasons.append("Duplicate submission blocked.")
    if eligibility is GateResult.FAIL: reasons.append("Known eligibility hard gate failed.")
    elif eligibility is GateResult.UNKNOWN: reasons.append("Eligibility contains unresolved verification debt.")
    gaps=[m.criterion for m in criterion_matches if m.gap]
    if gaps: reasons.append(f"Evidence gaps for {len(gaps)} criterion/criteria.")
    if missing_docs: reasons.append(f"Missing {len(missing_docs)} mandatory document(s).")
    can_generate_final = ai_policy in {AIPolicy.ALLOWED, AIPolicy.ASSIST_ONLY}
    if ai_policy is AIPolicy.FINAL_TEXT_PROHIBITED: reasons.append("Call prohibits AI-written final text.")
    elif ai_policy is AIPolicy.UNKNOWN: reasons.append("AI/application-writing policy is unverified.")
    if duplicate_already_submitted or eligibility is GateResult.FAIL:
        status="blocked"
    elif eligibility is GateResult.UNKNOWN or missing_docs or gaps or ai_policy is AIPolicy.UNKNOWN:
        status="needs_verification"
    elif ai_policy is AIPolicy.FINAL_TEXT_PROHIBITED:
        status="human_write_required"
    else:
        status="dossier_ready"
    return ApplicationReadiness(status, tuple(reasons), can_generate_final)
