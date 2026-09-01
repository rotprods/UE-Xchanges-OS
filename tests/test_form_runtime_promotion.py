from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from uexchanges.forms import (
    AuthRequirement,
    FieldOwnership,
    FieldSensitivity,
    FormExecutionPlan,
    FormExecutionState,
    FormField,
    FormFieldType,
    ProviderCapabilityManifest,
    RuntimeDoctorEvidence,
    SubmitAuthority,
    evaluate_prefill_promotion,
    issue_authenticated_inspect_evidence,
    issue_runtime_attestation,
)
from uexchanges.forms.provider_capability import provider_manifest_from_mapping
from uexchanges.models import AIPolicy


NOW = datetime(2026, 9, 1, 18, 50, tzinfo=timezone.utc)
RUNTIME_SECRET = b"r" * 32
INSPECT_SECRET = b"i" * 32
FORM_FP = "sha256:" + "f" * 64
VALIDATION_V1 = "sha256:" + "1" * 64
VALIDATION_V2 = "sha256:" + "2" * 64
ROOT = Path(__file__).resolve().parents[1]


def make_plan(**overrides) -> FormExecutionPlan:
    field = FormField(
        field_key="email",
        label="Email",
        field_type=FormFieldType.EMAIL,
        required=True,
        answer="candidate@example.com",
        answer_source="profile:email",
        evidence_ids=("ev-email",),
        ownership=FieldOwnership.GREEN,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=True,
    )
    base = dict(
        plan_id="plan-runtime-1",
        application_id="app-runtime-1",
        opportunity_id="opp-runtime-1",
        canonical_form_url="http://127.0.0.1:39000/form?call=fixture",
        provider="generic_html",
        form_fingerprint=FORM_FP,
        validation_signature=VALIDATION_V1,
        fields=(field,),
        ai_policy=AIPolicy.ASSIST_ONLY,
        auth_requirement=AuthRequirement.NONE,
        submit_authority=SubmitAuthority.HUMAN_ONLY,
        allowed_origins=("http://127.0.0.1:39000",),
        created_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
        source_version="runtime-fixture-v1",
        state=FormExecutionState.PREFILL_READY,
    )
    base.update(overrides)
    return FormExecutionPlan(**base)


def make_runtime(*, executor_version="0.4.0", browser_channel="chromium", ttl_seconds=3600, issued_at=None) -> str:
    issued = issued_at or (NOW - timedelta(minutes=1))
    doctor = RuntimeDoctorEvidence(
        status="ok",
        node_major=22,
        playwright_version="1.62.1",
        browser_channel=browser_channel,
        launch="ok",
        network="blocked",
        profile="ephemeral",
    )
    return issue_runtime_attestation(
        runtime_ref="runtime:uex-test",
        executor_version=executor_version,
        doctor_evidence=doctor,
        doctor_passed_at=issued - timedelta(minutes=1),
        issued_at=issued,
        secret=RUNTIME_SECRET,
        ttl_seconds=ttl_seconds,
        nonce=f"runtime-{executor_version}-{browser_channel}-{ttl_seconds}-{issued.isoformat()}",
    )


def make_inspect(runtime: str, plan: FormExecutionPlan, *, authenticated=False, human_login_ref=None, ttl_seconds=600) -> str:
    return issue_authenticated_inspect_evidence(
        runtime_token=runtime,
        runtime_secret=RUNTIME_SECRET,
        evidence_secret=INSPECT_SECRET,
        provider_id=plan.provider,
        canonical_form_url=plan.canonical_form_url,
        form_fingerprint=plan.form_fingerprint,
        validation_signature=plan.validation_signature,
        authenticated=authenticated,
        human_login_ref=human_login_ref,
        inspected_at=NOW,
        now=NOW,
        ttl_seconds=ttl_seconds,
        nonce=f"inspect-{authenticated}-{ttl_seconds}",
    )


def local_manifest() -> ProviderCapabilityManifest:
    raw = json.loads((ROOT / "config" / "form-providers" / "generic-html-local-fixture.json").read_text())
    return provider_manifest_from_mapping(raw)


class RuntimePrefillPromotionTests(unittest.TestCase):
    def test_local_fixture_can_pass_pure_prefill_gate_without_granting_submit(self):
        plan = make_plan()
        runtime = make_runtime()
        inspect = make_inspect(runtime, plan)
        manifest = local_manifest()
        decision = evaluate_prefill_promotion(
            plan=plan,
            runtime_token=runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=manifest,
            now=NOW + timedelta(seconds=1),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reasons, ())
        self.assertTrue(decision.capability_binding_hash.startswith("sha256:"))
        self.assertFalse(manifest.submit_certified)
        self.assertTrue(manifest.local_fixture_only)

    def test_validation_or_form_identity_drift_denies_prefill(self):
        plan = make_plan()
        runtime = make_runtime()
        inspect = make_inspect(runtime, plan)
        validation_changed = make_plan(validation_signature=VALIDATION_V2)
        result = evaluate_prefill_promotion(
            plan=validation_changed,
            runtime_token=runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(seconds=1),
        )
        self.assertFalse(result.allowed)
        self.assertIn("inspect_validation_signature_mismatch", result.reasons)

        form_changed = make_plan(form_fingerprint="sha256:" + "e" * 64)
        result = evaluate_prefill_promotion(
            plan=form_changed,
            runtime_token=runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(seconds=1),
        )
        self.assertIn("inspect_form_fingerprint_mismatch", result.reasons)

    def test_unbound_or_unready_plan_denies(self):
        plan = make_plan(validation_signature=None)
        runtime = make_runtime()
        bound = make_plan()
        inspect = make_inspect(runtime, bound)
        result = evaluate_prefill_promotion(
            plan=plan,
            runtime_token=runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(seconds=1),
        )
        self.assertIn("plan_validation_unbound", result.reasons)

        blocked = make_plan(state=FormExecutionState.HUMAN_REVIEW_REQUIRED)
        result = evaluate_prefill_promotion(
            plan=blocked,
            runtime_token=runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(seconds=1),
        )
        self.assertIn("plan_not_prefill_ready", result.reasons)

    def test_runtime_version_channel_and_expiry_are_enforced(self):
        plan = make_plan()
        wrong_runtime = make_runtime(executor_version="0.3.0")
        inspect = make_inspect(wrong_runtime, plan)
        result = evaluate_prefill_promotion(
            plan=plan,
            runtime_token=wrong_runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(seconds=1),
        )
        self.assertIn("executor_version_not_certified", result.reasons)

        wrong_channel = make_runtime(browser_channel="chrome")
        inspect = make_inspect(wrong_channel, plan)
        result = evaluate_prefill_promotion(
            plan=plan,
            runtime_token=wrong_channel,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(seconds=1),
        )
        self.assertIn("browser_channel_not_certified", result.reasons)

        short_runtime = make_runtime(ttl_seconds=30, issued_at=NOW)
        short_inspect = make_inspect(short_runtime, plan, ttl_seconds=20)
        result = evaluate_prefill_promotion(
            plan=plan,
            runtime_token=short_runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=short_inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=local_manifest(),
            now=NOW + timedelta(minutes=1),
        )
        self.assertIn("runtime_attestation_invalid", result.reasons)
        self.assertIn("inspect_evidence_invalid", result.reasons)

    def test_manifest_must_certify_provider_origin_and_prefill(self):
        plan = make_plan()
        runtime = make_runtime()
        inspect = make_inspect(runtime, plan)
        uncertified = ProviderCapabilityManifest(
            provider_id="generic_html",
            manifest_version="future-provider-v1",
            allowed_origins=("https://forms.example.org",),
            inspect_allowed=True,
            human_login_allowed=True,
            requires_human_login=True,
            prefill_certified=False,
            submit_certified=False,
            certified_executor_versions=("0.4.0",),
            certified_playwright_versions=("1.62.1",),
            certified_browser_channels=("chromium",),
            evidence_refs=(),
            local_fixture_only=False,
        )
        result = evaluate_prefill_promotion(
            plan=plan,
            runtime_token=runtime,
            runtime_secret=RUNTIME_SECRET,
            inspect_token=inspect,
            inspect_secret=INSPECT_SECRET,
            manifest=uncertified,
            now=NOW + timedelta(seconds=1),
        )
        self.assertIn("provider_prefill_not_certified", result.reasons)
        self.assertIn("provider_origin_not_certified", result.reasons)
        self.assertIn("human_login_evidence_required", result.reasons)

    def test_manifest_loader_is_strict(self):
        raw = json.loads((ROOT / "config" / "form-providers" / "generic-html-local-fixture.json").read_text())
        raw["surprise_permission"] = True
        with self.assertRaisesRegex(ValueError, "unknown keys"):
            provider_manifest_from_mapping(raw)

    def test_repository_has_no_certified_external_or_submit_manifest(self):
        files = sorted((ROOT / "config" / "form-providers").glob("*.json"))
        self.assertTrue(files)
        for path in files:
            manifest = provider_manifest_from_mapping(json.loads(path.read_text()))
            self.assertFalse(manifest.submit_certified, path.name)
            if manifest.prefill_certified:
                self.assertTrue(manifest.local_fixture_only, path.name)


if __name__ == "__main__":
    unittest.main()
