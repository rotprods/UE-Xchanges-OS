import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.recovery_drill import DrillStatus, RecoveryObjective, record_recovery_drill
from uexchanges.recovery_manifest import PrivateRecoverySource, RecoveryArtifactDigest, build_recovery_manifest
from uexchanges.recovery_verifier import RecoveryStatus

START = datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc)


def manifest():
    return build_recovery_manifest(
        generated_at=START,
        current_main_sha="a" * 40,
        event_watermark="EVT-3",
        bootstrap_manifest_version="1.0.0",
        command_center_ref="drive:cc",
        command_center_watermark="EVT-2",
        public_artifacts=(RecoveryArtifactDigest("goal.md", "b" * 64, "mission"),),
        private_sources=(PrivateRecoverySource("Agent_Event_Bus", True, "EVT-3"),),
    )


class RecoveryDrillTests(unittest.TestCase):
    def test_measured_pass_requires_full_event_inventory_and_steps(self):
        report = record_recovery_drill(
            drill_id="DRILL-1",
            started_at=START,
            completed_at=START + timedelta(seconds=180),
            manifest=manifest(),
            source_event_ids=("E1", "E2", "E3"),
            recovered_event_ids=("E1", "E2", "E3"),
            required_steps={"main": True, "event_bus": True, "leases": True, "command_center": True},
            recovery_status=RecoveryStatus.RECOVERABLE,
        )
        self.assertEqual(report.status, DrillStatus.PASS)
        self.assertTrue(report.measured_rpo_zero)
        self.assertEqual(report.event_loss_count, 0)
        self.assertEqual(report.rto_seconds, 180)

    def test_missing_event_fails_rpo_and_cannot_claim_zero(self):
        report = record_recovery_drill(
            drill_id="DRILL-2",
            started_at=START,
            completed_at=START + timedelta(seconds=100),
            manifest=manifest(),
            source_event_ids=("E1", "E2"),
            recovered_event_ids=("E1",),
            required_steps={"main": True},
            recovery_status=RecoveryStatus.RECOVERABLE,
        )
        self.assertEqual(report.status, DrillStatus.FAIL_RPO)
        self.assertFalse(report.measured_rpo_zero)
        self.assertEqual(report.missing_event_ids, ("E2",))

    def test_slow_recovery_fails_rto(self):
        report = record_recovery_drill(
            drill_id="DRILL-3",
            started_at=START,
            completed_at=START + timedelta(seconds=301),
            manifest=manifest(),
            source_event_ids=("E1",),
            recovered_event_ids=("E1",),
            required_steps={"main": True},
            recovery_status=RecoveryStatus.RECOVERABLE,
        )
        self.assertEqual(report.status, DrillStatus.FAIL_RTO)

    def test_degraded_recovery_does_not_pass_objective(self):
        report = record_recovery_drill(
            drill_id="DRILL-4",
            started_at=START,
            completed_at=START + timedelta(seconds=10),
            manifest=manifest(),
            source_event_ids=("E1",),
            recovered_event_ids=("E1",),
            required_steps={"main": True},
            recovery_status=RecoveryStatus.DEGRADED,
        )
        self.assertEqual(report.status, DrillStatus.FAIL_RECOVERY)

    def test_failed_step_is_explicit(self):
        report = record_recovery_drill(
            drill_id="DRILL-5",
            started_at=START,
            completed_at=START + timedelta(seconds=10),
            manifest=manifest(),
            source_event_ids=("E1",),
            recovered_event_ids=("E1",),
            required_steps={"main": True, "leases": False},
            recovery_status=RecoveryStatus.RECOVERABLE,
        )
        self.assertEqual(report.status, DrillStatus.FAIL_STEPS)

    def test_no_source_event_inventory_is_rejected(self):
        with self.assertRaises(ValueError):
            record_recovery_drill(
                drill_id="DRILL-6",
                started_at=START,
                completed_at=START + timedelta(seconds=10),
                manifest=manifest(),
                source_event_ids=(),
                recovered_event_ids=(),
                required_steps={"main": True},
                recovery_status=RecoveryStatus.RECOVERABLE,
            )

    def test_custom_objective_is_enforced(self):
        report = record_recovery_drill(
            drill_id="DRILL-7",
            started_at=START,
            completed_at=START + timedelta(seconds=61),
            manifest=manifest(),
            source_event_ids=("E1", "E2"),
            recovered_event_ids=("E1",),
            required_steps={"main": True},
            recovery_status=RecoveryStatus.RECOVERABLE,
            objective=RecoveryObjective(max_rto_seconds=60, max_event_loss=1),
        )
        self.assertEqual(report.status, DrillStatus.FAIL_RTO)
        self.assertFalse(report.measured_rpo_zero)


if __name__ == "__main__":
    unittest.main()
