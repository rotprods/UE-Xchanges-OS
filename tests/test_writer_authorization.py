import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
)
from uexchanges.control_plane_health import (
    HealthPolicy,
    LeaseHealthRecord,
    SessionHealthRecord,
    evaluate_control_plane_health,
)
from uexchanges.writer_authorization import (
    AuthorizationCode,
    WriteIntent,
    WriterAuthorizationPolicy,
    authorize_writer,
)

NOW = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
MAIN = "a" * 40


def session():
    return SessionSnapshot("s1", "a1", "ctx", NOW - timedelta(minutes=5), "ACTIVE")


def ack():
    return BootstrapAckSnapshot(
        event_id="E-ACK",
        event_at=NOW - timedelta(seconds=20),
        manifest_version="1.0.0",
        observed_main_sha="b" * 40,
        context_id="ctx",
        agent_id="a1",
        session_id="s1",
        private_event_watermark="E0",
        lease_scan_at=NOW - timedelta(seconds=21),
        public_read_refs=("goal.md", "AGENTS.md"),
    )


def lease():
    return LeaseSnapshot(
        lease_id="l1",
        owner_session_id="s1",
        owner_agent_id="a1",
        context_id="ctx",
        scope="github:new/path",
        acquired_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(minutes=30),
        status="ACTIVE",
    )


def prelease():
    return PreLeaseRefresh(MAIN, NOW - timedelta(seconds=2), "E1")


def policy():
    return WriterAuthorizationPolicy(
        BootstrapPolicy("1.0.0", MAIN, "ctx", NOW - timedelta(days=1))
    )


def clean_health(*, generated_at=NOW):
    return evaluate_control_plane_health(
        now=generated_at,
        sessions=(
            SessionHealthRecord(
                "s1", "a1", "ctx", NOW - timedelta(minutes=5), NOW - timedelta(seconds=10), "ACTIVE"
            ),
        ),
        leases=(
            LeaseHealthRecord(
                "l1", "s1", "a1", "ctx", "github:new/path",
                NOW - timedelta(seconds=1), NOW + timedelta(minutes=30), NOW - timedelta(seconds=1), "ACTIVE"
            ),
        ),
        policy=HealthPolicy(),
    )


class WriterAuthorizationTests(unittest.TestCase):
    def test_clean_versioned_code_writer_is_coordination_allowed(self):
        decision = authorize_writer(
            policy=policy(),
            session=session(),
            ack=ack(),
            proposed_lease=lease(),
            prelease=prelease(),
            health=clean_health(),
            now=NOW,
            intent=WriteIntent.VERSIONED_CODE,
        )
        self.assertTrue(decision.coordination_allowed)
        self.assertEqual(decision.codes, (AuthorizationCode.ALLOWED,))
        self.assertFalse(decision.is_domain_authority)
        self.assertFalse(decision.is_external_capability)

    def test_missing_bootstrap_ack_denies(self):
        decision = authorize_writer(
            policy=policy(), session=session(), ack=None, proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
        )
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.BOOTSTRAP_DENIED, decision.codes)

    def test_overlap_denies_even_when_bootstrap_and_health_pass(self):
        decision = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
            overlapping_unexpired_lease_ids=("other",),
        )
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.OVERLAPPING_LEASE, decision.codes)

    def test_stale_health_report_denies(self):
        old = clean_health(generated_at=NOW - timedelta(minutes=10))
        decision = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=old, now=NOW,
        )
        self.assertIn(AuthorizationCode.HEALTH_REPORT_STALE, decision.codes)

    def test_external_side_effect_is_never_authorized_by_coordination_broker(self):
        decision = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
            intent=WriteIntent.EXTERNAL_SIDE_EFFECT,
        )
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(
            AuthorizationCode.EXTERNAL_SIDE_EFFECT_REQUIRES_SEPARATE_CAPABILITY,
            decision.codes,
        )

    def test_control_plane_repair_requires_reconciliation_plan(self):
        denied = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
            intent=WriteIntent.CONTROL_PLANE_REPAIR,
        )
        self.assertIn(AuthorizationCode.REPAIR_PLAN_REQUIRED, denied.codes)
        allowed = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
            intent=WriteIntent.CONTROL_PLANE_REPAIR,
            repair_plan_id="RPL-0123456789abcdef",
        )
        self.assertTrue(allowed.coordination_allowed)

    def test_failed_required_health_slo_denies_canonical_write(self):
        broken = evaluate_control_plane_health(
            now=NOW,
            sessions=(
                SessionHealthRecord("s1", "a1", "ctx", NOW - timedelta(minutes=5), NOW - timedelta(seconds=1), "ACTIVE"),
                SessionHealthRecord("s1", "a2", "ctx", NOW - timedelta(minutes=4), NOW - timedelta(seconds=1), "ACTIVE"),
            ),
            leases=(),
        )
        decision = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=broken, now=NOW,
            intent=WriteIntent.CANONICAL_DOMAIN,
        )
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.REQUIRED_SLO_FAILED, decision.codes)

    def test_decision_digest_is_deterministic(self):
        first = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
        )
        second = authorize_writer(
            policy=policy(), session=session(), ack=ack(), proposed_lease=lease(),
            prelease=prelease(), health=clean_health(), now=NOW,
        )
        self.assertEqual(first.decision_digest, second.decision_digest)


if __name__ == "__main__":
    unittest.main()
