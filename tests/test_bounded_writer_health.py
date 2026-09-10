import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
)
from uexchanges.bounded_writer_health import (
    BOUNDED_WRITER_HEALTH_SCOPE,
    LiveWriterBootstrapEvidence,
    evaluate_bounded_writer_authorization_health,
)
from uexchanges.control_plane_health import LeaseHealthRecord, SessionHealthRecord

NOW = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)
MAIN = "a" * 40


def health_session(
    session_id: str = "SES-CURRENT",
    *,
    agent_id: str = "AGT-CURRENT",
    context_id: str = "CTX-1",
    status: str = "ACTIVE",
    heartbeat_age: int = 5,
) -> SessionHealthRecord:
    return SessionHealthRecord(
        session_id=session_id,
        agent_id=agent_id,
        context_id=context_id,
        started_at=NOW - timedelta(minutes=2),
        last_heartbeat=NOW - timedelta(seconds=heartbeat_age),
        status=status,
    )


def live_health_lease(
    lease_id: str = "LSE-LIVE",
    *,
    owner_session_id: str = "SES-OWNER",
    owner_agent_id: str = "AGT-OWNER",
    context_id: str = "CTX-1",
    expires_delta: timedelta = timedelta(minutes=10),
) -> LeaseHealthRecord:
    return LeaseHealthRecord(
        lease_id=lease_id,
        owner_session_id=owner_session_id,
        owner_agent_id=owner_agent_id,
        context_id=context_id,
        scope="derived:runtimegraph",
        acquired_at=NOW - timedelta(minutes=1),
        expires_at=NOW + expires_delta,
        last_heartbeat=NOW - timedelta(seconds=10),
        status="ACTIVE",
    )


def policy(context_id: str = "CTX-1") -> BootstrapPolicy:
    return BootstrapPolicy(
        manifest_version="1.1.0",
        current_main_sha=MAIN,
        context_id=context_id,
        effective_at=NOW - timedelta(days=1),
        max_prelease_scan_age_seconds=120,
    )


def bootstrap_evidence(
    *,
    session_id: str = "SES-CURRENT",
    agent_id: str = "AGT-CURRENT",
    context_id: str = "CTX-1",
    ack: bool = True,
    prelease_scan_at: datetime | None = None,
    proposed_owner_session_id: str | None = None,
):
    session = SessionSnapshot(
        session_id=session_id,
        agent_id=agent_id,
        context_id=context_id,
        started_at=NOW - timedelta(minutes=2),
        status="ACTIVE",
    )
    ack_snapshot = (
        BootstrapAckSnapshot(
            event_id="EVT-BOOT",
            event_at=NOW - timedelta(seconds=90),
            manifest_version="1.1.0",
            observed_main_sha=MAIN,
            context_id=context_id,
            agent_id=agent_id,
            session_id=session_id,
            private_event_watermark="EVT-WM",
            lease_scan_at=NOW - timedelta(seconds=100),
            public_read_refs=("goal.md", "AGENTS.md"),
        )
        if ack
        else None
    )
    prelease = PreLeaseRefresh(
        observed_main_sha=MAIN,
        lease_scan_at=prelease_scan_at or NOW - timedelta(seconds=30),
        private_event_watermark="EVT-WM-2",
    )
    proposed = LeaseSnapshot(
        lease_id="LSE-PROPOSED",
        owner_session_id=proposed_owner_session_id or session_id,
        owner_agent_id=agent_id,
        context_id=context_id,
        scope="derived:runtimegraph",
        acquired_at=NOW + timedelta(seconds=5),
        expires_at=NOW + timedelta(minutes=20),
        status="ACTIVE",
    )
    return session, ack_snapshot, proposed, prelease


def live_bootstrap_evidence(
    health_lease: LeaseHealthRecord,
    *,
    session_status: str = "ACTIVE",
    prelease_main: str = MAIN,
) -> LiveWriterBootstrapEvidence:
    session = SessionSnapshot(
        session_id=health_lease.owner_session_id,
        agent_id=health_lease.owner_agent_id,
        context_id=health_lease.context_id,
        started_at=health_lease.acquired_at - timedelta(minutes=2),
        status=session_status,
    )
    ack = BootstrapAckSnapshot(
        event_id=f"EVT-BOOT-{health_lease.lease_id}",
        event_at=health_lease.acquired_at - timedelta(seconds=30),
        manifest_version="1.1.0",
        observed_main_sha=MAIN,
        context_id=health_lease.context_id,
        agent_id=health_lease.owner_agent_id,
        session_id=health_lease.owner_session_id,
        private_event_watermark="EVT-LIVE-WM",
        lease_scan_at=health_lease.acquired_at - timedelta(seconds=40),
        public_read_refs=("goal.md", "AGENTS.md"),
    )
    lease_snapshot = LeaseSnapshot(
        lease_id=health_lease.lease_id,
        owner_session_id=health_lease.owner_session_id,
        owner_agent_id=health_lease.owner_agent_id,
        context_id=health_lease.context_id,
        scope=health_lease.scope,
        acquired_at=health_lease.acquired_at,
        expires_at=health_lease.expires_at,
        status=health_lease.status,
    )
    prelease = PreLeaseRefresh(
        observed_main_sha=prelease_main,
        lease_scan_at=health_lease.acquired_at - timedelta(seconds=10),
        private_event_watermark="EVT-LIVE-WM-2",
    )
    return LiveWriterBootstrapEvidence(session, ack, lease_snapshot, prelease)


def evaluate(
    *,
    rows=None,
    ack: bool = True,
    prelease_scan_at: datetime | None = None,
    proposed_owner_session_id: str | None = None,
    unexpired=(),
    owners=(),
    live_bootstrap=(),
):
    bootstrap_session, bootstrap_ack, proposed, prelease = bootstrap_evidence(
        ack=ack,
        prelease_scan_at=prelease_scan_at,
        proposed_owner_session_id=proposed_owner_session_id,
    )
    return evaluate_bounded_writer_authorization_health(
        now=NOW,
        current_session_id="SES-CURRENT",
        current_session_rows=(health_session(),) if rows is None else rows,
        bootstrap_policy=policy(),
        bootstrap_session=bootstrap_session,
        bootstrap_ack=bootstrap_ack,
        proposed_lease=proposed,
        prelease=prelease,
        currently_unexpired_leases=unexpired,
        live_owner_session_rows=owners,
        live_writer_bootstrap_evidence=live_bootstrap,
    )


def slo_map(evidence):
    return {item.name: item.passed for item in evidence.report.slos}


class BoundedWriterHealthTests(unittest.TestCase):
    def test_clean_current_writer_passes_required_normal_writer_slos_without_claiming_global_hygiene(self):
        evidence = evaluate()
        slos = slo_map(evidence)
        self.assertTrue(slos["bootstrap_compliance"])
        self.assertTrue(slos["session_identity_uniqueness"])
        self.assertTrue(slos["lease_fencing_integrity"])
        self.assertEqual(evidence.scope, BOUNDED_WRITER_HEALTH_SCOPE)
        self.assertFalse(evidence.historical_hygiene_evaluated)
        self.assertEqual(evidence.bootstrap_codes, ("COMPLIANT",))
        self.assertEqual(evidence.bootstrap_noncompliant_session_ids, ())

    def test_missing_current_session_row_fails_closed_instead_of_looking_unique(self):
        with self.assertRaisesRegex(ValueError, "no rows"):
            evaluate(rows=())

    def test_duplicate_current_session_id_fails_identity_slo(self):
        evidence = evaluate(rows=(health_session(), health_session()))
        self.assertFalse(slo_map(evidence)["session_identity_uniqueness"])

    def test_missing_bootstrap_ack_is_computed_by_real_guard_and_fails_bootstrap_slo(self):
        evidence = evaluate(ack=False)
        self.assertFalse(slo_map(evidence)["bootstrap_compliance"])
        self.assertIn("MISSING_BOOTSTRAP_ACK", evidence.bootstrap_codes)
        self.assertEqual(evidence.bootstrap_noncompliant_session_ids, ("SES-CURRENT",))

    def test_stale_prelease_is_computed_by_real_guard_and_fails_bootstrap_slo(self):
        evidence = evaluate(prelease_scan_at=NOW - timedelta(seconds=121))
        self.assertFalse(slo_map(evidence)["bootstrap_compliance"])
        self.assertIn("LEASE_SCAN_STALE", evidence.bootstrap_codes)

    def test_proposed_lease_owner_mismatch_is_computed_by_real_guard(self):
        evidence = evaluate(proposed_owner_session_id="SES-OTHER")
        self.assertFalse(slo_map(evidence)["bootstrap_compliance"])
        self.assertIn("LEASE_OWNER_MISMATCH", evidence.bootstrap_codes)

    def test_registry_identity_must_match_bootstrap_session(self):
        with self.assertRaisesRegex(ValueError, "registry identity"):
            evaluate(rows=(health_session(agent_id="AGT-WRONG"),))

    def test_active_unexpired_lease_requires_exact_bootstrap_evidence(self):
        live = live_health_lease()
        with self.assertRaisesRegex(ValueError, "match ACTIVE lease IDs exactly"):
            evaluate(
                unexpired=(live,),
                owners=(health_session("SES-OWNER", agent_id="AGT-OWNER"),),
            )

    def test_extra_live_bootstrap_evidence_is_rejected(self):
        live = live_health_lease()
        with self.assertRaisesRegex(ValueError, "match ACTIVE lease IDs exactly"):
            evaluate(live_bootstrap=(live_bootstrap_evidence(live),))

    def test_unexpired_lease_with_closed_owner_fails_fencing_and_bootstrap_slos(self):
        live = live_health_lease()
        evidence = evaluate(
            unexpired=(live,),
            owners=(health_session("SES-OWNER", agent_id="AGT-OWNER", status="COMPLETED"),),
            live_bootstrap=(live_bootstrap_evidence(live, session_status="COMPLETED"),),
        )
        self.assertFalse(slo_map(evidence)["lease_fencing_integrity"])
        self.assertFalse(slo_map(evidence)["bootstrap_compliance"])
        self.assertEqual(evidence.bootstrap_noncompliant_session_ids, ("SES-OWNER",))

    def test_unexpired_lease_with_matching_active_owner_preserves_required_slos(self):
        live = live_health_lease()
        evidence = evaluate(
            unexpired=(live,),
            owners=(health_session("SES-OWNER", agent_id="AGT-OWNER"),),
            live_bootstrap=(live_bootstrap_evidence(live),),
        )
        self.assertTrue(slo_map(evidence)["lease_fencing_integrity"])
        self.assertTrue(slo_map(evidence)["bootstrap_compliance"])
        self.assertEqual(evidence.report.metrics["effective_active_leases"], 1)

    def test_live_owner_stale_main_prelease_fails_bootstrap_slo(self):
        live = live_health_lease()
        evidence = evaluate(
            unexpired=(live,),
            owners=(health_session("SES-OWNER", agent_id="AGT-OWNER"),),
            live_bootstrap=(live_bootstrap_evidence(live, prelease_main="b" * 40),),
        )
        self.assertFalse(slo_map(evidence)["bootstrap_compliance"])
        self.assertEqual(evidence.bootstrap_noncompliant_session_ids, ("SES-OWNER",))

    def test_live_lease_identity_drift_between_health_and_bootstrap_is_rejected(self):
        live = live_health_lease()
        evidence = live_bootstrap_evidence(live)
        drifted_lease = LeaseSnapshot(
            lease_id=evidence.lease.lease_id,
            owner_session_id=evidence.lease.owner_session_id,
            owner_agent_id=evidence.lease.owner_agent_id,
            context_id=evidence.lease.context_id,
            scope="different-scope",
            acquired_at=evidence.lease.acquired_at,
            expires_at=evidence.lease.expires_at,
            status=evidence.lease.status,
        )
        with self.assertRaisesRegex(ValueError, "disagrees with health lease"):
            evaluate(
                unexpired=(live,),
                owners=(health_session("SES-OWNER", agent_id="AGT-OWNER"),),
                live_bootstrap=(
                    LiveWriterBootstrapEvidence(
                        evidence.session,
                        evidence.ack,
                        drifted_lease,
                        evidence.prelease,
                    ),
                ),
            )

    def test_expired_row_is_rejected_from_unexpired_input_contract(self):
        expired = live_health_lease(expires_delta=timedelta(seconds=-1))
        with self.assertRaisesRegex(ValueError, "expired lease"):
            evaluate(unexpired=(expired,))

    def test_different_session_id_in_exact_lookup_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "different session_id"):
            evaluate(rows=(health_session("SES-WRONG"),))


if __name__ == "__main__":
    unittest.main()
