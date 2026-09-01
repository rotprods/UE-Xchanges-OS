from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.forms import (
    AttestationStatus,
    AuthenticatedInspectClaims,
    RuntimeAttestationClaims,
    RuntimeDoctorEvidence,
    issue_authenticated_inspect_evidence,
    issue_runtime_attestation,
    runtime_doctor_evidence_hash,
    verify_authenticated_inspect_evidence,
    verify_runtime_attestation,
)


NOW = datetime(2026, 9, 1, 18, 45, tzinfo=timezone.utc)
RUNTIME_SECRET = b"r" * 32
INSPECT_SECRET = b"i" * 32
FORM_FP = "sha256:" + "f" * 64
VALIDATION = "sha256:" + "1" * 64


def doctor(**overrides) -> RuntimeDoctorEvidence:
    base = dict(
        status="ok",
        node_major=22,
        playwright_version="1.62.1",
        browser_channel="chrome",
        launch="ok",
        network="blocked",
        profile="ephemeral",
    )
    base.update(overrides)
    return RuntimeDoctorEvidence(**base)


def runtime_token(**overrides) -> str:
    args = dict(
        runtime_ref="runtime:uex-primary",
        executor_version="0.4.0",
        doctor_evidence=doctor(),
        profile_mode="dedicated_persistent",
        doctor_passed_at=NOW - timedelta(minutes=1),
        issued_at=NOW,
        secret=RUNTIME_SECRET,
        ttl_seconds=3600,
        nonce="runtime-test-nonce",
    )
    args.update(overrides)
    return issue_runtime_attestation(**args)


class RuntimeAttestationTests(unittest.TestCase):
    def test_valid_runtime_attestation_is_derived_from_safe_doctor_evidence(self):
        evidence = doctor()
        token = runtime_token(doctor_evidence=evidence)
        result = verify_runtime_attestation(token=token, secret=RUNTIME_SECRET, now=NOW + timedelta(seconds=1))
        self.assertTrue(result.valid)
        self.assertIs(result.status, AttestationStatus.VALID)
        self.assertIsInstance(result.claims, RuntimeAttestationClaims)
        self.assertEqual(result.claims.executor_version, "0.4.0")
        self.assertEqual(result.claims.playwright_version, "1.62.1")
        self.assertEqual(result.claims.browser_channel, "chrome")
        self.assertEqual(result.claims.profile_mode, "dedicated_persistent")
        self.assertEqual(result.claims.doctor_evidence_hash, runtime_doctor_evidence_hash(evidence))

    def test_doctor_evidence_is_deterministic_and_strict(self):
        self.assertEqual(runtime_doctor_evidence_hash(doctor()), runtime_doctor_evidence_hash(doctor()))
        for overrides, pattern in [
            ({"status": "fail"}, "status must be ok"),
            ({"node_major": 19}, "Node major"),
            ({"browser_channel": "firefox"}, "browser_channel"),
            ({"launch": "failed"}, "launch must be ok"),
            ({"network": "open"}, "network must be blocked"),
            ({"profile": "persistent"}, "profile must be ephemeral"),
        ]:
            with self.assertRaisesRegex(ValueError, pattern):
                doctor(**overrides)

    def test_runtime_attestation_tamper_wrong_secret_and_expiry_fail_closed(self):
        token = runtime_token(ttl_seconds=5)
        payload = token.split(".")
        payload[-1] = ("0" if payload[-1][0] != "0" else "1") + payload[-1][1:]
        tampered = verify_runtime_attestation(token=".".join(payload), secret=RUNTIME_SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(tampered.status, AttestationStatus.INVALID_SIGNATURE)
        wrong_secret = verify_runtime_attestation(token=token, secret=b"x" * 32, now=NOW + timedelta(seconds=1))
        self.assertIs(wrong_secret.status, AttestationStatus.INVALID_SIGNATURE)
        expired = verify_runtime_attestation(token=token, secret=RUNTIME_SECRET, now=NOW + timedelta(seconds=5))
        self.assertIs(expired.status, AttestationStatus.EXPIRED)

    def test_runtime_attestation_rejects_unsafe_runtime_claims(self):
        with self.assertRaisesRegex(ValueError, "dedicated_persistent"):
            runtime_token(profile_mode="personal_chrome")
        with self.assertRaisesRegex(ValueError, "cannot be after"):
            runtime_token(doctor_passed_at=NOW + timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "at least 32"):
            runtime_token(secret=b"short")

    def test_authenticated_inspect_is_bound_to_valid_runtime_and_has_no_values(self):
        rt = runtime_token()
        token = issue_authenticated_inspect_evidence(
            runtime_token=rt,
            runtime_secret=RUNTIME_SECRET,
            evidence_secret=INSPECT_SECRET,
            provider_id="example_provider",
            canonical_form_url="https://forms.example.org/apply#private",
            form_fingerprint=FORM_FP,
            validation_signature=VALIDATION,
            authenticated=True,
            human_login_ref="human-login:done-1",
            inspected_at=NOW + timedelta(seconds=1),
            now=NOW + timedelta(seconds=1),
            ttl_seconds=600,
            nonce="inspect-test-nonce",
        )
        result = verify_authenticated_inspect_evidence(token=token, secret=INSPECT_SECRET, now=NOW + timedelta(seconds=2))
        self.assertTrue(result.valid)
        self.assertIsInstance(result.claims, AuthenticatedInspectClaims)
        self.assertTrue(result.claims.authenticated)
        self.assertFalse(result.claims.form_values_read)
        self.assertFalse(result.claims.cookies_read)
        self.assertFalse(result.claims.storage_state_exported)
        self.assertEqual(result.claims.canonical_form_url, "https://forms.example.org/apply")

    def test_authenticated_inspect_requires_human_login_ref_and_live_runtime(self):
        rt = runtime_token(ttl_seconds=5)
        with self.assertRaisesRegex(ValueError, "human_login_ref"):
            issue_authenticated_inspect_evidence(
                runtime_token=rt,
                runtime_secret=RUNTIME_SECRET,
                evidence_secret=INSPECT_SECRET,
                provider_id="provider",
                canonical_form_url="https://forms.example.org/apply",
                form_fingerprint=FORM_FP,
                validation_signature=VALIDATION,
                authenticated=True,
                human_login_ref=None,
                inspected_at=NOW,
                now=NOW,
            )
        with self.assertRaisesRegex(ValueError, "valid runtime"):
            issue_authenticated_inspect_evidence(
                runtime_token=rt,
                runtime_secret=RUNTIME_SECRET,
                evidence_secret=INSPECT_SECRET,
                provider_id="provider",
                canonical_form_url="https://forms.example.org/apply",
                form_fingerprint=FORM_FP,
                validation_signature=VALIDATION,
                authenticated=False,
                human_login_ref=None,
                inspected_at=NOW + timedelta(seconds=6),
                now=NOW + timedelta(seconds=6),
            )

    def test_token_domains_cannot_be_confused(self):
        rt = runtime_token()
        result = verify_authenticated_inspect_evidence(token=rt, secret=RUNTIME_SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(result.status, AttestationStatus.MALFORMED)


if __name__ == "__main__":
    unittest.main()
