import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.economics import (
    EconomicsInputs,
    EconomicsStatus,
    PriorityComponents,
    calculate_economics,
    strategic_priority_score,
)

D = Decimal


class EconomicsTests(unittest.TestCase):
    def test_verified_cash_metrics(self):
        result = calculate_economics(
            EconomicsInputs(
                gross_cash=D("2000"),
                work_hours=D("40"),
                committed_hours=D("240"),
                mandatory_programme_fees=D("100"),
                unreimbursed_travel=D("100"),
                visa_and_insurance=D("0"),
                estimated_tax_and_contract_fees=D("200"),
                other_compulsory_costs=D("0"),
                travel_reimbursement_value=D("300"),
                accommodation_value=D("600"),
                meals_value=D("300"),
                training_value=D("200"),
                other_non_cash_value=D("0"),
            )
        )
        self.assertEqual(result.status, EconomicsStatus.VERIFIED)
        self.assertEqual(result.net_cash, D("1600"))
        self.assertEqual(result.net_cash_per_work_hour, D("40"))
        self.assertEqual(
            result.net_cash_per_committed_hour,
            D("6.666666666666666666666666667"),
        )
        self.assertEqual(result.verified_funded_value, D("1400"))

    def test_unknown_cost_prevents_fake_net_cash(self):
        result = calculate_economics(
            EconomicsInputs(
                gross_cash=D("2000"),
                work_hours=D("40"),
                committed_hours=D("240"),
                estimated_tax_and_contract_fees=None,
            )
        )
        self.assertEqual(result.status, EconomicsStatus.VERIFICATION_DEBT)
        self.assertIsNone(result.net_cash)
        self.assertIn("estimated_tax_and_contract_fees", result.missing_fields)

    def test_unknown_hours_prevent_rate_but_not_known_net_cash(self):
        result = calculate_economics(
            EconomicsInputs(gross_cash=D("1000"), work_hours=None, committed_hours=None)
        )
        self.assertEqual(result.net_cash, D("1000"))
        self.assertIsNone(result.net_cash_per_work_hour)
        self.assertEqual(result.status, EconomicsStatus.PARTIAL)

    def test_cash_and_non_cash_value_are_separate(self):
        result = calculate_economics(
            EconomicsInputs(
                gross_cash=D("0"),
                work_hours=D("10"),
                committed_hours=D("100"),
                travel_reimbursement_value=D("400"),
                accommodation_value=D("600"),
                meals_value=D("300"),
                training_value=D("100"),
                other_non_cash_value=D("0"),
            )
        )
        self.assertEqual(result.status, EconomicsStatus.NON_CASH)
        self.assertEqual(result.net_cash, D("0"))
        self.assertEqual(result.verified_funded_value, D("1400"))

    def test_negative_values_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_economics(
                EconomicsInputs(
                    gross_cash=D("-1"),
                    work_hours=D("1"),
                    committed_hours=D("1"),
                )
            )

    def test_priority_weights_sum_to_one_hundred(self):
        score = strategic_priority_score(
            PriorityComponents(
                paid_cash_rate=100,
                payment_certainty=100,
                total_net_cash=100,
                trainer_trajectory=100,
                outside_europe=100,
                rarity=100,
                remote_work_compatibility=100,
                experience_network=100,
            )
        )
        self.assertEqual(score, 100.0)

    def test_priority_score_does_not_accept_unbounded_inputs(self):
        with self.assertRaises(ValueError):
            strategic_priority_score(PriorityComponents(101, 0, 0, 0, 0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
