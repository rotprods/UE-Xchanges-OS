import unittest

from uexchanges.control_plane_health import HealthCode, HealthFinding, HealthSeverity
from uexchanges.reconciliation_planner import (
    RepairOperation,
    RepairRisk,
    build_reconciliation_plan,
    plan_health_finding,
    plan_recovery_finding,
)
from uexchanges.recovery_verifier import RecoveryCode, RecoveryFinding, RecoverySeverity


class ReconciliationPlannerTests(unittest.TestCase):
    def test_expired_active_lease_maps_to_scoped_plan_only_repair(self):
        finding = HealthFinding(
            HealthCode.ACTIVE_LEASE_EXPIRED_STALE_ROW,
            HealthSeverity.WARNING,
            "lease",
            "LSE-1",
            "row expired",
            "reconcile row",
        )
        plan = plan_health_finding(finding)
        self.assertEqual(plan.operation, RepairOperation.RECONCILE_LEASE_STATUS)
        self.assertEqual(plan.risk, RepairRisk.MEDIUM)
        self.assertEqual(plan.required_lease_scope, "drive:Work_Leases:LSE-1")
        self.assertFalse(plan.auto_execute)
        self.assertFalse(plan.canonical_domain_mutation)

    def test_plan_id_is_deterministic(self):
        finding = HealthFinding(
            HealthCode.CONTEXT_REGISTRY_STALE,
            HealthSeverity.WARNING,
            "context",
            "CTX-1",
            "old",
            "refresh",
        )
        self.assertEqual(plan_health_finding(finding).plan_id, plan_health_finding(finding).plan_id)

    def test_recovery_missing_artifact_never_becomes_auto_execute(self):
        plan = plan_recovery_finding(
            RecoveryFinding(
                RecoveryCode.REQUIRED_ARTIFACT_MISSING,
                RecoverySeverity.CRITICAL,
                "HANDOFF.md",
                "missing",
                "restore",
            )
        )
        self.assertEqual(plan.operation, RepairOperation.RESTORE_RECOVERY_ARTIFACT)
        self.assertEqual(plan.risk, RepairRisk.CRITICAL)
        self.assertFalse(plan.auto_execute)
        self.assertFalse(plan.canonical_domain_mutation)

    def test_plan_set_dedupes_identical_findings_and_orders_risk(self):
        low = HealthFinding(
            HealthCode.ACTIVE_LEASE_EXPIRED_STALE_ROW,
            HealthSeverity.WARNING,
            "lease",
            "LSE-1",
            "expired",
            "reconcile",
        )
        critical = HealthFinding(
            HealthCode.LEASE_AGENT_MISMATCH,
            HealthSeverity.CRITICAL,
            "lease",
            "LSE-2",
            "mismatch",
            "replace",
        )
        plans = build_reconciliation_plan(health_findings=(low, critical, low))
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0].risk, RepairRisk.CRITICAL)

    def test_all_health_codes_have_mapping(self):
        for code in HealthCode:
            finding = HealthFinding(code, HealthSeverity.WARNING, "x", f"id-{code.value}", "detail", "repair")
            plan = plan_health_finding(finding)
            self.assertFalse(plan.auto_execute)

    def test_all_recovery_codes_have_mapping(self):
        for code in RecoveryCode:
            finding = RecoveryFinding(code, RecoverySeverity.WARNING, f"subject-{code.value}", "detail", "repair")
            plan = plan_recovery_finding(finding)
            self.assertFalse(plan.auto_execute)


if __name__ == "__main__":
    unittest.main()
