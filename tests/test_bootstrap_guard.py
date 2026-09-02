import json
import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    GuardCode,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
    audit_control_plane,
    authorize_lease,
    parse_iso8601,
)

UTC = timezone.utc
T0 = datetime(2026, 9, 2, 5, 0, tzinfo=UTC)
MAIN_A = "a" * 40
MAIN_B = "b" * 40
CTX = "CTX-UEX-GLOBAL-EXPANSION-INCOME-V1"


def policy(*, main=MAIN_A):
    return BootstrapPolicy(
        manifest_version="1.0.0",
        current_main_sha=main,
        context_id=CTX,
        effective_at=T0,
        max_prelease_scan_age_seconds=120,
    )


def session(*, sid="SES-1", agent="AGT-1", status="ACTIVE", started=T0 + timedelta(minutes=1)):
    return SessionSnapshot(sid, agent, CTX, started, status)


def ack(*, sid="SES-1", agent="AGT-1", main=MAIN_A, version="1.0.0",
        at=T0 + timedelta(minutes=2), scan=None, refs=("goal.md", "AGENTS.md")):
    return BootstrapAckSnapshot(
        event_id="EVT-ACK",
        event_at=at,
        manifest_version=version,
        observed_main_sha=main,
        context_id=CTX,
        agent_id=agent,
        session_id=sid,
        private_event_watermark="EVT-PREV",
        lease_scan_at=scan or (at - timedelta(seconds=10)),
        public_read_refs=refs,
    )


def lease(*, sid="SES-1", agent="AGT-1", acquired=T0 + timedelta(minutes=3),
          status="ACTIVE", expires=None, scope="github:test"):
    return LeaseSnapshot(
        lease_id="LSE-1",
        owner_session_id=sid,
        owner_agent_id=agent,
        context_id=CTX,
        scope=scope,
        acquired_at=acquired,
        expires_at=expires or (acquired + timedelta(hours=1)),
        status=status,
    )


def refresh(*, main=MAIN_A, at=T0 + timedelta(minutes=2, seconds=50), watermark="EVT-TAIL"):
    return PreLeaseRefresh(main, at, watermark)


class BootstrapGuardTests(unittest.TestCase):
    def assertDenied(self, decision, code):
        self.assertFalse(decision.allowed)
        self.assertIn(code, decision.codes)

    def test_compliant_live_lease(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(), lease=lease(),
            prelease=refresh(), now=T0 + timedelta(minutes=4),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.codes, (GuardCode.COMPLIANT,))

    def test_full_bootstrap_ack_may_predate_unrelated_main_commit_if_prelease_is_current(self):
        decision = authorize_lease(
            policy=policy(main=MAIN_B),
            session=session(),
            ack=ack(main=MAIN_A),
            lease=lease(),
            prelease=refresh(main=MAIN_B),
            now=T0 + timedelta(minutes=4),
        )
        self.assertTrue(decision.allowed)

    def test_missing_ack_denied(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=None, lease=lease(),
            prelease=refresh(), now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.MISSING_BOOTSTRAP_ACK)

    def test_missing_prelease_refresh_denied(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(), lease=lease(),
            prelease=None, now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.MISSING_PRELEASE_REFRESH)

    def test_ack_after_lease_denied(self):
        decision = authorize_lease(
            policy=policy(), session=session(),
            ack=ack(at=T0 + timedelta(minutes=4)),
            lease=lease(acquired=T0 + timedelta(minutes=3)),
            prelease=refresh(at=T0 + timedelta(minutes=2, seconds=50)),
            now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.ACK_AFTER_LEASE)

    def test_ack_readset_scan_after_ack_denied(self):
        bad_ack = ack(
            at=T0 + timedelta(minutes=2),
            scan=T0 + timedelta(minutes=2, seconds=1),
        )
        decision = authorize_lease(
            policy=policy(), session=session(), ack=bad_ack, lease=lease(),
            prelease=refresh(), now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.ACK_READSET_TIMING_INVALID)

    def test_manifest_version_mismatch_denied(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(version="0.9.0"), lease=lease(),
            prelease=refresh(), now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.STALE_MANIFEST_VERSION)

    def test_prelease_main_must_match_current_main(self):
        decision = authorize_lease(
            policy=policy(main=MAIN_B), session=session(), ack=ack(main=MAIN_A), lease=lease(),
            prelease=refresh(main=MAIN_A), now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.PRELEASE_MAIN_SHA_STALE)

    def test_prelease_scan_must_happen_after_ack(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(), lease=lease(),
            prelease=refresh(at=T0 + timedelta(minutes=1, seconds=50)),
            now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.LEASE_SCAN_BEFORE_ACK)

    def test_prelease_scan_after_acquire_denied(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(), lease=lease(),
            prelease=refresh(at=T0 + timedelta(minutes=3, seconds=1)),
            now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.LEASE_SCAN_AFTER_ACQUIRE)

    def test_prelease_scan_too_old_denied(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(),
            lease=lease(acquired=T0 + timedelta(minutes=5)),
            prelease=refresh(at=T0 + timedelta(minutes=2, seconds=30)),
            now=T0 + timedelta(minutes=6),
        )
        self.assertDenied(decision, GuardCode.LEASE_SCAN_STALE)

    def test_owner_context_scope_and_expiry_are_fail_closed(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(),
            lease=LeaseSnapshot(
                lease_id="LSE-1", owner_session_id="SES-OTHER", owner_agent_id="AGT-OTHER",
                context_id="CTX-OTHER", scope=" ", acquired_at=T0 + timedelta(minutes=3),
                expires_at=T0 + timedelta(minutes=3, seconds=30), status="ACTIVE",
            ),
            prelease=refresh(), now=T0 + timedelta(minutes=4),
        )
        for code in (
            GuardCode.LEASE_OWNER_MISMATCH,
            GuardCode.LEASE_CONTEXT_MISMATCH,
            GuardCode.LEASE_SCOPE_EMPTY,
            GuardCode.LEASE_EXPIRED,
        ):
            self.assertIn(code, decision.codes)

    def test_released_lease_is_not_live_authority(self):
        decision = authorize_lease(
            policy=policy(), session=session(), ack=ack(),
            lease=lease(status="RELEASED"), prelease=refresh(),
            now=T0 + timedelta(minutes=4),
        )
        self.assertDenied(decision, GuardCode.LEASE_NOT_ACTIVE)

    def test_parser_accepts_json_refs(self):
        payload = {
            "manifest_version": "1.0.0",
            "observed_main_sha": MAIN_A,
            "context_id": CTX,
            "public_read_refs": ["goal.md", "AGENTS.md"],
            "private_event_watermark": "EVT-X",
            "lease_scan_at": "2026-09-02T05:01:50+00:00",
            "agent_id": "AGT-1",
            "session_id": "SES-1",
        }
        parsed = BootstrapAckSnapshot.from_event_payload(
            event_id="EVT-ACK", event_at=T0 + timedelta(minutes=2), payload=json.dumps(payload)
        )
        self.assertEqual(parsed.public_read_refs, ("goal.md", "AGENTS.md"))
        self.assertEqual(parsed.observed_main_sha, MAIN_A)

    def test_parser_rejects_missing_read_proof(self):
        payload = {
            "manifest_version": "1.0.0",
            "observed_main_sha": MAIN_A,
            "context_id": CTX,
            "private_event_watermark": "EVT-X",
            "lease_scan_at": "2026-09-02T05:01:50+00:00",
            "agent_id": "AGT-1",
            "session_id": "SES-1",
        }
        with self.assertRaises(ValueError):
            BootstrapAckSnapshot.from_event_payload(
                event_id="EVT-ACK", event_at=T0 + timedelta(minutes=2), payload=payload
            )

    def test_parse_iso_requires_timezone(self):
        with self.assertRaises(ValueError):
            parse_iso8601("2026-09-02T05:01:00")

    def test_auditor_flags_active_session_without_ack(self):
        findings = audit_control_plane(
            policy=policy(), sessions=[session()], acks=[], leases=[],
            now=T0 + timedelta(minutes=4),
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].codes, (GuardCode.MISSING_BOOTSTRAP_ACK,))

    def test_auditor_flags_session_reuse(self):
        findings = audit_control_plane(
            policy=policy(),
            sessions=[session(), session()],
            acks=[ack()], leases=[], now=T0 + timedelta(minutes=4),
        )
        self.assertTrue(any(GuardCode.SESSION_REUSED in finding.codes for finding in findings))

    def test_auditor_allows_active_lease_with_prelease_evidence(self):
        active_lease = lease()
        findings = audit_control_plane(
            policy=policy(), sessions=[session()], acks=[ack()], leases=[active_lease],
            prelease_by_lease={active_lease.lease_id: refresh()},
            now=T0 + timedelta(minutes=4),
        )
        lease_findings = [f for f in findings if f.subject_type == "lease"]
        self.assertEqual(len(lease_findings), 1)
        self.assertTrue(lease_findings[0].allowed)

    def test_auditor_classifies_closed_precontract_lease_as_legacy(self):
        old_acquired = T0 - timedelta(hours=1)
        old_session = session(started=T0 - timedelta(hours=2), status="COMPLETED")
        old_lease = lease(
            acquired=old_acquired,
            status="RELEASED",
            expires=old_acquired + timedelta(minutes=30),
        )
        findings = audit_control_plane(
            policy=policy(), sessions=[old_session], acks=[], leases=[old_lease],
            now=T0 + timedelta(minutes=4),
        )
        self.assertEqual(findings[0].codes, (GuardCode.LEGACY_PRE_CONTRACT,))


if __name__ == "__main__":
    unittest.main()
