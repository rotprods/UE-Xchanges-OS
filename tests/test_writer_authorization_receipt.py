import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
)
from uexchanges.control_plane_health import (
    ControlPlaneHealthReport,
    OverallHealth,
    SloResult,
)
from uexchanges.writer_authorization import (
    WriterAuthorizationPolicy,
    WriteIntent,
    authorize_writer,
)
from uexchanges.writer_authorization_receipt import (
    ReceiptVerificationCode,
    audit_lease_receipt_bindings,
    canonical_scope_sha256,
    issue_writer_authorization_receipt,
    verify_writer_authorization_receipt,
)

BASE = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
MAIN = "a" * 40
CONTEXT = "CTX-UEX-GLOBAL-EXPANSION-INCOME-V1"
SESSION = "SES-TEST-RECEIPT-01"
AGENT = "AGT-TEST-WRITER"
LEASE = "LSE-TEST-RECEIPT-01"
SCOPE = "github:src/uexchanges/example.py+tests/test_example.py"


def session():
    return SessionSnapshot(SESSION, AGENT, CONTEXT, BASE, "ACTIVE")


def ack():
    return BootstrapAckSnapshot(
        event_id="EVT-ACK-1",
        event_at=BASE + timedelta(seconds=10),
        manifest_version="1.0.0",
        observed_main_sha=MAIN,
        context_id=CONTEXT,
        agent_id=AGENT,
        session_id=SESSION,
        private_event_watermark="EVT-WATERMARK-1",
        lease_scan_at=BASE + timedelta(seconds=9),
        public_read_refs=("goal.md", "AGENTS.md", "MEMORY.md"),
    )


def prelease():
    return PreLeaseRefresh(
        observed_main_sha=MAIN,
        lease_scan_at=BASE + timedelta(seconds=20),
        private_event_watermark="EVT-WATERMARK-2",
    )


def lease(*, scope=SCOPE, acquired_at=None):
    acquired_at = acquired_at or BASE + timedelta(seconds=30)
    return LeaseSnapshot(
        lease_id=LEASE,
        owner_session_id=SESSION,
        owner_agent_id=AGENT,
        context_id=CONTEXT,
        scope=scope,
        acquired_at=acquired_at,
        expires_at=acquired_at + timedelta(minutes=30),
        status="ACTIVE",
    )


def health(*, generated_at=None, metrics=None):
    generated_at = generated_at or BASE + timedelta(seconds=19)
    return ControlPlaneHealthReport(
        generated_at=generated_at,
        overall=OverallHealth.GREEN,
        findings=(),
        metrics=metrics or {"active_sessions": 1},
        slos=(
            SloResult("bootstrap_compliance", True, 0, "0 violations"),
            SloResult("session_identity_uniqueness", True, 0, "0 duplicates"),
            SloResult("lease_fencing_integrity", True, 0, "0 conflicts"),
            SloResult("context_freshness", True, 0, "fresh"),
        ),
    )


def decision(*, intent=WriteIntent.VERSIONED_CODE, overlaps=()):
    return authorize_writer(
        policy=WriterAuthorizationPolicy(
            bootstrap=BootstrapPolicy(
                manifest_version="1.0.0",
                current_main_sha=MAIN,
                context_id=CONTEXT,
                effective_at=BASE - timedelta(hours=1),
            ),
            max_health_report_age_seconds=120,
        ),
        session=session(),
        ack=ack(),
        proposed_lease=lease(),
        prelease=prelease(),
        health=health(),
        now=BASE + timedelta(seconds=20),
        overlapping_unexpired_lease_ids=overlaps,
        intent=intent,
    )


def receipt():
    return issue_writer_authorization_receipt(
        decision=decision(),
        session=session(),
        proposed_lease=lease(),
        prelease=prelease(),
        health=health(),
        manifest_version="1.0.0",
        observed_main_sha=MAIN,
        issued_at=BASE + timedelta(seconds=21),
        ttl_seconds=60,
    )


class WriterAuthorizationReceiptTests(unittest.TestCase):
    def test_happy_path_binds_exact_acquisition_and_never_grants_domain_or_external(self):
        item = receipt()
        result = verify_writer_authorization_receipt(
            receipt=item,
            decision=decision(),
            session=session(),
            lease=lease(),
            prelease=prelease(),
            health=health(),
            manifest_version="1.0.0",
            observed_main_sha=MAIN,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.codes, (ReceiptVerificationCode.VALID,))
        self.assertTrue(item.coordination_allowed)
        self.assertFalse(item.domain_authority)
        self.assertFalse(item.external_capability)
        self.assertFalse(item.as_dict()["domain_authority"])
        self.assertFalse(item.as_dict()["external_capability"])

    def test_receipt_id_is_deterministic_for_identical_claims(self):
        self.assertEqual(receipt().receipt_id, receipt().receipt_id)

    def test_scope_change_invalidates_receipt(self):
        result = verify_writer_authorization_receipt(
            receipt=receipt(),
            decision=decision(),
            session=session(),
            lease=lease(scope="github:different/path.py"),
            prelease=prelease(),
            health=health(),
            manifest_version="1.0.0",
            observed_main_sha=MAIN,
        )
        self.assertFalse(result.allowed)
        self.assertIn(ReceiptVerificationCode.SCOPE_MISMATCH, result.codes)

    def test_decision_digest_change_invalidates_receipt(self):
        altered = replace(decision(), decision_digest="0" * 64)
        result = verify_writer_authorization_receipt(
            receipt=receipt(),
            decision=altered,
            session=session(),
            lease=lease(),
            prelease=prelease(),
            health=health(),
            manifest_version="1.0.0",
            observed_main_sha=MAIN,
        )
        self.assertFalse(result.allowed)
        self.assertIn(ReceiptVerificationCode.AUTHORIZATION_DIGEST_MISMATCH, result.codes)

    def test_main_change_invalidates_receipt(self):
        result = verify_writer_authorization_receipt(
            receipt=receipt(),
            decision=decision(),
            session=session(),
            lease=lease(),
            prelease=prelease(),
            health=health(),
            manifest_version="1.0.0",
            observed_main_sha="b" * 40,
        )
        self.assertFalse(result.allowed)
        self.assertIn(ReceiptVerificationCode.MAIN_SHA_MISMATCH, result.codes)

    def test_health_snapshot_change_invalidates_receipt(self):
        changed = health(metrics={"active_sessions": 2})
        result = verify_writer_authorization_receipt(
            receipt=receipt(),
            decision=decision(),
            session=session(),
            lease=lease(),
            prelease=prelease(),
            health=changed,
            manifest_version="1.0.0",
            observed_main_sha=MAIN,
        )
        self.assertFalse(result.allowed)
        self.assertIn(ReceiptVerificationCode.HEALTH_REPORT_MISMATCH, result.codes)

    def test_issue_rejects_denied_decision(self):
        denied = decision(overlaps=("LSE-BLOCKER",))
        self.assertFalse(denied.coordination_allowed)
        with self.assertRaisesRegex(ValueError, "denied writer authorization"):
            issue_writer_authorization_receipt(
                decision=denied,
                session=session(),
                proposed_lease=lease(),
                prelease=prelease(),
                health=health(),
                manifest_version="1.0.0",
                observed_main_sha=MAIN,
                issued_at=BASE + timedelta(seconds=21),
            )

    def test_issue_rejects_ttl_that_does_not_cover_acquisition(self):
        with self.assertRaisesRegex(ValueError, "TTL does not cover"):
            issue_writer_authorization_receipt(
                decision=decision(),
                session=session(),
                proposed_lease=lease(),
                prelease=prelease(),
                health=health(),
                manifest_version="1.0.0",
                observed_main_sha=MAIN,
                issued_at=BASE + timedelta(seconds=21),
                ttl_seconds=5,
            )

    def test_historical_verification_rejects_lease_acquired_after_receipt_expiry(self):
        item = receipt()
        late = lease(acquired_at=item.expires_at + timedelta(seconds=1))
        result = verify_writer_authorization_receipt(
            receipt=item,
            decision=decision(),
            session=session(),
            lease=late,
            prelease=prelease(),
            health=health(),
            manifest_version="1.0.0",
            observed_main_sha=MAIN,
        )
        self.assertFalse(result.allowed)
        self.assertIn(ReceiptVerificationCode.RECEIPT_EXPIRED_BEFORE_LEASE_ACQUIRE, result.codes)

    def test_structural_audit_flags_missing_receipt_only_after_effective_date(self):
        current = lease()
        legacy = replace(
            current,
            lease_id="LSE-LEGACY",
            acquired_at=BASE - timedelta(hours=2),
            expires_at=BASE - timedelta(hours=1),
        )
        findings = audit_lease_receipt_bindings(
            leases=(legacy, current),
            receipts=(),
            effective_at=BASE - timedelta(minutes=1),
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].lease_id, LEASE)
        self.assertEqual(
            findings[0].codes,
            (ReceiptVerificationCode.MISSING_AUTHORIZATION_RECEIPT,),
        )

    def test_structural_audit_flags_duplicate_receipts(self):
        findings = audit_lease_receipt_bindings(
            leases=(lease(),),
            receipts=(receipt(), receipt()),
            effective_at=BASE,
        )
        self.assertEqual(
            findings[0].codes,
            (ReceiptVerificationCode.DUPLICATE_AUTHORIZATION_RECEIPT,),
        )

    def test_structural_audit_accepts_one_matching_receipt(self):
        findings = audit_lease_receipt_bindings(
            leases=(lease(),),
            receipts=(receipt(),),
            effective_at=BASE,
        )
        self.assertTrue(findings[0].allowed)
        self.assertEqual(findings[0].codes, (ReceiptVerificationCode.VALID,))

    def test_scope_hash_is_exact_not_whitespace_normalized(self):
        self.assertNotEqual(canonical_scope_sha256("scope:a"), canonical_scope_sha256("scope:a "))

    def test_json_schema_keeps_receipt_coordination_only(self):
        schema = json.loads(Path("schemas/writer-authorization-receipt.schema.json").read_text())
        props = schema["properties"]
        self.assertEqual(props["coordination_allowed"], {"const": True})
        self.assertEqual(props["domain_authority"], {"const": False})
        self.assertEqual(props["external_capability"], {"const": False})
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
