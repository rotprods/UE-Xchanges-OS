import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "RUNBOOKS" / "RG22_SCHEDULED_CANARY.md"


class RG22ScheduledCanaryRunbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = RUNBOOK.read_text(encoding="utf-8")

    def test_runbook_is_present_and_routes_to_bounded_health_helper(self):
        self.assertIn("evaluate_bounded_writer_authorization_health", self.text)
        self.assertIn("historical_hygiene_evaluated=false", self.text)
        self.assertIn("currently-unexpired", self.text)

    def test_source_micro_batch_is_hard_bounded(self):
        self.assertIn("at most 5 new/late-unique source candidates", self.text)
        self.assertIn("at most 2 exact `application_id` / `opportunity_id` subgraphs", self.text)
        self.assertIn("never a second adapter in the same activation", self.text)
        self.assertIn("never advance a\ncursor past unprocessed evidence", self.text)

    def test_normal_writer_required_slos_are_explicit(self):
        for name in (
            "bootstrap_compliance",
            "session_identity_uniqueness",
            "lease_fencing_integrity",
        ):
            self.assertIn(name, self.text)

    def test_canary_cannot_promote_recurring_production_by_itself(self):
        self.assertIn("`recurring_production_enabled=false`", self.text)
        self.assertIn("does **not** by itself certify recurring production", self.text)

    def test_absolute_prohibitions_remain_explicit(self):
        for token in (
            "Never pay",
            "authenticate",
            "credentials/OTP/cookies",
            "externally PREFILL",
            "irreversibly Submit",
            "execute `Agent_Next`",
            "infer receipt from Gmail",
        ):
            self.assertIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
