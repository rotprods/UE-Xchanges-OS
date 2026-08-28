import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.facts import FactClaim, resolve_fact_claims


class FactResolutionTests(unittest.TestCase):
    def claim(self, value, source, day, authority=80, live=False):
        return FactClaim(
            fact_key="deadline",
            value=value,
            source_id=source,
            authority_rank=authority,
            observed_at=datetime(2026, 8, day, 12, tzinfo=timezone.utc),
            live_current=live,
        )

    def test_missing_fact_stays_unresolved(self):
        result = resolve_fact_claims([])
        self.assertFalse(result.resolved)
        self.assertEqual(result.decision_code, "VERIFY_MISSING_FACT")

    def test_consistent_claims_resolve(self):
        result = resolve_fact_claims([
            self.claim("2026-09-02", "older", 20),
            self.claim("2026-09-02", "newer", 28),
        ])
        self.assertTrue(result.resolved)
        self.assertEqual(result.value, "2026-09-02")
        self.assertEqual(result.winning_source_id, "newer")

    def test_newer_live_peer_supersedes_stale_same_authority(self):
        result = resolve_fact_claims([
            self.claim("2026-08-12", "stale-infopack", 12),
            self.claim("2026-08-28", "live-salto", 28, live=True),
        ])
        self.assertTrue(result.resolved)
        self.assertEqual(result.value, "2026-08-28")
        self.assertEqual(result.decision_code, "LIVE_SOURCE_SUPERSEDES_STALE_ARTIFACT")

    def test_newer_lower_authority_does_not_override_higher_authority(self):
        result = resolve_fact_claims([
            self.claim("A", "official", 20, authority=100),
            self.claim("B", "social", 28, authority=30, live=True),
        ])
        self.assertFalse(result.resolved)
        self.assertEqual(result.decision_code, "VERIFY_CONFLICTING_FACT")

    def test_two_live_top_authority_conflicts_stay_unresolved(self):
        result = resolve_fact_claims([
            self.claim("A", "live-a", 27, live=True),
            self.claim("B", "live-b", 28, live=True),
        ])
        self.assertFalse(result.resolved)

    def test_mixed_fact_keys_rejected(self):
        first = self.claim("A", "a", 27)
        second = FactClaim("country", "ES", "b", 80, datetime(2026, 8, 28, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            resolve_fact_claims([first, second])


if __name__ == "__main__":
    unittest.main()
