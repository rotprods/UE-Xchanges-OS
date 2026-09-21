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
            "docs/APPLICATION_EXECUTION_CONTRACT.md",
            "docs/WRITER_AUTHORIZATION_AND_RELIABILITY_WATCHDOG.md",
            "docs/WRITER_AUTHORIZATION_RECEIPT.md",
            "schemas/writer-authorization-receipt.schema.json",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_manifest_is_strict_and_requires_bootstrap_writer_auth_and_execution_contract(self):
        manifest = json.loads((ROOT / "agent_context/bootstrap_manifest.json").read_text())
        self.assertEqual(manifest["contract"], "UEX_AGENT_BOOTSTRAP")
        self.assertEqual(manifest["version"], "1.3.0")
        self.assertEqual(manifest["authority"], "DERIVED_BOOTSTRAP_ROUTER_ONLY")
        self.assertEqual(manifest["application_execution_contract"], "docs/APPLICATION_EXECUTION_CONTRACT.md")
        rules = manifest["rules"]
        self.assertFalse(rules["chat_memory_is_authoritative"])
        self.assertFalse(rules["memory_md_is_live_state"])
        self.assertTrue(rules["must_emit_bootstrap_ack_before_lease"])
        self.assertEqual(rules["required_ack_event"], "BOOTSTRAP_CONTEXT_LOADED")
        self.assertTrue(rules["must_evaluate_writer_authorization_before_lease"])
        self.assertTrue(rules["must_emit_writer_authorization_receipt_before_lease"])
        self.assertTrue(rules["must_resolve_global_barriers_before_writer_authorization"])
        self.assertTrue(rules["must_recheck_global_barrier_before_lease_acquisition"])
        self.assertTrue(rules["must_recheck_global_barrier_before_irreversible_effect"])
        self.assertEqual(rules["required_writer_authorization_event"], "WRITER_AUTHORIZATION_GRANTED")
        self.assertEqual(rules["writer_authorization_receipt_version"], "1.0.0")
        self.assertTrue(rules["external_side_effects_require_separate_capability"])
        self.assertTrue(rules["must_read_application_execution_contract_before_selecting_frontier"])
        self.assertTrue(rules["safe_live_application_execution_outranks_nonblocking_architecture"])
        self.assertIn("MEMORY.md", manifest["required_public_reads"])
        self.assertIn("docs/APPLICATION_EXECUTION_CONTRACT.md", manifest["required_public_reads"])
        self.assertIn("agent_context/context.md", manifest["required_public_reads"])
        self.assertIn("docs/WRITER_AUTHORIZATION_RECEIPT.md", manifest["required_public_reads"])
        self.assertIn("Drive:Work_Leases:UNEXPIRED_ONLY", manifest["required_private_reads"])
        self.assertIn("Drive:Agent_Inbox:GLOBAL_BARRIER_STATE", manifest["required_private_reads"])
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
            sequence.index("RESOLVE_GLOBAL_BARRIERS"),
        )
        self.assertLess(
            sequence.index("RESOLVE_GLOBAL_BARRIERS"),
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
        self.assertLess(
            sequence.index("ACQUIRE_SMALLEST_SAFE_LEASE"),
            sequence.index("RECHECK_GLOBAL_BARRIER"),
        )
        self.assertLess(
            sequence.index("RECHECK_GLOBAL_BARRIER"),
            sequence.index("EXECUTE_BOUNDED_TRANSITION"),
        )

    def test_manifest_migration_is_nonretroactive_and_external_side_effects_stay_separate(self):
        manifest = json.loads((ROOT / "agent_context/bootstrap_manifest.json").read_text())
        migration = manifest["migration"]
        self.assertEqual(migration["receipt_enforcement"], "NON_RETROACTIVE")
        self.assertIn("no existing lease is retroactively invalidated", migration["existing_sessions"])
        self.assertIn("separately versioned capability", migration["external_side_effects"])
        self.assertIn("execution contract", migration["application_execution_required_read"])
        shortcuts = manifest["forbidden_bootstrap_shortcuts"]
        self.assertIn(
            "acquire_post_v1_1_write_lease_without_WRITER_AUTHORIZATION_GRANTED_receipt",
            shortcuts,
        )
        self.assertIn("treat_writer_authorization_receipt_as_domain_authority", shortcuts)
        self.assertIn("treat_writer_authorization_receipt_as_external_capability", shortcuts)
        self.assertIn("choose_nonblocking_architecture_over_safe_live_application_execution", shortcuts)
        self.assertIn("acquire_write_lease_without_complete_fresh_global_barrier_snapshot", shortcuts)
        self.assertIn("execute_irreversible_effect_without_fresh_global_barrier_recheck", shortcuts)

    def test_agents_enforces_manifest_memory_and_handshake(self):
        agents = (ROOT / "AGENTS.md").read_text()
        for marker in [
            "agent_context/bootstrap_manifest.json",
            "MEMORY.md",
            "BOOTSTRAP_CONTEXT_LOADED",
            "agent_context/context.md",
            "currently unexpired",
            "Unregistered sessions are read-only",
            "Safe live application execution outranks non-blocking architecture",
            "5 days / 120 hours",
            "global barrier",
        ]:
            self.assertIn(marker, agents)

    def test_next_router_points_to_execution_contract(self):
        router = (ROOT / "agent_context/NEXT.md").read_text()
        for marker in [
            "docs/APPLICATION_EXECUTION_CONTRACT.md",
            "Execution-first selection law",
            "architecture activity != application outcome",
            "unknown send outcome != permission to resend",
        ]:
            self.assertIn(marker, router)

    def test_execution_contract_contains_durable_outreach_invariants(self):
        contract = (ROOT / "docs/APPLICATION_EXECUTION_CONTRACT.md").read_text()
        for marker in [
            "Outcome-first law",
            "One opportunity, one outbound identity",
            "Route resolution before outreach",
            "5 days / 120 hours",
            "signature",
            "CAPTURE_ALL_STEPS",
            "EMAIL_CANDIDATURE_SENT",
            "FORM_SUBMITTED",
            "Throughput metrics",
        ]:
            self.assertIn(marker, contract)

    def test_deathsafe_router_is_execution_first_not_historical_semantic_backlog(self):
        router = (ROOT / "agent_context/NEXT_DEATHSAFE.md").read_text()
        for marker in [
            "EXECUTION-FIRST",
            "Execution-first frontier selection",
            "docs/APPLICATION_EXECUTION_CONTRACT.md",
            "do not execute historical semantic P0s without a fresh demonstrated need",
            "Then execute — do not return to architecture by habit.",
        ]:
            self.assertIn(marker, router)
        self.assertNotIn("## 19. Immediate P0 frontier", router)
        self.assertNotIn("P0-A — exact binary/model durability", router)

    def test_mandatory_control_docs_have_entropy_budget(self):
        ceilings = {
            "AGENTS.md": 15000,
            "MEMORY.md": 12000,
            "agent_context/NEXT_DEATHSAFE.md": 12000,
        }
        for path, ceiling in ceilings.items():
            with self.subTest(path=path):
                size = len((ROOT / path).read_text().encode("utf-8"))
                self.assertLessEqual(size, ceiling, f"{path} exceeded the cold-start entropy budget")

    def test_handoff_points_zero_context_agents_to_manifest_and_memory(self):
        handoff = (ROOT / "HANDOFF.md").read_text()
        for marker in ["agent_context/bootstrap_manifest.json", "MEMORY.md", "BOOTSTRAP_CONTEXT_LOADED"]:
            self.assertIn(marker, handoff)

    def test_memory_is_explicitly_non_authoritative_nonvolatile_and_execution_aware(self):
        memory = (ROOT / "MEMORY.md").read_text()
        for marker in [
            "Durable semantic memory, not live state",
            "Do **not** store live counts",
            "Chat memory is never the continuity system",
            "BOOTSTRAP_CONTEXT_LOADED",
            "SubmissionAttempt != SubmissionReceipt",
            "Safe live execution outranks non-blocking architecture",
            "Unknown prior-send outcome",
            "5 days / 120 hours",
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
            "global barrier",
        ]:
            self.assertIn(marker, protocol)


if __name__ == "__main__":
    unittest.main()
