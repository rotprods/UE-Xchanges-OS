from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable


ZERO = Decimal("0")


class EconomicsStatus(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    NON_CASH = "non_cash"
    VERIFICATION_DEBT = "verification_debt"


@dataclass(frozen=True)
class EconomicsInputs:
    gross_cash: Decimal | None
    work_hours: Decimal | None
    committed_hours: Decimal | None
    mandatory_programme_fees: Decimal | None = ZERO
    unreimbursed_travel: Decimal | None = ZERO
    visa_and_insurance: Decimal | None = ZERO
    estimated_tax_and_contract_fees: Decimal | None = ZERO
    other_compulsory_costs: Decimal | None = ZERO
    travel_reimbursement_value: Decimal | None = None
    accommodation_value: Decimal | None = None
    meals_value: Decimal | None = None
    training_value: Decimal | None = None
    other_non_cash_value: Decimal | None = None


@dataclass(frozen=True)
class EconomicsMetrics:
    status: EconomicsStatus
    net_cash: Decimal | None
    net_cash_per_work_hour: Decimal | None
    net_cash_per_committed_hour: Decimal | None
    verified_funded_value: Decimal
    funded_value_complete: bool
    missing_fields: tuple[str, ...]


@dataclass(frozen=True)
class PriorityComponents:
    paid_cash_rate: float
    payment_certainty: float
    total_net_cash: float
    trainer_trajectory: float
    outside_europe: float
    rarity: float
    remote_work_compatibility: float
    experience_network: float


PRIORITY_WEIGHTS = {
    "paid_cash_rate": 0.35,
    "payment_certainty": 0.15,
    "total_net_cash": 0.10,
    "trainer_trajectory": 0.12,
    "outside_europe": 0.10,
    "rarity": 0.08,
    "remote_work_compatibility": 0.05,
    "experience_network": 0.05,
}


def _validate_money(value: Decimal | None, name: str) -> None:
    if value is not None and value < ZERO:
        raise ValueError(f"{name} cannot be negative")


def _missing(values: Iterable[tuple[str, Decimal | None]]) -> tuple[str, ...]:
    return tuple(name for name, value in values if value is None)


def calculate_economics(inputs: EconomicsInputs) -> EconomicsMetrics:
    """Calculate only what the evidence supports; missing costs never become zero."""
    money_fields = (
        ("gross_cash", inputs.gross_cash),
        ("mandatory_programme_fees", inputs.mandatory_programme_fees),
        ("unreimbursed_travel", inputs.unreimbursed_travel),
        ("visa_and_insurance", inputs.visa_and_insurance),
        ("estimated_tax_and_contract_fees", inputs.estimated_tax_and_contract_fees),
        ("other_compulsory_costs", inputs.other_compulsory_costs),
        ("travel_reimbursement_value", inputs.travel_reimbursement_value),
        ("accommodation_value", inputs.accommodation_value),
        ("meals_value", inputs.meals_value),
        ("training_value", inputs.training_value),
        ("other_non_cash_value", inputs.other_non_cash_value),
    )
    for name, value in money_fields:
        _validate_money(value, name)
    for name, value in (
        ("work_hours", inputs.work_hours),
        ("committed_hours", inputs.committed_hours),
    ):
        if value is not None and value <= ZERO:
            raise ValueError(f"{name} must be positive when provided")

    cash_dependencies = (
        ("gross_cash", inputs.gross_cash),
        ("mandatory_programme_fees", inputs.mandatory_programme_fees),
        ("unreimbursed_travel", inputs.unreimbursed_travel),
        ("visa_and_insurance", inputs.visa_and_insurance),
        ("estimated_tax_and_contract_fees", inputs.estimated_tax_and_contract_fees),
        ("other_compulsory_costs", inputs.other_compulsory_costs),
    )
    missing = list(_missing(cash_dependencies))
    net_cash: Decimal | None = None
    if not missing:
        assert inputs.gross_cash is not None
        costs = sum(
            (value for _, value in cash_dependencies[1:] if value is not None), ZERO
        )
        net_cash = inputs.gross_cash - costs

    per_work: Decimal | None = None
    if net_cash is not None and inputs.work_hours is not None:
        per_work = net_cash / inputs.work_hours
    elif inputs.work_hours is None:
        missing.append("work_hours")

    per_committed: Decimal | None = None
    if net_cash is not None and inputs.committed_hours is not None:
        per_committed = net_cash / inputs.committed_hours
    elif inputs.committed_hours is None:
        missing.append("committed_hours")

    benefit_fields = (
        inputs.travel_reimbursement_value,
        inputs.accommodation_value,
        inputs.meals_value,
        inputs.training_value,
        inputs.other_non_cash_value,
    )
    funded_value = sum((value for value in benefit_fields if value is not None), ZERO)
    funded_complete = all(value is not None for value in benefit_fields)

    unique_missing = tuple(dict.fromkeys(missing))
    if net_cash == ZERO and inputs.gross_cash == ZERO and not unique_missing:
        status = EconomicsStatus.NON_CASH
    elif not unique_missing and funded_complete:
        status = EconomicsStatus.VERIFIED
    elif net_cash is None:
        status = EconomicsStatus.VERIFICATION_DEBT
    else:
        status = EconomicsStatus.PARTIAL

    return EconomicsMetrics(
        status=status,
        net_cash=net_cash,
        net_cash_per_work_hour=per_work,
        net_cash_per_committed_hour=per_committed,
        verified_funded_value=funded_value,
        funded_value_complete=funded_complete,
        missing_fields=unique_missing,
    )


def strategic_priority_score(components: PriorityComponents) -> float:
    """Return a 0–100 scheduling score. It never decides eligibility."""
    total = 0.0
    for name, weight in PRIORITY_WEIGHTS.items():
        value = float(getattr(components, name))
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"{name} must be between 0 and 100")
        total += value * weight
    return round(total, 4)
