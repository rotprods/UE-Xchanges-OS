from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ExecutionPolicyInvariantTests(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_source_first_and_inbound_action_are_canonical(self):
        for rel in [
            "AGENTS.md",
            "MEMORY.md",
            "docs/APPLICATION_EXECUTION_CONTRACT.md",
            "agent_context/NEXT_DEATHSAFE.md",
        ]:
            text = self.read(rel)
            self.assertIn("INFOPACK-FIRST", text, rel)
            self.assertIn("INBOUND_ACTION_FIRST", text, rel)

    def test_source_first_chain_is_ordered(self):
        for rel in ["AGENTS.md", "docs/APPLICATION_EXECUTION_CONTRACT.md", "agent_context/NEXT_DEATHSAFE.md"]:
            text = self.read(rel)
            for token in ["ORIGINAL INFOPACK", "CURRENT CALL", "CURRENT FORM", "OFFICIAL ORGANISER"]:
                self.assertIn(token, text, rel)

    def test_historical_scheduler_frontier_not_canonical_next(self):
        text = self.read("agent_context/NEXT_DEATHSAFE.md")
        self.assertNotIn("SCHEDULER_PRODUCTION_CANARY_PASS #1", text)

    def test_signature_fails_closed_without_safe_renderer(self):
        text = self.read("AGENTS.md")
        self.assertIn("privacy-safe renderer/template", text)
        self.assertIn("outbound email is **blocked**", text)

if __name__ == "__main__":
    unittest.main()
