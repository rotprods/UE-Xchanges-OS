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
from uexchanges.global_barrier import (
    BarrierRecord,
    BarrierState,
    resolve_global_barriers,
)
from uexchanges.writer_authorization import (
    AuthorizationCode,
    WriteIntent,
    WriterAuthorizationPolicy,
    authorize_writer,
)

NOW = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
MAIN = "a" * 40
PROJECT = "UE-Xchanges-OS"


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


def lease(scope="github:new/path"):
    return LeaseSnapshot(
        lease_id="l1",
        owner_session_id="s1",
        owner_agent_id="a1",
        context_id="ctx",
        scope=scope,
        acquired_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(minutes=30),
        status="ACTIVE",
    )


def prelease(watermark="E1"):
    return PreLeaseRefresh(MAIN, NOW - timedelta(seconds=2), watermark)


def policy():
    return WriterAuthorizationPolicy(
        BootstrapPolicy("1.0.0", MAIN, "ctx", NOW - timedelta(days=1)),
        project_id=PROJECT,
    )


def barrier(
    *,
    intent=WriteIntent.VERSIONED_CODE,
    scope="github:new/path",
    watermark="E1",
    observed_at=NOW,
    records=(),
    complete=True,
):
    return resolve_global_barriers(
        records=records,
        project_id=PROJECT,
        context_id="ctx",
        intent=intent.value,
        scope=scope,
        observed_at=observed_at,
        event_watermark=watermark,
        source_complete=complete,
    )


def active_barrier(*, revision=1, state=BarrierState.ACTIVE, intents=("VERSIONED_CODE",)):
    return BarrierRecord(
        barrier_id="BAR-C0",
        revision=revision,
        event_id=f"EVT-BAR-{revision}-{state.value}",
        project_id=PROJECT,
        context_id="ctx",
        state=state,
        blocked_intents=tuple(sorted(intents)),
        updated_at=NOW,
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


def decide(**changes):
    values = dict(
        policy=policy(),
        session=session(),
        ack=ack(),
        proposed_lease=lease(),
        prelease=prelease(),
        health=clean_health(),
        global_barrier=barrier(),
        now=NOW,
        intent=WriteIntent.VERSIONED_CODE,
    )
    values.update(changes)
    return authorize_writer(**values)


class WriterAuthorizationTests(unittest.TestCase):
    def test_clean_versioned_code_writer_is_coordination_allowed(self):
        decision = decide()
        self.assertTrue(decision.coordination_allowed)
        self.assertEqual(decision.codes, (AuthorizationCode.ALLOWED,))
        self.assertFalse(decision.is_domain_authority)
        self.assertFalse(decision.is_external_capability)
        self.assertIsNotNone(decision.global_barrier_revision_sha256)

    def test_missing_bootstrap_ack_denies(self):
        decision = decide(ack=None)
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.BOOTSTRAP_DENIED, decision.codes)

    def test_overlap_denies_even_when_bootstrap_health_and_barrier_pass(self):
        decision = decide(overlapping_unexpired_lease_ids=("other",))
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.OVERLAPPING_LEASE, decision.codes)

    def test_stale_health_report_denies(self):
        old = clean_health(generated_at=NOW - timedelta(minutes=10))
        decision = decide(health=old)
        self.assertIn(AuthorizationCode.HEALTH_REPORT_STALE, decision.codes)

    def test_external_side_effect_is_never_authorized_by_coordination_broker(self):
        ext_barrier = barrier(intent=WriteIntent.EXTERNAL_SIDE_EFFECT)
        decision = decide(intent=WriteIntent.EXTERNAL_SIDE_EFFECT, global_barrier=ext_barrier)
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(
            AuthorizationCode.EXTERNAL_SIDE_EFFECT_REQUIRES_SEPARATE_CAPABILITY,
            decision.codes,
        )

    def test_control_plane_repair_requires_reconciliation_plan(self):
        repair_barrier = barrier(intent=WriteIntent.CONTROL_PLANE_REPAIR)
        denied = decide(intent=WriteIntent.CONTROL_PLANE_REPAIR, global_barrier=repair_barrier)
        self.assertIn(AuthorizationCode.REPAIR_PLAN_REQUIRED, denied.codes)
        allowed = decide(
            intent=WriteIntent.CONTROL_PLANE_REPAIR,
            repair_plan_id="RPL-0123456789abcdef",
            global_barrier=repair_barrier,
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
        domain_barrier = barrier(intent=WriteIntent.CANONICAL_DOMAIN)
        decision = decide(
            health=broken,
            intent=WriteIntent.CANONICAL_DOMAIN,
            global_barrier=domain_barrier,
        )
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.REQUIRED_SLO_FAILED, decision.codes)

    def test_missing_global_barrier_authority_denies_clean_writer(self):
        decision = decide(global_barrier=None)
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.GLOBAL_BARRIER_UNKNOWN, decision.codes)

    def test_incomplete_global_barrier_authority_denies_clean_writer(self):
        decision = decide(global_barrier=barrier(complete=False))
        self.assertIn(AuthorizationCode.GLOBAL_BARRIER_UNKNOWN, decision.codes)

    def test_active_global_barrier_beats_zero_overlap(self):
        item = barrier(records=(active_barrier(),))
        decision = decide(global_barrier=item, overlapping_unexpired_lease_ids=())
        self.assertFalse(decision.coordination_allowed)
        self.assertIn(AuthorizationCode.GLOBAL_BARRIER_ACTIVE, decision.codes)
        self.assertEqual(decision.active_global_barrier_ids, ("BAR-C0",))

    def test_stale_global_barrier_snapshot_denies(self):
        item = barrier(observed_at=NOW - timedelta(seconds=121))
        decision = decide(global_barrier=item)
        self.assertIn(AuthorizationCode.GLOBAL_BARRIER_STALE, decision.codes)

    def test_global_barrier_watermark_must_equal_prelease_event_cut(self):
        item = barrier(watermark="E2")
        decision = decide(global_barrier=item)
        self.assertIn(AuthorizationCode.GLOBAL_BARRIER_WATERMARK_MISMATCH, decision.codes)

    def test_global_barrier_scope_mismatch_denies(self):
        item = barrier(scope="github:other")
        decision = decide(global_barrier=item)
        self.assertIn(AuthorizationCode.GLOBAL_BARRIER_MISMATCH, decision.codes)

    def test_explicit_release_allows_fresh_new_authorization(self):
        records = (
            active_barrier(revision=1, state=BarrierState.ACTIVE),
            active_barrier(revision=2, state=BarrierState.RELEASED),
        )
        item = barrier(records=records)
        decision = decide(global_barrier=item)
        self.assertTrue(decision.coordination_allowed)

    def test_decision_digest_is_deterministic_and_barrier_bound(self):
        first = decide()
        second = decide()
        self.assertEqual(first.decision_digest, second.decision_digest)
        released = barrier(
            records=(active_barrier(revision=1, state=BarrierState.RELEASED),)
        )
        changed = decide(global_barrier=released)
        self.assertNotEqual(first.decision_digest, changed.decision_digest)


if __name__ == "__main__":
    unittest.main()
