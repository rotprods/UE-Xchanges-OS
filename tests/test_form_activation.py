from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.forms.activation import (
    build_human_login_evidence,
    form_execution_plan_from_mapping,
    human_login_evidence_from_mapping,
    human_login_evidence_to_mapping,
    inspect_identity_from_mapping,
    profile_dir_hash,
    runtime_doctor_envelope,
    runtime_doctor_envelope_from_mapping,
    runtime_doctor_from_mapping,
)
from uexchanges.forms.models import FormExecutionState


NOW = datetime(2026, 9, 1, 20, 15, tzinfo=timezone.utc)
FORM_FP = "sha256:" + "f" * 64
VALIDATION = "sha256:" + "1" * 64


class TargetMacActivationTests(unittest.TestCase):
    def test_doctor_mapping_and_envelope_are_strict(self):
        raw = {
            "status": "ok",
            "node_major": 22,
            "playwright_version": "1.62.1",
            "browser_channel": "chrome",
            "launch": "ok",
            "network": "blocked",
            "profile": "ephemeral",
        }
        doctor = runtime_doctor_from_mapping(raw)
        self.assertEqual(doctor.browser_channel, "chrome")
        envelope = runtime_doctor_envelope(doctor=doctor, doctor_passed_at=NOW)
        parsed, passed_at = runtime_doctor_envelope_from_mapping(envelope)
        self.assertEqual(parsed, doctor)
        self.assertEqual(passed_at, NOW)

        with self.assertRaisesRegex(ValueError, "unknown keys"):
            runtime_doctor_from_mapping({**raw, "secret": "should-never-be-accepted"})
        with self.assertRaisesRegex(ValueError, "node_major must be an integer"):
            runtime_doctor_from_mapping({**raw, "node_major": True})
        with self.assertRaisesRegex(ValueError, "network must be blocked"):
            runtime_doctor_from_mapping({**raw, "network": "open"})

    def test_human_login_evidence_is_opaque_and_profile_bound(self):
        evidence = build_human_login_evidence(
            profile_dir="/tmp/uex-dedicated-profile",
            browser_channel="chrome",
            allowed_origins=("https://example.org/path?private=1", "https://auth.example.org/login"),
            completed_at=NOW,
            nonce="fixed-nonce",
        )
        payload = human_login_evidence_to_mapping(evidence)
        serialized = str(payload)
        self.assertNotIn("/tmp/uex-dedicated-profile", serialized)
        self.assertNotIn("private=1", serialized)
        self.assertTrue(evidence.human_login_ref.startswith("human-login:"))
        self.assertEqual(evidence.profile_dir_hash, profile_dir_hash("/tmp/uex-dedicated-profile"))
        self.assertEqual(payload["allowed_origins"], ["https://example.org", "https://auth.example.org"])
        self.assertEqual(human_login_evidence_from_mapping(payload), evidence)

        tampered = dict(payload)
        tampered["extra"] = True
        with self.assertRaisesRegex(ValueError, "unknown keys"):
            human_login_evidence_from_mapping(tampered)

    def test_inspect_identity_accepts_only_value_free_safe_output(self):
        raw = {
            "mode": "INSPECT_ONLY",
            "identity_version": "0.1.0",
            "provider": "generic_html",
            "form_fingerprint": FORM_FP,
            "validation_signature": VALIDATION,
            "profile_mode": "dedicated_persistent",
            "browser_channel": "chrome",
            "page": {"url": "https://example.org/apply", "origin": "https://example.org"},
            "safety": {
                "form_values_read": False,
                "url_query_material_exported": False,
                "cookies_read": False,
                "storage_state_exported": False,
                "mutating_http_methods_blocked": True,
                "submit_events_blocked": True,
            },
            "fields": [{"field_key": "motivation", "answer": "NOT-USED-BY-ACTIVATION"}],
        }
        evidence = inspect_identity_from_mapping(raw)
        self.assertEqual(evidence.form_fingerprint, FORM_FP)
        self.assertEqual(evidence.validation_signature, VALIDATION)

        unsafe = {**raw, "safety": {**raw["safety"], "cookies_read": True}}
        with self.assertRaisesRegex(ValueError, "cookies_read"):
            inspect_identity_from_mapping(unsafe)
        bad_query_export = {**raw, "page": {"url": "https://example.org/apply?secret=x"}}
        with self.assertRaisesRegex(ValueError, "must not export query"):
            inspect_identity_from_mapping(bad_query_export)
        ambiguous_bool = {**raw, "safety": {**raw["safety"], "form_values_read": "false"}}
        with self.assertRaisesRegex(ValueError, "form_values_read"):
            inspect_identity_from_mapping(ambiguous_bool)

    def test_plan_loader_is_schema_strict_and_preserves_identity(self):
        payload = {
            "plan_id": "plan-1",
            "application_id": "app-1",
            "opportunity_id": "opp-1",
            "canonical_form_url": "https://example.org/apply",
            "provider": "generic_html",
            "form_fingerprint": FORM_FP,
            "validation_signature": VALIDATION,
            "fields": [
                {
                    "field_key": "email",
                    "label": "Email",
                    "field_type": "email",
                    "required": True,
                    "options": [],
                    "maxlength": None,
                    "answer": "candidate@example.org",
                    "answer_source": "profile:email",
                    "evidence_ids": ["ev-email"],
                    "ownership": "green_agent_factual",
                    "sensitivity": "private",
                    "editable_by_agent": True,
                }
            ],
            "ai_policy": "ai_assist_only",
            "auth_requirement": "existing_session",
            "submit_authority": "human_only",
            "allowed_origins": ["https://example.org"],
            "created_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(hours=1)).isoformat(),
            "source_version": "source-v1",
            "attachments": [],
            "state": "prefill_ready",
        }
        plan = form_execution_plan_from_mapping(payload)
        self.assertEqual(plan.form_fingerprint, FORM_FP)
        self.assertEqual(plan.validation_signature, VALIDATION)
        self.assertIs(plan.state, FormExecutionState.PREFILL_READY)

        with self.assertRaisesRegex(ValueError, "unknown keys"):
            form_execution_plan_from_mapping({**payload, "browser_submit": True})
        bad_field = dict(payload)
        bad_field["fields"] = [{**payload["fields"][0], "required": "true"}]
        with self.assertRaisesRegex(ValueError, "must be booleans"):
            form_execution_plan_from_mapping(bad_field)


if __name__ == "__main__":
    unittest.main()
