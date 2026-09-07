"""Adversarial tests for Writer Authorization Receipt content integrity."""
from __future__ import annotations

import importlib.util
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
)
from uexchanges.control_plane_health import SessionHealthRecord, evaluate_control_plane_health
from uexchanges.writer_authorization import WriterAuthorizationPolicy, authorize_writer
from uexchanges.writer_authorization_receipt import issue_writer_authorization_receipt
from uexchanges.writer_receipt_gate import (
    WriterPreparationDenied,
    prepare_writer_authorization,
    verify_prepared_acquisition,
)
from uexchanges.writer_receipt_integrity import (
    ReceiptIntegrityCode,
    ReceiptIntegrityError,
    expected_receipt_id,
    inspect_receipt_integrity,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "uex_receipt_auditor_integrity", ROOT / "scripts/audit_writer_authorization_receipts.py"
)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class WriterReceiptIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
        self.sha = "a" * 40
        self.session = SessionSnapshot(
            "SES-INTEGRITY", "AGT-INTEGRITY", "CTX-INTEGRITY",
            self.now - timedelta(seconds=20), "ACTIVE",
        )
        self.ack = BootstrapAckSnapshot(
            event_id="EVT-ACK",
            event_at=self.now - timedelta(seconds=10),
            manifest_version="1.1.0",
            observed_main_sha=self.sha,
            context_id="CTX-INTEGRITY",
            agent_id="AGT-INTEGRITY",
            session_id="SES-INTEGRITY",
            private_event_watermark="EVT-INPUT",
            lease_scan_at=self.now - timedelta(seconds=11),
            public_read_refs=("goal.md@" + self.sha,),
        )
        self.prelease = PreLeaseRefresh(
            observed_main_sha=self.sha,
            lease_scan_at=self.now,
            private_event_watermark="EVT-ACK",
        )
        self.lease = LeaseSnapshot(
            lease_id="LSE-INTEGRITY",
            owner_session_id="SES-INTEGRITY",
            owner_agent_id="AGT-INTEGRITY",
            context_id="CTX-INTEGRITY",
            scope="github:synthetic-integrity-only",
            acquired_at=self.now,
            expires_at=self.now + timedelta(minutes=10),
            status="ACTIVE",
        )
        self.policy = WriterAuthorizationPolicy(
            BootstrapPolicy(
                manifest_version="1.1.0",
                current_main_sha=self.sha,
                context_id="CTX-INTEGRITY",
                effective_at=self.now - timedelta(days=1),
            )
        )
        self.health = evaluate_control_plane_health(
            now=self.now,
            sessions=[
                SessionHealthRecord(
                    "SES-INTEGRITY", "AGT-INTEGRITY", "CTX-INTEGRITY",
                    self.session.started_at, self.now, "ACTIVE",
                )
            ],
            leases=[],
            bootstrap_noncompliant_count=0,
        )
        self.decision = authorize_writer(
            policy=self.policy,
            session=self.session,
            ack=self.ack,
            proposed_lease=self.lease,
            prelease=self.prelease,
            health=self.health,
            now=self.now,
            overlapping_unexpired_lease_ids=(),
        )
        self.receipt = issue_writer_authorization_receipt(
            decision=self.decision,
            session=self.session,
            proposed_lease=self.lease,
            prelease=self.prelease,
            health=self.health,
            manifest_version="1.1.0",
            observed_main_sha=self.sha,
            issued_at=self.now,
        )

    def test_issuer_receipt_id_matches_recomputed_content_address(self):
        self.assertEqual(self.receipt.receipt_id, expected_receipt_id(self.receipt))
        self.assertTrue(inspect_receipt_integrity(self.receipt, decision=self.decision).allowed)

    def test_shape_valid_receipt_id_tampering_is_rejected(self):
        tampered = replace(self.receipt, receipt_id="WAZ-" + "0" * 24)
        result = inspect_receipt_integrity(tampered, decision=self.decision)
        self.assertFalse(result.allowed)
        self.assertIn(ReceiptIntegrityCode.RECEIPT_ID_MISMATCH, result.codes)

    def test_authorization_time_tampering_is_rejected_even_with_recomputed_id(self):
        altered = replace(
            self.receipt,
            authorization_evaluated_at=self.receipt.authorization_evaluated_at + timedelta(seconds=1),
        )
        altered = replace(altered, receipt_id=expected_receipt_id(altered))
        result = inspect_receipt_integrity(altered, decision=self.decision)
        self.assertFalse(result.allowed)
        self.assertNotIn(ReceiptIntegrityCode.RECEIPT_ID_MISMATCH, result.codes)
        self.assertIn(ReceiptIntegrityCode.AUTHORIZATION_EVALUATED_AT_MISMATCH, result.codes)

    def test_offline_auditor_rejects_tampered_content_address_before_binding_audit(self):
        raw = self.receipt.as_dict()
        raw["receipt_id"] = "WAZ-" + "0" * 24
        with self.assertRaises(ReceiptIntegrityError) as caught:
            AUDITOR.receipt_from_dict(raw)
        self.assertIn(ReceiptIntegrityCode.RECEIPT_ID_MISMATCH, caught.exception.codes)

    def test_gate_acquisition_can_recheck_later_without_rebinding_original_timestamp(self):
        prepared = prepare_writer_authorization(
            policy=self.policy,
            session=self.session,
            ack=self.ack,
            proposed_lease=self.lease,
            prelease=self.prelease,
            health=self.health,
            now=self.now,
            overlapping_unexpired_lease_ids=(),
        )
        result = verify_prepared_acquisition(
            prepared=prepared,
            policy=self.policy,
            session=self.session,
            ack=self.ack,
            lease=self.lease,
            prelease=self.prelease,
            health=self.health,
            now=self.now + timedelta(seconds=1),
            overlapping_unexpired_lease_ids=(),
        )
        self.assertTrue(result.allowed)

    def test_gate_rejects_evaluation_time_tampering_with_self_consistent_receipt_id(self):
        prepared = prepare_writer_authorization(
            policy=self.policy,
            session=self.session,
            ack=self.ack,
            proposed_lease=self.lease,
            prelease=self.prelease,
            health=self.health,
            now=self.now,
            overlapping_unexpired_lease_ids=(),
        )
        altered = replace(
            prepared.receipt,
            authorization_evaluated_at=prepared.receipt.authorization_evaluated_at + timedelta(seconds=1),
        )
        altered = replace(altered, receipt_id=expected_receipt_id(altered))
        corrupted = replace(prepared, receipt=altered)
        with self.assertRaises(WriterPreparationDenied) as caught:
            verify_prepared_acquisition(
                prepared=corrupted,
                policy=self.policy,
                session=self.session,
                ack=self.ack,
                lease=self.lease,
                prelease=self.prelease,
                health=self.health,
                now=self.now + timedelta(seconds=1),
                overlapping_unexpired_lease_ids=(),
            )
        self.assertIn("AUTHORIZATION_EVALUATED_AT_MISMATCH", caught.exception.codes)


if __name__ == "__main__":
    unittest.main()
