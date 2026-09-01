from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from .fingerprint import canonicalize_form_url
from .models import FormExecutionPlan
from .receipts import execution_plan_hash
from .runtime_attestation import (
    AuthenticatedInspectClaims,
    RuntimeAttestationClaims,
    verify_authenticated_inspect_evidence,
    verify_runtime_attestation,
)


_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class ProviderCapabilityManifest:
    provider_id: str
    manifest_version: str
    allowed_origins: tuple[str, ...]
    inspect_allowed: bool
    human_login_allowed: bool
    requires_human_login: bool
    prefill_certified: bool
    submit_certified: bool
    certified_executor_versions: tuple[str, ...]
    certified_playwright_versions: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    local_fixture_only: bool = False

    def __post_init__(self) -> None:
        if not self.provider_id.strip() or not self.manifest_version.strip():
            raise ValueError("provider_id/manifest_version must be non-empty")
        if not self.allowed_origins:
            raise ValueError("allowed_origins must not be empty")
        for origin in self.allowed_origins:
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("allowed_origins must contain absolute HTTP(S) origins")
            if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username or parsed.password:
                raise ValueError("allowed_origins must not contain path/query/fragment/credentials")
            if self.local_fixture_only and parsed.hostname not in _LOOPBACK_HOSTS:
                raise ValueError("local_fixture_only manifests may contain only loopback origins")
        if self.requires_human_login and not self.human_login_allowed:
            raise ValueError("requires_human_login requires human_login_allowed")
        if self.prefill_certified and not self.inspect_allowed:
            raise ValueError("prefill_certified requires inspect_allowed")
        if self.submit_certified and not self.prefill_certified:
            raise ValueError("submit_certified requires prefill_certified")
        if (self.prefill_certified or self.submit_certified) and not self.evidence_refs:
            raise ValueError("certified write/submit capabilities require evidence_refs")
        if self.prefill_certified and (not self.certified_executor_versions or not self.certified_playwright_versions):
            raise ValueError("prefill certification requires executor and Playwright version constraints")


@dataclass(frozen=True)
class PrefillPromotionDecision:
    allowed: bool
    reasons: tuple[str, ...]
    capability_binding_hash: str | None = None
    runtime_attestation_id: str | None = None
    inspect_evidence_id: str | None = None


def _origin(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must be absolute HTTP(S)")
    host = parsed.hostname.lower()
    default_port = 80 if parsed.scheme == "http" else 443
    port = parsed.port or default_port
    return f"{parsed.scheme.lower()}://{host}:{port}"


def _manifest_allows_url(manifest: ProviderCapabilityManifest, url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if manifest.local_fixture_only:
        allowed_pairs = {(urlparse(origin).scheme.lower(), urlparse(origin).hostname.lower()) for origin in manifest.allowed_origins}
        return (parsed.scheme.lower(), parsed.hostname.lower()) in allowed_pairs and parsed.hostname.lower() in _LOOPBACK_HOSTS
    target = _origin(url)
    return target in {_origin(origin) for origin in manifest.allowed_origins}


def evaluate_prefill_promotion(
    *,
    plan: FormExecutionPlan,
    runtime_token: str,
    runtime_secret: bytes,
    inspect_token: str,
    inspect_secret: bytes,
    manifest: ProviderCapabilityManifest,
    now: datetime,
) -> PrefillPromotionDecision:
    """Evaluate PREFILL_ONLY promotion without issuing or exercising browser authority."""
    reasons: list[str] = []
    runtime_result = verify_runtime_attestation(token=runtime_token, secret=runtime_secret, now=now)
    inspect_result = verify_authenticated_inspect_evidence(token=inspect_token, secret=inspect_secret, now=now)

    runtime = runtime_result.claims if runtime_result.valid and isinstance(runtime_result.claims, RuntimeAttestationClaims) else None
    inspect = inspect_result.claims if inspect_result.valid and isinstance(inspect_result.claims, AuthenticatedInspectClaims) else None
    if runtime is None:
        reasons.append("runtime_attestation_invalid")
    if inspect is None:
        reasons.append("inspect_evidence_invalid")

    if not plan.ready_for_prefill:
        reasons.append("plan_not_prefill_ready")
    if not plan.validation_signature:
        reasons.append("plan_validation_unbound")
    if manifest.provider_id != plan.provider:
        reasons.append("provider_manifest_mismatch")
    if not manifest.inspect_allowed:
        reasons.append("provider_inspect_not_certified")
    if not manifest.prefill_certified:
        reasons.append("provider_prefill_not_certified")
    if not _manifest_allows_url(manifest, plan.canonical_form_url):
        reasons.append("provider_origin_not_certified")

    if runtime is not None:
        if runtime.executor_version not in manifest.certified_executor_versions:
            reasons.append("executor_version_not_certified")
        if runtime.playwright_version not in manifest.certified_playwright_versions:
            reasons.append("playwright_version_not_certified")

    if inspect is not None:
        if runtime is not None and inspect.runtime_attestation_id != runtime.attestation_id:
            reasons.append("inspect_runtime_binding_mismatch")
        if inspect.provider_id != plan.provider:
            reasons.append("inspect_provider_mismatch")
        if canonicalize_form_url(inspect.canonical_form_url) != canonicalize_form_url(plan.canonical_form_url):
            reasons.append("inspect_form_url_mismatch")
        if inspect.form_fingerprint != plan.form_fingerprint:
            reasons.append("inspect_form_fingerprint_mismatch")
        if inspect.validation_signature != plan.validation_signature:
            reasons.append("inspect_validation_signature_mismatch")
        if manifest.requires_human_login and not inspect.authenticated:
            reasons.append("human_login_evidence_required")
        if not manifest.requires_human_login and inspect.authenticated and not manifest.human_login_allowed:
            reasons.append("unexpected_authenticated_session")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons or runtime is None or inspect is None:
        return PrefillPromotionDecision(
            allowed=False,
            reasons=unique_reasons,
            runtime_attestation_id=None if runtime is None else runtime.attestation_id,
            inspect_evidence_id=None if inspect is None else inspect.evidence_id,
        )

    binding_raw = "|".join(
        [
            "PREFILL_ONLY",
            plan.application_id,
            execution_plan_hash(plan),
            runtime.attestation_id,
            inspect.evidence_id,
            manifest.provider_id,
            manifest.manifest_version,
        ]
    ).encode("utf-8")
    return PrefillPromotionDecision(
        allowed=True,
        reasons=(),
        capability_binding_hash=f"sha256:{hashlib.sha256(binding_raw).hexdigest()}",
        runtime_attestation_id=runtime.attestation_id,
        inspect_evidence_id=inspect.evidence_id,
    )
