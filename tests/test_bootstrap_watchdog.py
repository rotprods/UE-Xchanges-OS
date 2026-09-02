import unittest

from uexchanges.bootstrap_guard import ComplianceFinding, GuardCode
from uexchanges.bootstrap_watchdog import (
    AlertTransition,
    PreviousAlert,
    WatchdogSeverity,
    build_watchdog_report,
    current_state_as_json,
    previous_state_from_json,
    severity_for_codes,
)


def finding(subject_id="LSE-1", *codes, subject_type="lease", session_id="SES-1", allowed=False):
    return ComplianceFinding(
        subject_type=subject_type,
        subject_id=subject_id,
        session_id=session_id,
        allowed=allowed,
        codes=tuple(codes) or (GuardCode.MISSING_BOOTSTRAP_ACK,),
    )


class BootstrapWatchdogTests(unittest.TestCase):
    def test_critical_identity_and_missing_ack(self):
        self.assertEqual(severity_for_codes((GuardCode.MISSING_BOOTSTRAP_ACK,)), WatchdogSeverity.CRITICAL)
        self.assertEqual(severity_for_codes((GuardCode.LEASE_OWNER_MISMATCH,)), WatchdogSeverity.CRITICAL)

    def test_stale_main_and_scan_are_high(self):
        self.assertEqual(severity_for_codes((GuardCode.PRELEASE_MAIN_SHA_STALE,)), WatchdogSeverity.HIGH)
        self.assertEqual(severity_for_codes((GuardCode.LEASE_SCAN_STALE,)), WatchdogSeverity.HIGH)

    def test_legacy_and_compliant_findings_do_not_open_alerts(self):
        report = build_watchdog_report(
            [
                finding("old", GuardCode.LEGACY_PRE_CONTRACT),
                finding("ok", GuardCode.COMPLIANT, allowed=True),
            ]
        )
        self.assertTrue(report.healthy)
        self.assertEqual(report.open_alerts, ())

    def test_new_high_alert_notifies_once(self):
        report = build_watchdog_report([finding("LSE-1", GuardCode.PRELEASE_MAIN_SHA_STALE)])
        self.assertEqual(report.open_alerts[0].transition, AlertTransition.NEW)
        self.assertTrue(report.open_alerts[0].notify)
        previous = report.current_state
        second = build_watchdog_report(
            [finding("LSE-1", GuardCode.PRELEASE_MAIN_SHA_STALE)], previous=previous
        )
        self.assertEqual(second.open_alerts[0].transition, AlertTransition.PERSISTING)
        self.assertFalse(second.open_alerts[0].notify)

    def test_changed_reason_or_severity_becomes_updated(self):
        first = build_watchdog_report([finding("LSE-1", GuardCode.LEASE_SCAN_STALE)])
        second = build_watchdog_report(
            [finding("LSE-1", GuardCode.LEASE_OWNER_MISMATCH)],
            previous=first.current_state,
        )
        alert = second.open_alerts[0]
        self.assertEqual(alert.transition, AlertTransition.UPDATED)
        self.assertEqual(alert.severity, WatchdogSeverity.CRITICAL)
        self.assertTrue(alert.notify)

    def test_resolved_high_alert_notifies_resolution(self):
        first = build_watchdog_report([finding("LSE-1", GuardCode.LEASE_SCAN_STALE)])
        resolved = build_watchdog_report([], previous=first.current_state)
        self.assertEqual(len(resolved.alerts), 1)
        alert = resolved.alerts[0]
        self.assertEqual(alert.transition, AlertTransition.RESOLVED)
        self.assertTrue(alert.notify)
        self.assertTrue(resolved.healthy)

    def test_warning_resolution_is_silent(self):
        first = build_watchdog_report([finding("LSE-1", GuardCode.LEASE_EXPIRED)])
        self.assertFalse(first.notifications)
        resolved = build_watchdog_report([], previous=first.current_state)
        self.assertFalse(resolved.notifications)

    def test_recommendations_are_specific(self):
        session_reuse = build_watchdog_report([
            finding("SES-X", GuardCode.SESSION_REUSED, subject_type="session", session_id="SES-X")
        ]).open_alerts[0]
        self.assertIn("FRESH_SESSION", session_reuse.recommended_action)
        stale = build_watchdog_report([
            finding("LSE-X", GuardCode.MISSING_PRELEASE_REFRESH)
        ]).open_alerts[0]
        self.assertIn("ACQUIRE_NEW_FENCE", stale.recommended_action)

    def test_state_json_roundtrip(self):
        report = build_watchdog_report([finding("LSE-1", GuardCode.MISSING_BOOTSTRAP_ACK)])
        encoded = current_state_as_json(report)
        decoded = previous_state_from_json(encoded)
        self.assertEqual(decoded["lease:LSE-1"].fingerprint, report.open_alerts[0].fingerprint)
        self.assertEqual(decoded["lease:LSE-1"].severity, WatchdogSeverity.CRITICAL)

    def test_invalid_previous_state_rejected(self):
        with self.assertRaises(ValueError):
            previous_state_from_json({"lease:x": {"fingerprint": "bad", "severity": "HIGH"}})

    def test_report_counts_and_health(self):
        report = build_watchdog_report(
            [
                finding("LSE-HIGH", GuardCode.LEASE_SCAN_STALE),
                finding("LSE-WARN", GuardCode.LEASE_EXPIRED),
            ]
        )
        data = report.as_dict()
        self.assertFalse(data["healthy"])
        self.assertEqual(data["open_alert_count"], 2)
        self.assertEqual(data["open_by_severity"]["HIGH"], 1)
        self.assertEqual(data["open_by_severity"]["WARNING"], 1)


if __name__ == "__main__":
    unittest.main()
