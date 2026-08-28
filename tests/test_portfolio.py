import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.portfolio import (
    OpportunityWindow,
    PortfolioState,
    build_conflict_edges,
    evaluate_commitment,
    intervals_overlap,
)


class PortfolioConflictTests(unittest.TestCase):
    def window(self, opportunity_id, start, end, state=PortfolioState.APPLIED):
        return OpportunityWindow(opportunity_id, date.fromisoformat(start), date.fromisoformat(end), state)

    def test_inclusive_same_day_overlap(self):
        a = self.window("a", "2026-10-01", "2026-10-16")
        b = self.window("b", "2026-10-16", "2026-10-20")
        self.assertTrue(intervals_overlap(a, b))

    def test_adjacent_next_day_does_not_overlap(self):
        a = self.window("a", "2026-10-01", "2026-10-16")
        b = self.window("b", "2026-10-17", "2026-10-20")
        self.assertFalse(intervals_overlap(a, b))

    def test_applied_overlap_creates_edge_but_does_not_imply_block(self):
        edges = build_conflict_edges([
            self.window("ctrl-real", "2026-09-28", "2026-10-05"),
            self.window("yupi", "2026-10-01", "2026-10-16"),
        ])
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].edge_type, "MUTUALLY_EXCLUSIVE_IF_ACCEPTED")

    def test_terminal_window_is_not_in_active_conflict_projection(self):
        edges = build_conflict_edges([
            self.window("a", "2026-10-01", "2026-10-10", PortfolioState.WITHDRAWN),
            self.window("b", "2026-10-05", "2026-10-12", PortfolioState.APPLIED),
        ])
        self.assertEqual(edges, [])

    def test_commit_allowed_when_overlap_is_only_applied(self):
        windows = [
            self.window("a", "2026-10-01", "2026-10-10", PortfolioState.ACCEPTED),
            self.window("b", "2026-10-05", "2026-10-12", PortfolioState.APPLIED),
        ]
        decision = evaluate_commitment("a", windows)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "COMMIT")

    def test_commit_requires_resolution_when_other_overlap_is_accepted(self):
        windows = [
            self.window("a", "2026-10-01", "2026-10-10", PortfolioState.ACCEPTED),
            self.window("b", "2026-10-05", "2026-10-12", PortfolioState.ACCEPTED),
        ]
        decision = evaluate_commitment("a", windows)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "PORTFOLIO_RESOLUTION")
        self.assertEqual(decision.conflicting_ids, ("b",))

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            self.window("bad", "2026-10-10", "2026-10-01")


if __name__ == "__main__":
    unittest.main()
