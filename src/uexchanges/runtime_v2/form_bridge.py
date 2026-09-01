from __future__ import annotations

import hashlib
from datetime import datetime

from ..forms.models import FormExecutionPlan, FormExecutionState
from ..models import AIPolicy
from .models import RuntimeDomainEvent, RuntimeEventKind


def form_plan_runtime_events(
    *,
    plan: FormExecutionPlan,
    observed_at: datetime,
) -> tuple[RuntimeDomainEvent, ...]:
    """Translate a verified FormExecutionPlan into value-free RuntimeGraph events.

    This bridge never carries field answers, cookies, credentials or secret values.
    """
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")

    evidence_ref = f"formplan:{plan.plan_id}"
    seed = f"{plan.application_id}|{plan.plan_id}|{plan.source_version}|{plan.form_fingerprint}"
    event_base = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]

    evidence_event = RuntimeDomainEvent(
        event_id=f"rg2form:{event_base}:evidence",
        kind=RuntimeEventKind.EVIDENCE_ADDED,
        application_id=plan.application_id,
        occurred_at=observed_at,
        source_ref=evidence_ref,
        source_version=plan.source_version,
        payload={
            "evidence_ref": evidence_ref,
            "provider": plan.provider,
            "form_fingerprint": plan.form_fingerprint,
            "state": plan.state.value,
        },
    )

    if plan.state is FormExecutionState.BLOCKED:
        gate_result = "fail"
        reason = "Form Execution Plan is BLOCKED."
    elif plan.ai_policy is AIPolicy.UNKNOWN:
        gate_result = "unknown"
        reason = "Form structure is captured but AI/application-writing policy remains unknown."
    else:
        gate_result = "pass"
        reason = (
            f"Form plan {plan.plan_id} verified at state {plan.state.value}; "
            f"AI policy={plan.ai_policy.value}."
        )

    gate_event = RuntimeDomainEvent(
        event_id=f"rg2form:{event_base}:gate",
        kind=RuntimeEventKind.GATE_RESOLVED,
        application_id=plan.application_id,
        occurred_at=observed_at,
        source_ref=evidence_ref,
        source_version=plan.source_version,
        payload={
            "gate_name": "Infopack/Form/AI",
            "result": gate_result,
            "reason": reason,
        },
    )
    return evidence_event, gate_event
