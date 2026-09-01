from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from ..models import AIPolicy
from .models import (
    AuthRequirement,
    FieldOwnership,
    FieldSensitivity,
    FormExecutionPlan,
    FormExecutionState,
    FormField,
    FormFieldType,
    SubmitAuthority,
)
from .provider_capability import PrefillPromotionDecision, ProviderCapabilityManifest, provider_manifest_from_mapping
from .runtime_attestation import RuntimeDoctorEvidence


_SHA256_PREFIX = "sha256:"
_DOCTOR_KEYS = {
    "status",
    "node_major",
    "playwright_version",
    "browser_channel",
    "launch",
    "network",
    "profile",
}
_DOCTOR_ENVELOPE_KEYS = {"schema_version", "doctor", "doctor_passed_at"}
_LOGIN_EVIDENCE_KEYS = {
    "schema_version",
    "human_login_ref",
    "completed_at",
    "profile_dir_hash",
    "browser_channel",
    "allowed_origins",
}
_PLAN_KEYS = {
    "plan_id",
    "application_id",
    "opportunity_id",
    "canonical_form_url",
    "provider",
    "form_fingerprint",
    "validation_signature",
    "fields",
    "ai_policy",
    "auth_requirement",
    "submit_authority",
    "allowed_origins",
    "created_at",
    "expires_at",
    "source_version",
    "attachments",
    "state",
}
_PLAN_REQUIRED_KEYS = _PLAN_KEYS - {"validation_signature", "attachments"}
_FIELD_KEYS = {
    "field_key",
    "label",
    "field_type",
    "required",
    "options",
    "maxlength",
    "answer",
    "answer_source",
    "evidence_ids",
    "ownership",
    "sensitivity",
    "editable_by_agent",
}
_FIELD_REQUIRED_KEYS = {
    "field_key",
    "label",
    "field_type",
    "required",
    "ownership",
    "sensitivity",
    "editable_by_agent",
}
_SAFE_INSPECT_FLAGS = {
    "form_values_read": False,
    "url_query_material_exported": False,
    "cookies_read": False,
    "storage_state_exported": False,
    "mutating_http_methods_blocked": True,
    "submit_events_blocked": True,
}


def _strict_keys(raw: Mapping[str, Any], *, allowed: set[str], required: set[str], name: str) -> None:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be an object")
    actual = set(raw)
    missing = required - actual
    unknown = actual - allowed
    if missing:
        raise ValueError(f"{name} missing keys: {','.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{name} has unknown keys: {','.join(sorted(unknown))}")


def _parse_datetime(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 datetime") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return parsed


def _require_hash(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith(_SHA256_PREFIX):
        raise ValueError(f"{name} must use sha256:<64 lowercase hex>")
    digest = value[len(_SHA256_PREFIX) :]
    if any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must use sha256:<64 lowercase hex>")
    return value


def _require_string_list(value: Any, name: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be an array of strings")
    if nonempty and not value:
        raise ValueError(f"{name} must not be empty")
    return tuple(value)


def _origin(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("origin source must be absolute HTTP(S)")
    if parsed.username or parsed.password:
        raise ValueError("origin source must not contain credentials")
    netloc = parsed.hostname.lower()
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return f"{parsed.scheme.lower()}://{netloc}"


def profile_dir_hash(profile_dir: str | Path) -> str:
    resolved = str(Path(profile_dir).expanduser().resolve())
    return f"sha256:{hashlib.sha256(resolved.encode('utf-8')).hexdigest()}"


def runtime_doctor_from_mapping(raw: Mapping[str, Any]) -> RuntimeDoctorEvidence:
    _strict_keys(raw, allowed=_DOCTOR_KEYS, required=_DOCTOR_KEYS, name="runtime doctor")
    if not isinstance(raw["node_major"], int) or isinstance(raw["node_major"], bool):
        raise ValueError("runtime doctor node_major must be an integer")
    for key in _DOCTOR_KEYS - {"node_major"}:
        if not isinstance(raw[key], str):
            raise ValueError(f"runtime doctor {key} must be a string")
    return RuntimeDoctorEvidence(
        status=raw["status"],
        node_major=raw["node_major"],
        playwright_version=raw["playwright_version"],
        browser_channel=raw["browser_channel"],
        launch=raw["launch"],
        network=raw["network"],
        profile=raw["profile"],
    )


def runtime_doctor_envelope(*, doctor: RuntimeDoctorEvidence, doctor_passed_at: datetime) -> dict[str, Any]:
    if doctor_passed_at.tzinfo is None or doctor_passed_at.utcoffset() is None:
        raise ValueError("doctor_passed_at must be timezone-aware")
    return {
        "schema_version": "0.1.0",
        "doctor": {
            "status": doctor.status,
            "node_major": doctor.node_major,
            "playwright_version": doctor.playwright_version,
            "browser_channel": doctor.browser_channel,
            "launch": doctor.launch,
            "network": doctor.network,
            "profile": doctor.profile,
        },
        "doctor_passed_at": doctor_passed_at.isoformat(),
    }


def runtime_doctor_envelope_from_mapping(raw: Mapping[str, Any]) -> tuple[RuntimeDoctorEvidence, datetime]:
    _strict_keys(raw, allowed=_DOCTOR_ENVELOPE_KEYS, required=_DOCTOR_ENVELOPE_KEYS, name="doctor envelope")
    if raw["schema_version"] != "0.1.0":
        raise ValueError("unsupported doctor envelope schema_version")
    return runtime_doctor_from_mapping(raw["doctor"]), _parse_datetime(raw["doctor_passed_at"], "doctor_passed_at")


@dataclass(frozen=True)
class HumanLoginEvidence:
    human_login_ref: str
    completed_at: datetime
    profile_dir_hash: str
    browser_channel: str
    allowed_origins: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.human_login_ref.startswith("human-login:") or len(self.human_login_ref) != len("human-login:") + 64:
            raise ValueError("human_login_ref must use human-login:<64 hex>")
        if any(char not in "0123456789abcdef" for char in self.human_login_ref.split(":", 1)[1]):
            raise ValueError("human_login_ref must use human-login:<64 hex>")
        _require_hash(self.profile_dir_hash, "profile_dir_hash")
        if self.completed_at.tzinfo is None or self.completed_at.utcoffset() is None:
            raise ValueError("completed_at must be timezone-aware")
        if self.browser_channel not in {"chrome", "chromium", "msedge"}:
            raise ValueError("browser_channel must be chrome, chromium or msedge")
        if not self.allowed_origins:
            raise ValueError("allowed_origins must not be empty")
        for origin in self.allowed_origins:
            if _origin(origin) != origin:
                raise ValueError("allowed_origins must contain normalized origins")


def build_human_login_evidence(
    *,
    profile_dir: str | Path,
    browser_channel: str,
    allowed_origins: tuple[str, ...],
    completed_at: datetime,
    nonce: str | None = None,
) -> HumanLoginEvidence:
    normalized_origins = tuple(dict.fromkeys(_origin(origin) for origin in allowed_origins))
    profile_hash = profile_dir_hash(profile_dir)
    token_nonce = nonce or secrets.token_urlsafe(18)
    if not token_nonce.strip():
        raise ValueError("nonce must be non-empty")
    raw = "|".join([profile_hash, browser_channel, *normalized_origins, completed_at.isoformat(), token_nonce]).encode("utf-8")
    return HumanLoginEvidence(
        human_login_ref=f"human-login:{hashlib.sha256(raw).hexdigest()}",
        completed_at=completed_at,
        profile_dir_hash=profile_hash,
        browser_channel=browser_channel,
        allowed_origins=normalized_origins,
    )


def human_login_evidence_to_mapping(evidence: HumanLoginEvidence) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "human_login_ref": evidence.human_login_ref,
        "completed_at": evidence.completed_at.isoformat(),
        "profile_dir_hash": evidence.profile_dir_hash,
        "browser_channel": evidence.browser_channel,
        "allowed_origins": list(evidence.allowed_origins),
    }


def human_login_evidence_from_mapping(raw: Mapping[str, Any]) -> HumanLoginEvidence:
    _strict_keys(raw, allowed=_LOGIN_EVIDENCE_KEYS, required=_LOGIN_EVIDENCE_KEYS, name="human login evidence")
    if raw["schema_version"] != "0.1.0":
        raise ValueError("unsupported human login evidence schema_version")
    if not isinstance(raw["human_login_ref"], str) or not isinstance(raw["profile_dir_hash"], str) or not isinstance(raw["browser_channel"], str):
        raise ValueError("human login evidence identifiers must be strings")
    return HumanLoginEvidence(
        human_login_ref=raw["human_login_ref"],
        completed_at=_parse_datetime(raw["completed_at"], "completed_at"),
        profile_dir_hash=raw["profile_dir_hash"],
        browser_channel=raw["browser_channel"],
        allowed_origins=_require_string_list(raw["allowed_origins"], "allowed_origins", nonempty=True),
    )


@dataclass(frozen=True)
class InspectIdentityEvidence:
    provider: str
    form_fingerprint: str
    validation_signature: str
    page_url: str
    browser_channel: str
    profile_mode: str


def inspect_identity_from_mapping(raw: Mapping[str, Any], *, expected_provider: str = "generic_html") -> InspectIdentityEvidence:
    if not isinstance(raw, Mapping):
        raise ValueError("inspect result must be an object")
    if raw.get("mode") != "INSPECT_ONLY":
        raise ValueError("inspect result must use INSPECT_ONLY mode")
    if raw.get("identity_version") != "0.1.0":
        raise ValueError("inspect result identity_version is unsupported")
    if raw.get("provider") != expected_provider:
        raise ValueError("inspect result provider does not match expected provider")
    if raw.get("profile_mode") != "dedicated_persistent":
        raise ValueError("inspect result must use dedicated_persistent profile_mode")
    browser_channel = raw.get("browser_channel")
    if browser_channel not in {"chrome", "chromium", "msedge"}:
        raise ValueError("inspect result browser_channel is unsupported")
    safety = raw.get("safety")
    if not isinstance(safety, Mapping):
        raise ValueError("inspect result safety block is required")
    for key, expected in _SAFE_INSPECT_FLAGS.items():
        if type(safety.get(key)) is not bool or safety.get(key) is not expected:
            raise ValueError(f"inspect safety invariant failed: {key}")
    page = raw.get("page")
    if not isinstance(page, Mapping) or not isinstance(page.get("url"), str):
        raise ValueError("inspect result page.url is required")
    page_url = page["url"]
    if "?" in page_url or "#" in page_url:
        raise ValueError("inspect result page.url must not export query or fragment material")
    parsed_page = urlparse(page_url)
    if parsed_page.username or parsed_page.password:
        raise ValueError("inspect result page.url must not contain credentials")
    return InspectIdentityEvidence(
        provider=expected_provider,
        form_fingerprint=_require_hash(raw.get("form_fingerprint"), "form_fingerprint"),
        validation_signature=_require_hash(raw.get("validation_signature"), "validation_signature"),
        page_url=page_url,
        browser_channel=browser_channel,
        profile_mode="dedicated_persistent",
    )


def _form_field_from_mapping(raw: Mapping[str, Any]) -> FormField:
    _strict_keys(raw, allowed=_FIELD_KEYS, required=_FIELD_REQUIRED_KEYS, name="form field")
    if type(raw["required"]) is not bool or type(raw["editable_by_agent"]) is not bool:
        raise ValueError("form field required/editable_by_agent must be booleans")
    options = _require_string_list(raw.get("options", []), "field.options")
    evidence_ids = _require_string_list(raw.get("evidence_ids", []), "field.evidence_ids")
    maxlength = raw.get("maxlength")
    if maxlength is not None and (not isinstance(maxlength, int) or isinstance(maxlength, bool)):
        raise ValueError("field.maxlength must be an integer or null")
    answer_source = raw.get("answer_source")
    if answer_source is not None and not isinstance(answer_source, str):
        raise ValueError("field.answer_source must be a string or null")
    return FormField(
        field_key=str(raw["field_key"]),
        label=str(raw["label"]),
        field_type=FormFieldType(str(raw["field_type"])),
        required=raw["required"],
        options=options,
        maxlength=maxlength,
        answer=raw.get("answer"),
        answer_source=answer_source,
        evidence_ids=evidence_ids,
        ownership=FieldOwnership(str(raw["ownership"])),
        sensitivity=FieldSensitivity(str(raw["sensitivity"])),
        editable_by_agent=raw["editable_by_agent"],
    )


def form_execution_plan_from_mapping(raw: Mapping[str, Any]) -> FormExecutionPlan:
    _strict_keys(raw, allowed=_PLAN_KEYS, required=_PLAN_REQUIRED_KEYS, name="form execution plan")
    fields_raw = raw["fields"]
    if not isinstance(fields_raw, list):
        raise ValueError("form execution plan fields must be an array")
    validation_signature = raw.get("validation_signature")
    if validation_signature is not None:
        validation_signature = _require_hash(validation_signature, "validation_signature")
    return FormExecutionPlan(
        plan_id=str(raw["plan_id"]),
        application_id=str(raw["application_id"]),
        opportunity_id=str(raw["opportunity_id"]),
        canonical_form_url=str(raw["canonical_form_url"]),
        provider=str(raw["provider"]),
        form_fingerprint=str(raw["form_fingerprint"]),
        validation_signature=validation_signature,
        fields=tuple(_form_field_from_mapping(item) for item in fields_raw),
        ai_policy=AIPolicy(str(raw["ai_policy"])),
        auth_requirement=AuthRequirement(str(raw["auth_requirement"])),
        submit_authority=SubmitAuthority(str(raw["submit_authority"])),
        allowed_origins=_require_string_list(raw["allowed_origins"], "allowed_origins", nonempty=True),
        created_at=_parse_datetime(raw["created_at"], "created_at"),
        expires_at=_parse_datetime(raw["expires_at"], "expires_at"),
        source_version=str(raw["source_version"]),
        attachments=_require_string_list(raw.get("attachments", []), "attachments"),
        state=FormExecutionState(str(raw["state"])),
    )


def provider_manifest_from_activation_mapping(raw: Mapping[str, Any]) -> ProviderCapabilityManifest:
    return provider_manifest_from_mapping(raw)


def promotion_decision_to_mapping(decision: PrefillPromotionDecision) -> dict[str, Any]:
    return {
        "allowed": decision.allowed,
        "reasons": list(decision.reasons),
        "capability_binding_hash": decision.capability_binding_hash,
        "runtime_attestation_id": decision.runtime_attestation_id,
        "inspect_evidence_id": decision.inspect_evidence_id,
    }
