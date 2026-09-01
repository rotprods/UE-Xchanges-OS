from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .fingerprint import canonicalize_form_url


MIN_ATTESTATION_KEY_BYTES = 32
MAX_RUNTIME_TTL_SECONDS = 86_400
MAX_INSPECT_TTL_SECONDS = 3_600
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_RUNTIME_DOMAIN = b"UEX_RUNTIME_ATTESTATION_V1\x00"
_INSPECT_DOMAIN = b"UEX_AUTH_INSPECT_V1\x00"
_ALLOWED_BROWSER_CHANNELS = {"chrome", "chromium", "msedge"}


class AttestationStatus(str, Enum):
    VALID = "valid"
    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    BINDING_MISMATCH = "binding_mismatch"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class RuntimeDoctorEvidence:
    status: str
    node_major: int
    playwright_version: str
    browser_channel: str
    launch: str
    network: str
    profile: str

    def __post_init__(self) -> None:
        if self.status != "ok":
            raise ValueError("runtime doctor status must be ok")
        if not isinstance(self.node_major, int) or isinstance(self.node_major, bool) or self.node_major < 20:
            raise ValueError("runtime doctor requires Node major >= 20")
        if not self.playwright_version.strip():
            raise ValueError("runtime doctor playwright_version must be non-empty")
        if self.browser_channel not in _ALLOWED_BROWSER_CHANNELS:
            raise ValueError("runtime doctor browser_channel is unsupported")
        if self.launch != "ok":
            raise ValueError("runtime doctor launch must be ok")
        if self.network != "blocked":
            raise ValueError("runtime doctor network must be blocked")
        if self.profile != "ephemeral":
            raise ValueError("runtime doctor profile must be ephemeral")


@dataclass(frozen=True)
class RuntimeAttestationClaims:
    attestation_id: str
    runtime_ref: str
    executor_version: str
    playwright_version: str
    browser_channel: str
    profile_mode: str
    doctor_evidence_hash: str
    doctor_passed_at: datetime
    issued_at: datetime
    expires_at: datetime
    nonce: str


@dataclass(frozen=True)
class AuthenticatedInspectClaims:
    evidence_id: str
    runtime_attestation_id: str
    provider_id: str
    canonical_form_url: str
    form_fingerprint: str
    validation_signature: str
    authenticated: bool
    human_login_ref: str | None
    inspected_at: datetime
    expires_at: datetime
    form_values_read: bool
    cookies_read: bool
    storage_state_exported: bool
    nonce: str


@dataclass(frozen=True)
class AttestationVerification:
    status: AttestationStatus
    valid: bool
    reason: str
    claims: RuntimeAttestationClaims | AuthenticatedInspectClaims | None = None


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _require_secret(secret: bytes) -> None:
    if not isinstance(secret, bytes) or len(secret) < MIN_ATTESTATION_KEY_BYTES:
        raise ValueError(f"attestation signing secret must be at least {MIN_ATTESTATION_KEY_BYTES} bytes")


def _require_nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _require_sha256(value: str, name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must use sha256:<64 lowercase hex>")
    return value


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _encode(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def runtime_doctor_evidence_hash(evidence: RuntimeDoctorEvidence) -> str:
    payload = {
        "status": evidence.status,
        "node_major": evidence.node_major,
        "playwright_version": evidence.playwright_version,
        "browser_channel": evidence.browser_channel,
        "launch": evidence.launch,
        "network": evidence.network,
        "profile": evidence.profile,
    }
    return f"sha256:{hashlib.sha256(_encode(payload)).hexdigest()}"


def _sign(domain: bytes, payload: bytes, secret: bytes) -> str:
    return hmac.new(secret, domain + payload, hashlib.sha256).hexdigest()


def _pack(prefix: str, domain: bytes, payload: dict[str, Any], secret: bytes) -> str:
    raw = _encode(payload)
    return f"{prefix}.{_b64encode(raw)}.{_sign(domain, raw, secret)}"


def _unpack(token: str, prefix: str) -> tuple[bytes, str] | None:
    try:
        actual_prefix, payload_part, signature = token.split(".", 2)
        if actual_prefix != prefix:
            return None
        return _b64decode(payload_part), signature
    except Exception:
        return None


def issue_runtime_attestation(
    *,
    runtime_ref: str,
    executor_version: str,
    doctor_evidence: RuntimeDoctorEvidence,
    doctor_passed_at: datetime,
    issued_at: datetime,
    secret: bytes,
    profile_mode: str = "dedicated_persistent",
    ttl_seconds: int = MAX_RUNTIME_TTL_SECONDS,
    nonce: str | None = None,
) -> str:
    """Issue local proof that a restricted browser runtime passed its doctor.

    `runtime_ref` is deliberately opaque and must not contain a hardware serial,
    password, cookie or other secret. The attestation can only be issued from a
    structurally valid, network-isolated doctor result.
    """
    _require_secret(secret)
    runtime_ref = _require_nonempty(runtime_ref, "runtime_ref")
    executor_version = _require_nonempty(executor_version, "executor_version")
    profile_mode = _require_nonempty(profile_mode, "profile_mode")
    if profile_mode != "dedicated_persistent":
        raise ValueError("runtime attestation requires dedicated_persistent profile_mode")
    doctor_hash = runtime_doctor_evidence_hash(doctor_evidence)
    doctor_passed_at = _require_aware(doctor_passed_at, "doctor_passed_at")
    issued_at = _require_aware(issued_at, "issued_at")
    if doctor_passed_at > issued_at:
        raise ValueError("doctor_passed_at cannot be after issued_at")
    if ttl_seconds <= 0 or ttl_seconds > MAX_RUNTIME_TTL_SECONDS:
        raise ValueError(f"ttl_seconds must be between 1 and {MAX_RUNTIME_TTL_SECONDS}")
    token_nonce = nonce or secrets.token_urlsafe(18)
    _require_nonempty(token_nonce, "nonce")
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    attestation_id = f"runtime:{hashlib.sha256(f'{runtime_ref}|{doctor_hash}|{issued_at.isoformat()}|{token_nonce}'.encode()).hexdigest()}"
    payload = {
        "attestation_id": attestation_id,
        "runtime_ref": runtime_ref,
        "executor_version": executor_version,
        "playwright_version": doctor_evidence.playwright_version,
        "browser_channel": doctor_evidence.browser_channel,
        "profile_mode": profile_mode,
        "doctor_evidence_hash": doctor_hash,
        "doctor_passed_at": doctor_passed_at.isoformat(),
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "nonce": token_nonce,
    }
    return _pack("uexrt1", _RUNTIME_DOMAIN, payload, secret)


def _parse_runtime(payload: bytes) -> RuntimeAttestationClaims:
    raw = json.loads(payload.decode("utf-8"))
    claims = RuntimeAttestationClaims(
        attestation_id=_require_nonempty(str(raw["attestation_id"]), "attestation_id"),
        runtime_ref=_require_nonempty(str(raw["runtime_ref"]), "runtime_ref"),
        executor_version=_require_nonempty(str(raw["executor_version"]), "executor_version"),
        playwright_version=_require_nonempty(str(raw["playwright_version"]), "playwright_version"),
        browser_channel=_require_nonempty(str(raw["browser_channel"]), "browser_channel"),
        profile_mode=_require_nonempty(str(raw["profile_mode"]), "profile_mode"),
        doctor_evidence_hash=_require_sha256(str(raw["doctor_evidence_hash"]), "doctor_evidence_hash"),
        doctor_passed_at=_require_aware(datetime.fromisoformat(str(raw["doctor_passed_at"])), "doctor_passed_at"),
        issued_at=_require_aware(datetime.fromisoformat(str(raw["issued_at"])), "issued_at"),
        expires_at=_require_aware(datetime.fromisoformat(str(raw["expires_at"])), "expires_at"),
        nonce=_require_nonempty(str(raw["nonce"]), "nonce"),
    )
    if claims.browser_channel not in _ALLOWED_BROWSER_CHANNELS:
        raise ValueError("runtime attestation browser channel is unsupported")
    if claims.profile_mode != "dedicated_persistent" or claims.doctor_passed_at > claims.issued_at or claims.expires_at <= claims.issued_at:
        raise ValueError("runtime attestation claims violate invariants")
    return claims


def verify_runtime_attestation(*, token: str, secret: bytes, now: datetime) -> AttestationVerification:
    _require_secret(secret)
    now = _require_aware(now, "now")
    unpacked = _unpack(token, "uexrt1")
    if unpacked is None:
        return AttestationVerification(AttestationStatus.MALFORMED, False, "Runtime attestation encoding is malformed.")
    payload, signature = unpacked
    if not hmac.compare_digest(signature, _sign(_RUNTIME_DOMAIN, payload, secret)):
        return AttestationVerification(AttestationStatus.INVALID_SIGNATURE, False, "Runtime attestation signature is invalid.")
    try:
        claims = _parse_runtime(payload)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return AttestationVerification(AttestationStatus.MALFORMED, False, "Runtime attestation claims are malformed.")
    if now < claims.issued_at:
        return AttestationVerification(AttestationStatus.NOT_YET_VALID, False, "Runtime attestation is not yet valid.", claims)
    if now >= claims.expires_at:
        return AttestationVerification(AttestationStatus.EXPIRED, False, "Runtime attestation has expired.", claims)
    return AttestationVerification(AttestationStatus.VALID, True, "Runtime attestation is valid.", claims)


def issue_authenticated_inspect_evidence(
    *,
    runtime_token: str,
    runtime_secret: bytes,
    evidence_secret: bytes,
    provider_id: str,
    canonical_form_url: str,
    form_fingerprint: str,
    validation_signature: str,
    authenticated: bool,
    human_login_ref: str | None,
    inspected_at: datetime,
    now: datetime,
    ttl_seconds: int = MAX_INSPECT_TTL_SECONDS,
    nonce: str | None = None,
) -> str:
    """Issue value-free proof for one inspected form identity on a trusted runtime."""
    runtime = verify_runtime_attestation(token=runtime_token, secret=runtime_secret, now=now)
    if not runtime.valid or not isinstance(runtime.claims, RuntimeAttestationClaims):
        raise ValueError("authenticated inspect evidence requires a valid runtime attestation")
    _require_secret(evidence_secret)
    provider_id = _require_nonempty(provider_id, "provider_id")
    canonical = canonicalize_form_url(canonical_form_url)
    _require_sha256(form_fingerprint, "form_fingerprint")
    _require_sha256(validation_signature, "validation_signature")
    inspected_at = _require_aware(inspected_at, "inspected_at")
    now = _require_aware(now, "now")
    if inspected_at > now:
        raise ValueError("inspected_at cannot be in the future")
    if ttl_seconds <= 0 or ttl_seconds > MAX_INSPECT_TTL_SECONDS:
        raise ValueError(f"ttl_seconds must be between 1 and {MAX_INSPECT_TTL_SECONDS}")
    if authenticated:
        human_login_ref = _require_nonempty(human_login_ref or "", "human_login_ref")
    elif human_login_ref is not None:
        raise ValueError("human_login_ref requires authenticated=True")
    token_nonce = nonce or secrets.token_urlsafe(18)
    _require_nonempty(token_nonce, "nonce")
    expires_at = min(inspected_at + timedelta(seconds=ttl_seconds), runtime.claims.expires_at)
    if expires_at <= now:
        raise ValueError("inspect evidence would already be expired")
    evidence_id = f"inspect:{hashlib.sha256(f'{runtime.claims.attestation_id}|{provider_id}|{canonical}|{form_fingerprint}|{validation_signature}|{inspected_at.isoformat()}|{token_nonce}'.encode()).hexdigest()}"
    payload = {
        "evidence_id": evidence_id,
        "runtime_attestation_id": runtime.claims.attestation_id,
        "provider_id": provider_id,
        "canonical_form_url": canonical,
        "form_fingerprint": form_fingerprint,
        "validation_signature": validation_signature,
        "authenticated": authenticated,
        "human_login_ref": human_login_ref,
        "inspected_at": inspected_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "form_values_read": False,
        "cookies_read": False,
        "storage_state_exported": False,
        "nonce": token_nonce,
    }
    return _pack("uexinsp1", _INSPECT_DOMAIN, payload, evidence_secret)


def _parse_inspect(payload: bytes) -> AuthenticatedInspectClaims:
    raw = json.loads(payload.decode("utf-8"))
    human_login_ref = raw.get("human_login_ref")
    claims = AuthenticatedInspectClaims(
        evidence_id=_require_nonempty(str(raw["evidence_id"]), "evidence_id"),
        runtime_attestation_id=_require_nonempty(str(raw["runtime_attestation_id"]), "runtime_attestation_id"),
        provider_id=_require_nonempty(str(raw["provider_id"]), "provider_id"),
        canonical_form_url=canonicalize_form_url(str(raw["canonical_form_url"])),
        form_fingerprint=_require_sha256(str(raw["form_fingerprint"]), "form_fingerprint"),
        validation_signature=_require_sha256(str(raw["validation_signature"]), "validation_signature"),
        authenticated=bool(raw["authenticated"]),
        human_login_ref=None if human_login_ref is None else _require_nonempty(str(human_login_ref), "human_login_ref"),
        inspected_at=_require_aware(datetime.fromisoformat(str(raw["inspected_at"])), "inspected_at"),
        expires_at=_require_aware(datetime.fromisoformat(str(raw["expires_at"])), "expires_at"),
        form_values_read=bool(raw["form_values_read"]),
        cookies_read=bool(raw["cookies_read"]),
        storage_state_exported=bool(raw["storage_state_exported"]),
        nonce=_require_nonempty(str(raw["nonce"]), "nonce"),
    )
    if claims.authenticated != (claims.human_login_ref is not None):
        raise ValueError("authenticated/human_login_ref claims disagree")
    if claims.expires_at <= claims.inspected_at:
        raise ValueError("inspect evidence expiry is invalid")
    if claims.form_values_read or claims.cookies_read or claims.storage_state_exported:
        raise ValueError("inspect evidence cannot claim unsafe data extraction")
    return claims


def verify_authenticated_inspect_evidence(*, token: str, secret: bytes, now: datetime) -> AttestationVerification:
    _require_secret(secret)
    now = _require_aware(now, "now")
    unpacked = _unpack(token, "uexinsp1")
    if unpacked is None:
        return AttestationVerification(AttestationStatus.MALFORMED, False, "Inspect evidence encoding is malformed.")
    payload, signature = unpacked
    if not hmac.compare_digest(signature, _sign(_INSPECT_DOMAIN, payload, secret)):
        return AttestationVerification(AttestationStatus.INVALID_SIGNATURE, False, "Inspect evidence signature is invalid.")
    try:
        claims = _parse_inspect(payload)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return AttestationVerification(AttestationStatus.MALFORMED, False, "Inspect evidence claims are malformed.")
    if now < claims.inspected_at:
        return AttestationVerification(AttestationStatus.NOT_YET_VALID, False, "Inspect evidence is not yet valid.", claims)
    if now >= claims.expires_at:
        return AttestationVerification(AttestationStatus.EXPIRED, False, "Inspect evidence has expired.", claims)
    return AttestationVerification(AttestationStatus.VALID, True, "Authenticated inspect evidence is valid.", claims)
