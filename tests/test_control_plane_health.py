import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.control_plane_health import (
    ContextHealthRecord,
    EffectiveLeaseState,
    HealthCode,
    LeaseHealthRecord,
    OverallHealth,
    ProjectionHealthRecord,
    SessionHealthRecord,
    effective_lease_state,
    evaluate_control_plane_health,
)

NOW = datetime(2026, 9, 2, 9, 30, tzinfo=timezone.utc)


def session(*, sid="s1", agent="a1", status="ACTIVE", heartbeat=None, started_at=None):
    return SessionHealthRecord(
        session_id=sid,
        agent_id=agent,
        context_id="ctx",
        started_at=started_at or NOW - timedelta(minutes=10),
        last_heartbeat=heartbeat or NOW - timedelta(minutes=1),
        status=status,
    )


def lease(*, lid="l1", sid="s1", agent="a1", status="ACTIVE", expires=None, heartbeat=None, scope="github:x"):
    return LeaseHealthRecord(
        lease_id=lid,
        owner_session_id=sid,
        owner_agent_id=agent,
        context_id="ctx",
        scope=scope,
        acquired_at=NOW - timedelta(minutes=5),
        expires_at=expires or NOW + timedelta(minutes=30),
        last_heartbeat=heartbeat or NOW - timedelta(minutes=1),
        status=status,
    )


class ControlPlaneHealthTests(unittest.TestCase):
    def test_clean_snapshot_is_green(self):
        report = evaluate_control_plane_health(
            now=NOW,
            sessions=(session(),),
            leases=(lease(),),
            contexts=(ContextHealthRecord("ctx", NOW - timedelta(hours=1), "ACTIVE", "evt"),),
            projections=(ProjectionHealthRecord("Command_Center", NOW - timedelta(minutes=5), "evt"),),
        )
        self.assertEqual(report.overall, OverallHealth.GREEN)
        self.assertFalse(report.findings)
        self.assertTrue(all(item.passed for item in report.slos))

    def test_expired_active_row_is_not_effective_fence(self):
        row = lease(expires=NOW - timedelta(seconds=1))
        self.assertEqual(
            effective_lease_state(row, session=session(), now=NOW),
            EffectiveLeaseState.EXPIRED_STALE_ROW,
        )
        report = evaluate_control_plane_health(now=NOW, sessions=(session(),), leases=(row,))
        codes = {item.code for item in report.findings}
        self.assertIn(HealthCode.ACTIVE_LEASE_EXPIRED_STALE_ROW, codes)
        self.assertEqual(report.metrics["effective_active_leases"], 0)
        self.assertEqual(report.metrics["stale_active_lease_rows"], 1)
        self.assertEqual(report.overall, OverallHealth.AMBER)

    def test_active_lease_owned_by_completed_session_is_orphaned(self):
        closed = session(status="COMPLETED")
        row = lease()
        self.assertEqual(
            effective_lease_state(row, session=closed, now=NOW),
            EffectiveLeaseState.ORPHANED_OWNER_CLOSED,
        )
        report = evaluate_control_plane_health(now=NOW, sessions=(closed,), leases=(row,))
        self.assertIn(HealthCode.ACTIVE_LEASE_OWNER_CLOSED, {item.code for item in report.findings})
        self.assertEqual(report.metrics["orphaned_active_lease_rows"], 1)

    def test_missing_owner_and_agent_mismatch_fail_fencing_slo(self):
        report = evaluate_control_plane_health(
            now=NOW,
            sessions=(session(agent="a1"),),
            leases=(
                lease(lid="missing", sid="missing", agent="ghost"),
                lease(lid="mismatch", agent="wrong"),
            ),
        )
        codes = {item.code for item in report.findings}
        self.assertIn(HealthCode.ACTIVE_LEASE_OWNER_MISSING, codes)
        self.assertIn(HealthCode.LEASE_AGENT_MISMATCH, codes)
        self.assertEqual(report.overall, OverallHealth.RED)
        self.assertFalse(next(item for item in report.slos if item.name == "lease_fencing_integrity").passed)

    def test_duplicate_session_id_is_critical(self):
        report = evaluate_control_plane_health(
            now=NOW,
            sessions=(session(), session(agent="a2")),
            leases=(),
        )
        self.assertIn(HealthCode.SESSION_ID_REUSED, {item.code for item in report.findings})
        self.assertEqual(report.overall, OverallHealth.RED)

    def test_stale_context_projection_bootstrap_and_dead_letter_are_visible(self):
        report = evaluate_control_plane_health(
            now=NOW,
            sessions=(
                session(
                    started_at=NOW - timedelta(hours=2),
                    heartbeat=NOW - timedelta(hours=1),
                ),
            ),
            leases=(),
            contexts=(ContextHealthRecord("ctx", NOW - timedelta(days=2), "ACTIVE"),),
            projections=(ProjectionHealthRecord("Command_Center", NOW - timedelta(hours=2), "old"),),
            bootstrap_noncompliant_count=1,
            dead_letter_count=2,
        )
        codes = {item.code for item in report.findings}
        self.assertTrue(
            {
                HealthCode.SESSION_HEARTBEAT_STALE,
                HealthCode.CONTEXT_REGISTRY_STALE,
                HealthCode.PROJECTION_STALE,
                HealthCode.BOOTSTRAP_NONCOMPLIANT,
                HealthCode.DEAD_LETTER_PRESENT,
            }.issubset(codes)
        )
        self.assertEqual(report.overall, OverallHealth.RED)

    def test_empty_scope_is_critical(self):
        report = evaluate_control_plane_health(
            now=NOW,
            sessions=(session(),),
            leases=(lease(scope=" "),),
        )
        self.assertIn(HealthCode.LEASE_SCOPE_EMPTY, {item.code for item in report.findings})
        self.assertEqual(report.overall, OverallHealth.RED)


if __name__ == "__main__":
    unittest.main()
