import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AgentBootstrapContractTests(unittest.TestCase):
    def test_required_bootstrap_files_exist(self):
        required = [
            "AGENTS.md",
            "MEMORY.md",
            "HANDOFF.md",
            "agent_context/README.md",
            "agent_context/context.md",
            "agent_context/progress.md",
            "agent_context/checkpoints.md",
            "agent_context/session.md",
            "agent_context/runtimegraph.md",
            "agent_context/knowledge.md",
            "agent_context/recovery.md",
            "agent_context/bootstrap_manifest.json",
            "docs/AGENT_BOOTSTRAP_PROTOCOL.md",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_manifest_is_strict_and_requires_bootstrap_ack(self):
        manifest = json.loads((ROOT / "agent_context/bootstrap_manifest.json").read_text())
        self.assertEqual(manifest["contract"], "UEX_AGENT_BOOTSTRAP")
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(manifest["authority"], "DERIVED_BOOTSTRAP_ROUTER_ONLY")
        rules = manifest["rules"]
        self.assertFalse(rules["chat_memory_is_authoritative"])
        self.assertFalse(rules["memory_md_is_live_state"])
        self.assertTrue(rules["must_emit_bootstrap_ack_before_lease"])
        self.assertEqual(rules["required_ack_event"], "BOOTSTRAP_CONTEXT_LOADED")
        self.assertIn("MEMORY.md", manifest["required_public_reads"])
        self.assertIn("agent_context/context.md", manifest["required_public_reads"])
        self.assertIn("Drive:Work_Leases:UNEXPIRED_ONLY", manifest["required_private_reads"])
        sequence = manifest["write_sequence"]
        self.assertLess(sequence.index("EMIT_BOOTSTRAP_CONTEXT_LOADED"), sequence.index("ACQUIRE_SMALLEST_SAFE_LEASE"))

    def test_agents_enforces_manifest_memory_and_handshake(self):
        agents = (ROOT / "AGENTS.md").read_text()
        for marker in [
            "agent_context/bootstrap_manifest.json",
            "MEMORY.md",
            "BOOTSTRAP_CONTEXT_LOADED",
            "agent_context/context.md",
            "currently unexpired",
            "Unregistered sessions are read-only",
        ]:
            self.assertIn(marker, agents)

    def test_handoff_points_zero_context_agents_to_manifest_and_memory(self):
        handoff = (ROOT / "HANDOFF.md").read_text()
        for marker in ["agent_context/bootstrap_manifest.json", "MEMORY.md", "BOOTSTRAP_CONTEXT_LOADED"]:
            self.assertIn(marker, handoff)

    def test_memory_is_explicitly_non_authoritative_and_nonvolatile(self):
        memory = (ROOT / "MEMORY.md").read_text()
        for marker in [
            "Durable semantic memory, not live state",
            "Do **not** store live counts",
            "Chat memory is never the continuity system",
            "BOOTSTRAP_CONTEXT_LOADED",
            "SubmissionAttempt != SubmissionReceipt",
        ]:
            self.assertIn(marker, memory)

    def test_context_readme_points_to_manifest_and_memory(self):
        readme = (ROOT / "agent_context/README.md").read_text()
        self.assertIn("bootstrap_manifest.json", readme)
        self.assertIn("../MEMORY.md", readme)
        self.assertIn("BOOTSTRAP_CONTEXT_LOADED", readme)

    def test_protocol_prohibits_volatile_memory_and_session_reuse(self):
        protocol = (ROOT / "docs/AGENT_BOOTSTRAP_PROTOCOL.md").read_text()
        self.assertIn("Never reuse a historical Session ID", protocol)
        self.assertIn("Do not store", protocol)
        self.assertIn("current opportunity/application counts", protocol)
        self.assertIn("CI cannot prove a remote agent actually read a file", protocol)


if __name__ == "__main__":
    unittest.main()
