"""Synthetic integration tests using the real guard, broker, issuer and auditor.

No monkey-patched constructors, credentials, live CRM values or network calls.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot, BootstrapPolicy, LeaseSnapshot,
    PreLeaseRefresh, SessionSnapshot,
)
from uexchanges.control_plane_health import (
    SessionHealthRecord, evaluate_control_plane_health,
)
from uexchanges.writer_authorization import (
    AuthorizationCode, WriteIntent, WriterAuthorizationPolicy, authorize_writer,
)
from uexchanges.writer_authorization_receipt import (
    ReceiptVerificationCode, issue_writer_authorization_receipt,
    verify_writer_authorization_receipt,
)
from uexchanges.writer_receipt_integrity import expected_receipt_id
from uexchanges.writer_receipt_payload import ReceiptPayloadError, require_valid_receipt_payload

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "uex_receipt_auditor_integration", ROOT / "scripts/audit_writer_authorization_receipts.py"
)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class RealReceiptIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
        self.sha = "a" * 40
        self.session = SessionSnapshot("SES-TEST", "AGT-TEST", "CTX-TEST", self.now-timedelta(seconds=20))
        self.ack = BootstrapAckSnapshot(
            "EVT-ACK", self.now-timedelta(seconds=10), "1.1.0", self.sha,
            "CTX-TEST", "AGT-TEST", "SES-TEST", "EVT-INPUT",
            self.now-timedelta(seconds=11), public_read_refs=("goal.md@"+self.sha,),
        )
        self.prelease = PreLeaseRefresh(self.sha, self.now, "EVT-ACK")
        self.lease = LeaseSnapshot(
            "LSE-TEST", "SES-TEST", "AGT-TEST", "CTX-TEST", "github:synthetic-code-only",
            self.now, self.now+timedelta(minutes=10),
        )
        self.policy = WriterAuthorizationPolicy(BootstrapPolicy(
            "1.1.0", self.sha, "CTX-TEST", self.now-timedelta(days=1),
        ))
        self.health = evaluate_control_plane_health(
            now=self.now,
            sessions=[SessionHealthRecord("SES-TEST", "AGT-TEST", "CTX-TEST",
                       self.session.started_at, self.now, "ACTIVE")],
            leases=[], bootstrap_noncompliant_count=0,
        )
        self.decision = self.decide()
        self.receipt = issue_writer_authorization_receipt(
            decision=self.decision, session=self.session, proposed_lease=self.lease,
            prelease=self.prelease, health=self.health, manifest_version="1.1.0",
            observed_main_sha=self.sha, issued_at=self.now,
        )

    def decide(self, **changes):
        values = dict(policy=self.policy, session=self.session, ack=self.ack,
                      proposed_lease=self.lease, prelease=self.prelease,
                      health=self.health, now=self.now)
        values.update(changes)
        return authorize_writer(**values)

    def verify(self, **changes):
        values = dict(receipt=self.receipt, decision=self.decision, session=self.session,
                      lease=self.lease, prelease=self.prelease, health=self.health,
                      manifest_version="1.1.0", observed_main_sha=self.sha)
        values.update(changes)
        return verify_writer_authorization_receipt(**values)

    def snapshot(self):
        lease = {k:v.isoformat() if isinstance(v,datetime) else v for k,v in asdict(self.lease).items()}
        return dict(effective_at=(self.now-timedelta(days=1)).isoformat(),
                    leases=[lease], receipts=[self.receipt.as_dict()])

    def cli(self, payload):
        text=payload if isinstance(payload,str) else json.dumps(payload)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"synthetic.json"; path.write_text(text)
            env=dict(os.environ, PYTHONPATH=str(ROOT/"src"))
            return subprocess.run([sys.executable, str(ROOT/"scripts/audit_writer_authorization_receipts.py"),
                                   str(path), "--fail-on-findings"], env=env, cwd=ROOT,
                                  capture_output=True, text=True, timeout=10, check=False)

    def test_real_broker_issuer_shape_deserializer_verifier_roundtrip(self):
        self.assertTrue(self.decision.coordination_allowed)
        payload=self.receipt.event_payload()
        require_valid_receipt_payload(payload)
        reconstructed=AUDITOR.receipt_from_dict(payload)
        self.assertEqual(reconstructed, self.receipt)
        self.assertTrue(self.verify(receipt=reconstructed).allowed)

    def test_real_deserializer_accepts_schema_valid_lowercase_utc_suffix(self):
        raw = self.receipt.as_dict()
        raw["issued_at"] = raw["issued_at"].replace("+00:00", "z")
        require_valid_receipt_payload(raw)
        self.assertEqual(AUDITOR.receipt_from_dict(raw), self.receipt)

    def test_real_constructor_no_longer_accepts_coerced_identity(self):
        raw=self.receipt.as_dict(); raw["session_id"]=None
        with self.assertRaises(ReceiptPayloadError): AUDITOR.receipt_from_dict(raw)

    def test_real_deserializer_rejects_metadata_inside_receipt(self):
        raw=self.receipt.as_dict(); raw["decision"]="ALLOWED"
        with self.assertRaises(ReceiptPayloadError): AUDITOR.receipt_from_dict(raw)

    def test_real_deserializer_rejects_missing_required_null(self):
        raw=self.receipt.as_dict(); del raw["repair_plan_id"]
        with self.assertRaises(ReceiptPayloadError): AUDITOR.receipt_from_dict(raw)

    def test_real_deserializer_rejects_missing_overlap_inventory(self):
        raw=self.receipt.as_dict(); del raw["overlapping_lease_ids"]
        with self.assertRaises(ReceiptPayloadError): AUDITOR.receipt_from_dict(raw)

    def test_real_deserializer_rejects_noncanonical_boolean(self):
        raw=self.receipt.as_dict(); raw["domain_authority"]=0
        with self.assertRaises(ReceiptPayloadError): AUDITOR.receipt_from_dict(raw)

    def test_real_guard_denies_read_only_session_without_coercion(self):
        result=self.decide(session=replace(self.session,status="ACTIVE_READ_ONLY"))
        self.assertFalse(result.coordination_allowed)
        self.assertIn(AuthorizationCode.BOOTSTRAP_DENIED,result.codes)

    def test_real_guard_denies_missing_ack(self):
        self.assertFalse(self.decide(ack=None).coordination_allowed)

    def test_real_broker_denies_explicit_overlap(self):
        result=self.decide(overlapping_unexpired_lease_ids=("LSE-OTHER",))
        self.assertIn(AuthorizationCode.OVERLAPPING_LEASE,result.codes)
        self.assertFalse(result.coordination_allowed)

    def test_real_broker_denies_stale_health(self):
        result=self.decide(health=replace(self.health,generated_at=self.now-timedelta(seconds=121)))
        self.assertIn(AuthorizationCode.HEALTH_REPORT_STALE,result.codes)

    def test_real_broker_denies_failed_bootstrap_slo(self):
        health=evaluate_control_plane_health(now=self.now,sessions=[],leases=[],bootstrap_noncompliant_count=1)
        self.assertFalse(self.decide(health=health).coordination_allowed)

    def test_real_broker_never_grants_external_side_effects(self):
        result=self.decide(intent=WriteIntent.EXTERNAL_SIDE_EFFECT)
        self.assertFalse(result.coordination_allowed)
        with self.assertRaises(ValueError):
            issue_writer_authorization_receipt(decision=result,session=self.session,proposed_lease=self.lease,
                prelease=self.prelease,health=self.health,manifest_version="1.1.0",observed_main_sha=self.sha,issued_at=self.now)

    def test_shape_valid_tampering_still_fails_full_verifier(self):
        altered = replace(self.receipt, scope_sha256="b"*64)
        altered = replace(altered, receipt_id=expected_receipt_id(altered))
        result=self.verify(receipt=altered)
        self.assertIn(ReceiptVerificationCode.SCOPE_MISMATCH,result.codes)

    def test_full_verifier_denies_changed_decision_digest(self):
        altered = replace(self.receipt, authorization_decision_digest="b"*64)
        altered = replace(altered, receipt_id=expected_receipt_id(altered))
        result=self.verify(receipt=altered)
        self.assertIn(ReceiptVerificationCode.AUTHORIZATION_DIGEST_MISMATCH,result.codes)

    def test_full_verifier_denies_other_lease(self):
        result=self.verify(lease=replace(self.lease,lease_id="LSE-OTHER"))
        self.assertIn(ReceiptVerificationCode.LEASE_ID_MISMATCH,result.codes)

    def test_full_verifier_denies_late_acquisition(self):
        result=self.verify(lease=replace(self.lease,acquired_at=self.now+timedelta(seconds=121)))
        self.assertIn(ReceiptVerificationCode.RECEIPT_EXPIRED_BEFORE_LEASE_ACQUIRE,result.codes)

    def test_full_verifier_denies_changed_watermark(self):
        result=self.verify(prelease=replace(self.prelease,private_event_watermark="EVT-OTHER"))
        self.assertFalse(result.allowed)

    def test_cli_real_historical_audit_passes(self):
        result=self.cli(self.snapshot())
        self.assertEqual(result.returncode,0,result.stderr)
        output=json.loads(result.stdout)
        self.assertEqual(output["finding_count"],0)
        self.assertEqual(output["lease_count"],1)

    def test_cli_real_audit_detects_missing_receipt(self):
        raw=self.snapshot();raw["receipts"]=[]
        result=self.cli(raw)
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertEqual(json.loads(result.stdout)["finding_count"],1)

    def test_cli_rejects_duplicate_json_keys_not_last_value_wins(self):
        text=json.dumps(self.snapshot()).replace('"coordination_allowed": true',
                '"coordination_allowed": false, "coordination_allowed": true')
        result=self.cli(text)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("DUPLICATE_JSON_KEY",result.stderr)

    def test_cli_rejects_malformed_receipt_before_binding_audit(self):
        raw=self.snapshot();raw["receipts"][0]["session_id"]=12
        result=self.cli(raw)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("NONEMPTY_STRING_REQUIRED",result.stderr)

    def test_cli_precontract_lease_is_not_retroactively_condemned(self):
        raw=self.snapshot();raw["effective_at"]=(self.now+timedelta(days=1)).isoformat();raw["receipts"]=[]
        result=self.cli(raw)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["lease_count"],0)

    def test_serialization_is_deterministic_and_does_not_mutate_input(self):
        before=copy.deepcopy(self.receipt.as_dict())
        self.assertEqual(AUDITOR.receipt_from_dict(before).as_dict(),self.receipt.as_dict())
        self.assertEqual(before,self.receipt.as_dict())
