from __future__ import annotations
from dataclasses import dataclass
from .models import GateDecision, GateResult

@dataclass(frozen=True)
class TrainerActivity:
    international: bool | None
    youth_work_field: bool | None
    days: float | None
    non_formal_learning: bool | None
    full_time_trainer: bool | None
    responsible_for_educational_goals: bool | None
    reference_validatable: bool | None

@dataclass(frozen=True)
class TrainerQualification:
    result: GateResult
    gates: tuple[GateDecision, ...]

def _bool_gate(name: str, value: bool | None, pass_reason: str, fail_reason: str) -> GateDecision:
    if value is None: return GateDecision(name, GateResult.UNKNOWN, f"{name} is not verified.")
    return GateDecision(name, GateResult.PASS if value else GateResult.FAIL, pass_reason if value else fail_reason)

def evaluate_toy_reference(activity: TrainerActivity) -> TrainerQualification:
    gates = [
        _bool_gate("international", activity.international, "International/intercultural activity verified.", "Activity is not international/intercultural."),
        _bool_gate("youth_work_field", activity.youth_work_field, "Youth-work context verified.", "Activity is outside the youth-work field."),
        GateDecision("duration", GateResult.UNKNOWN if activity.days is None else (GateResult.PASS if activity.days >= 3 else GateResult.FAIL), "Duration is unverified." if activity.days is None else ("At least 3 training days." if activity.days >= 3 else "Fewer than 3 training days.")),
        _bool_gate("non_formal_learning", activity.non_formal_learning, "NFE methodology verified.", "NFE methodology requirement not met."),
        _bool_gate("full_time_trainer", activity.full_time_trainer, "Full-time trainer role verified.", "Role was not full-time trainer."),
        _bool_gate("educational_responsibility", activity.responsible_for_educational_goals, "Responsibility for overall educational goals verified.", "No verified responsibility for overall educational goals."),
        _bool_gate("reference", activity.reference_validatable, "Reference can be validated.", "Reference is not validatable."),
    ]
    if any(g.result is GateResult.FAIL for g in gates): result=GateResult.FAIL
    elif any(g.result is GateResult.UNKNOWN for g in gates): result=GateResult.UNKNOWN
    else: result=GateResult.PASS
    return TrainerQualification(result, tuple(gates))
