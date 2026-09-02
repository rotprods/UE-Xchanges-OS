import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.control_plane_health import LeaseHealthRecord, SessionHealthRecord, evaluate_control_plane_health
from uexchanges.reliability_watchdog import (
    AlertPhase,
    AlertSeverity,
    PreviousAlertState,
    evaluate_reliability_watchdog,
)
from uexchanges.recovery_verifier import (
    RecoveryArtifact,
    verify_recovery,
)

NOW = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)


def health_with_expired_lease():
    return evaluate_control_plane_health(
        now=NOW,
        sessions=(
            SessionHealthRecord("s1", "a1", "ctx", NOW - timedelta(hours=1), NOW - timedelta(minutes=1), "ACTIVE"),
        ),
        leases=(
            LeaseHealthRecord(
                "l1", "s1", "a1", "ctx", "scope", NOW - timedelta(hours=1),
                NOW - timedelta(seconds=1), NOW - timedelta(minutes=5), "ACTIVE"
            ),
        ),
    )


def recovery_missing_artifact():
    return verify_recovery(
        now=NOW,
        current_main_sha="a" * 40,
        event_watermark="E1",
        required_public_paths=("goal.md",),
        manifest_required_reads=("goal.md",),
        artifacts=(RecoveryArtifact("goal.md", False, "mission"),),
        private_sources_available={
            "Context_Registry": True,
            "Agent_Sessions": True,
            "Work_Leases": True,
            "Agent_Event_Bus": True,
            "RuntimeGraphV2CommandCenter": True,
        },
        command_center_available=True,
    )


class ReliabilityWatchdogTests(unittest.TestCase):
    def test_new_alert_contains_reconciliation_plan(self):
        report = evaluate_reliability_watchdog(now=NOW, health=health_with_expired_lease())
        active = [item for item in report.alerts if item.phase is not AlertPhase.RESOLVED]
        self.assertTrue(active)
        alert = active[0]
        self.assertEqual(alert.phase, AlertPhase.NEW)
        self.assertTrue(alert.reconciliation_plan_id.startswith("RPL-"))
        self.assertFalse(report.auto_remediation)

    def test_same_alert_persists_and_increments_count(self):
        first = evaluate_reliability_watchdog(now=NOW, health=health_with_expired_lease())
        second = evaluate_reliability_watchdog(
            now=NOW + timedelta(minutes=1),
            health=health_with_expired_lease(),
            previous=first.next_state(),
        )
        active = [item for item in second.alerts if item.phase is not AlertPhase.RESOLVED]
        self.assertEqual(active[0].phase, AlertPhase.PERSISTING)
        self.assertEqual(active[0].occurrence_count, 2)

    def test_changed_fingerprint_updates_alert(self):
        first = evaluate_reliability_watchdog(now=NOW, health=health_with_expired_lease())
        previous = first.next_state()[0]
        modified = PreviousAlertState(
            alert_key=previous.alert_key,
            fingerprint="0" * 64,
            severity=previous.severity,
            occurrence_count=previous.occurrence_count,
        )
        second = evaluate_reliability_watchdog(
            now=NOW + timedelta(minutes=1), health=health_with_expired_lease(), previous=(modified,)
        )
        active = [item for item in second.alerts if item.phase is not AlertPhase.RESOLVED]
        self.assertEqual(active[0].phase, AlertPhase.UPDATED)

    def test_previous_alert_resolves_when_finding_disappears(self):
        first = evaluate_reliability_watchdog(now=NOW, health=health_with_expired_lease())
        clean = evaluate_control_plane_health(now=NOW, sessions=(), leases=())
        second = evaluate_reliability_watchdog(
            now=NOW + timedelta(minutes=1), health=clean, previous=first.next_state()
        )
        self.assertEqual(len(second.alerts), 1)
        self.assertEqual(second.alerts[0].phase, AlertPhase.RESOLVED)
        self.assertEqual(second.active_alert_count, 0)

    def test_recovery_finding_is_alerted_as_critical(self):
        clean = evaluate_control_plane_health(now=NOW, sessions=(), leases=())
        report = evaluate_reliability_watchdog(
            now=NOW, health=clean, recovery=recovery_missing_artifact()
        )
        self.assertEqual(report.critical_active_count, 1)
        self.assertEqual(report.alerts[0].severity, AlertSeverity.CRITICAL)
        self.assertEqual(report.alerts[0].source_kind, "recovery")

    def test_generator_previous_state_is_supported(self):
        first = evaluate_reliability_watchdog(now=NOW, health=health_with_expired_lease())
        generator = (item for item in first.next_state())
        second = evaluate_reliability_watchdog(
            now=NOW + timedelta(minutes=1), health=health_with_expired_lease(), previous=generator
        )
        self.assertEqual(second.active_alert_count, first.active_alert_count)


if __name__ == "__main__":
    unittest.main()
