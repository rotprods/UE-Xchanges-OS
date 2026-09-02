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
            "docs/WRITER_AUTHORIZATION_AND_RELIABILITY_WATCHDOG.md",
            "docs/WRITER_AUTHORIZATION_RECEIPT.md",
            "schemas/writer-authorization-receipt.schema.json",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_manifest_is_strict_and_requires_bootstrap_and_writer_authorization(self):
        manifest = json.loads((ROOT / "agent_context/bootstrap_manifest.json").read_text())
        self.assertEqual(manifest["contract"], "UEX_AGENT_BOOTSTRAP")
        self.assertEqual(manifest["version"], "1.1.0")
        self.assertEqual(manifest["authority"], "DERIVED_BOOTSTRAP_ROUTER_ONLY")
        rules = manifest["rules"]
        self.assertFalse(rules["chat_memory_is_authoritative"])
        self.assertFalse(rules["memory_md_is_live_state"])
        self.assertTrue(rules["must_emit_bootstrap_ack_before_lease"])
        self.assertEqual(rules["required_ack_event"], "BOOTSTRAP_CONTEXT_LOADED")
        self.assertTrue(rules["must_evaluate_writer_authorization_before_lease"])
        self.assertTrue(rules["must_emit_writer_authorization_receipt_before_lease"])
        self.assertEqual(rules["required_writer_authorization_event"], "WRITER_AUTHORIZATION_GRANTED")
        self.assertEqual(rules["writer_authorization_receipt_version"], "1.0.0")
        self.assertTrue(rules["external_side_effects_require_separate_capability"])
        self.assertIn("MEMORY.md", manifest["required_public_reads"])
        self.assertIn("agent_context/context.md", manifest["required_public_reads"])
        self.assertIn("docs/WRITER_AUTHORIZATION_RECEIPT.md", manifest["required_public_reads"])
        self.assertIn("Drive:Work_Leases:UNEXPIRED_ONLY", manifest["required_private_reads"])
        self.assertIn("health_report_sha256", manifest["writer_authorization_receipt_required_fields"])
        self.assertIn("scope_sha256", manifest["writer_authorization_receipt_required_fields"])
        self.assertIn("authorization_receipt_id", manifest["lease_acquired_required_authorization_refs"])

        sequence = manifest["write_sequence"]
        self.assertLess(
            sequence.index("EMIT_BOOTSTRAP_CONTEXT_LOADED"),
            sequence.index("EVALUATE_CONTROL_PLANE_HEALTH"),
        )
        self.assertLess(
            sequence.index("EVALUATE_CONTROL_PLANE_HEALTH"),
            sequence.index("EVALUATE_WRITER_AUTHORIZATION"),
        )
        self.assertLess(
            sequence.index("EVALUATE_WRITER_AUTHORIZATION"),
            sequence.index("EMIT_WRITER_AUTHORIZATION_GRANTED"),
        )
        self.assertLess(
            sequence.index("EMIT_WRITER_AUTHORIZATION_GRANTED"),
            sequence.index("ACQUIRE_SMALLEST_SAFE_LEASE"),
        )

    def test_manifest_migration_is_nonretroactive_and_external_side_effects_stay_separate(self):
        manifest = json.loads((ROOT / "agent_context/bootstrap_manifest.json").read_text())
        migration = manifest["migration"]
        self.assertEqual(migration["receipt_enforcement"], "NON_RETROACTIVE")
        self.assertIn("not retroactively invalidated", migration["existing_sessions"])
        self.assertIn("separately versioned capability", migration["external_side_effects"])
        shortcuts = manifest["forbidden_bootstrap_shortcuts"]
        self.assertIn(
            "acquire_post_v1_1_write_lease_without_WRITER_AUTHORIZATION_GRANTED_receipt",
            shortcuts,
        )
        self.assertIn("treat_writer_authorization_receipt_as_domain_authority", shortcuts)
        self.assertIn("treat_writer_authorization_receipt_as_external_capability", shortcuts)

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

    def test_context_readme_routes_through_authorization_receipt_before_lease(self):
        readme = (ROOT / "agent_context/README.md").read_text()
        for marker in [
            "bootstrap_manifest.json",
            "../MEMORY.md",
            "BOOTSTRAP_CONTEXT_LOADED",
            "WriterAuthorization(ALLOWED)",
            "WRITER_AUTHORIZATION_GRANTED(receipt)",
            "domain authority",
        ]:
            self.assertIn(marker, readme)

    def test_protocol_prohibits_volatile_memory_and_requires_receipt(self):
        protocol = (ROOT / "docs/AGENT_BOOTSTRAP_PROTOCOL.md").read_text()
        for marker in [
            "Never reuse a historical Session ID",
            "Do not store",
            "current opportunity/application counts",
            "WRITER_AUTHORIZATION_GRANTED",
            "authorization_receipt_id",
            "domain_authority",
            "external_capability",
            "non-retroactive",
            "CI cannot prove a remote agent actually read a file",
        ]:
            self.assertIn(marker, protocol)


if __name__ == "__main__":
    unittest.main()
