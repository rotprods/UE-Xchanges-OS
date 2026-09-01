#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
TOOLS = ROOT / "tools" / "form-executor"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uexchanges.forms.activation import (  # noqa: E402
    build_human_login_evidence,
    form_execution_plan_from_mapping,
    human_login_evidence_from_mapping,
    human_login_evidence_to_mapping,
    inspect_identity_from_mapping,
    profile_dir_hash,
    promotion_decision_to_mapping,
    provider_manifest_from_activation_mapping,
    runtime_doctor_envelope,
    runtime_doctor_envelope_from_mapping,
    runtime_doctor_from_mapping,
)
from uexchanges.forms.provider_capability import evaluate_prefill_promotion  # noqa: E402
from uexchanges.forms.runtime_attestation import (  # noqa: E402
    RuntimeAttestationClaims,
    issue_authenticated_inspect_evidence,
    issue_runtime_attestation,
    verify_runtime_attestation,
)

DOCTOR_CLI = TOOLS / "src" / "doctor-cli.mjs"
LOGIN_CLI = TOOLS / "src" / "login-cli.mjs"
INSPECT_CLI = TOOLS / "src" / "cli.mjs"
PACKAGE_JSON = TOOLS / "package.json"
DEFAULT_RUNTIME_SECRET_ENV = "UEX_RUNTIME_ATTESTATION_SECRET"
DEFAULT_INSPECT_SECRET_ENV = "UEX_INSPECT_ATTESTATION_SECRET"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _private_write(path: str | Path, content: str) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        target.parent.chmod(0o700)
    except OSError:
        pass
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, content.encode("utf-8"))
    finally:
        os.close(fd)
    try:
        target.chmod(0o600)
    except OSError:
        pass
    return target


def _private_write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    return _private_write(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _secret_from_env(name: str) -> bytes:
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"required secret environment variable is not set: {name}")
    raw = value.encode("utf-8")
    if len(raw) < 32:
        raise ValueError(f"{name} must contain at least 32 UTF-8 bytes")
    return raw


def _executor_version() -> str:
    package = _read_json(PACKAGE_JSON)
    version = package.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("form-executor package version is missing")
    return version.strip()


def _run_node_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=TOOLS,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        marker = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "NODE_COMMAND_FAILED"
        raise RuntimeError(marker)
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError("Node command did not return a JSON object")
    return payload


def _origin(value: str) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must be absolute HTTP(S)")
    if parsed.username or parsed.password:
        raise ValueError("URL must not contain embedded credentials")
    netloc = parsed.hostname.lower()
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return f"{parsed.scheme.lower()}://{netloc}"


def _origins(url: str, extras: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys([_origin(url), *(_origin(item) for item in extras)]))


def _safe_summary(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def command_doctor(args: argparse.Namespace) -> int:
    raw = _run_node_json(["node", str(DOCTOR_CLI), "--channel", args.channel])
    doctor = runtime_doctor_from_mapping(raw)
    passed_at = _now()
    target = _private_write_json(args.out, runtime_doctor_envelope(doctor=doctor, doctor_passed_at=passed_at))
    _safe_summary(
        {
            "status": "PASS",
            "artifact": str(target),
            "doctor_passed_at": passed_at.isoformat(),
            "node_major": doctor.node_major,
            "playwright_version": doctor.playwright_version,
            "browser_channel": doctor.browser_channel,
            "network": doctor.network,
            "profile": doctor.profile,
        }
    )
    return 0


def command_attest_runtime(args: argparse.Namespace) -> int:
    doctor_raw = _read_json(args.doctor)
    doctor, doctor_passed_at = runtime_doctor_envelope_from_mapping(doctor_raw)
    secret = _secret_from_env(args.secret_env)
    issued_at = _now()
    token = issue_runtime_attestation(
        runtime_ref=args.runtime_ref,
        executor_version=_executor_version(),
        doctor_evidence=doctor,
        doctor_passed_at=doctor_passed_at,
        issued_at=issued_at,
        secret=secret,
        profile_mode="dedicated_persistent",
        ttl_seconds=args.ttl_seconds,
    )
    verified = verify_runtime_attestation(token=token, secret=secret, now=issued_at)
    if not verified.valid or not isinstance(verified.claims, RuntimeAttestationClaims):
        raise RuntimeError("new runtime attestation did not verify")
    target = _private_write(args.out, token + "\n")
    _safe_summary(
        {
            "status": "PASS",
            "artifact": str(target),
            "attestation_id": verified.claims.attestation_id,
            "runtime_ref": verified.claims.runtime_ref,
            "executor_version": verified.claims.executor_version,
            "playwright_version": verified.claims.playwright_version,
            "browser_channel": verified.claims.browser_channel,
            "expires_at": verified.claims.expires_at.isoformat(),
            "secret_exported": False,
        }
    )
    return 0


def command_human_login(args: argparse.Namespace) -> int:
    origins = _origins(args.url, args.allowed_origin)
    command = [
        "node",
        str(LOGIN_CLI),
        "--url",
        args.url,
        "--profile-dir",
        str(Path(args.profile_dir).expanduser()),
        "--channel",
        args.channel,
        "--timeout-ms",
        str(args.timeout_ms),
    ]
    for origin in args.allowed_origin:
        command.extend(["--allowed-origin", origin])
    result = subprocess.run(command, cwd=TOOLS, check=False)
    if result.returncode != 0:
        raise RuntimeError("human login did not complete successfully")
    completed_at = _now()
    evidence = build_human_login_evidence(
        profile_dir=args.profile_dir,
        browser_channel=args.channel,
        allowed_origins=origins,
        completed_at=completed_at,
    )
    target = _private_write_json(args.out, human_login_evidence_to_mapping(evidence))
    _safe_summary(
        {
            "status": "PASS",
            "artifact": str(target),
            "human_login_ref": evidence.human_login_ref,
            "completed_at": completed_at.isoformat(),
            "profile_dir_hash": evidence.profile_dir_hash,
            "browser_channel": evidence.browser_channel,
            "credentials_exported": False,
            "cookies_exported": False,
            "storage_state_exported": False,
        }
    )
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    if args.provider != "generic_html":
        raise ValueError("activation inspect currently supports only provider=generic_html; certify adapters separately")
    origins = _origins(args.url, args.allowed_origin)
    runtime_secret = _secret_from_env(args.runtime_secret_env)
    inspect_secret = _secret_from_env(args.inspect_secret_env)
    runtime_token = Path(args.runtime_token).read_text(encoding="utf-8").strip()

    human_login_ref = None
    authenticated = False
    if args.login_evidence:
        login = human_login_evidence_from_mapping(_read_json(args.login_evidence))
        if login.profile_dir_hash != profile_dir_hash(args.profile_dir):
            raise ValueError("human login evidence does not match the requested dedicated profile")
        if login.browser_channel != args.channel:
            raise ValueError("human login evidence browser channel does not match inspect channel")
        if _origin(args.url) not in login.allowed_origins:
            raise ValueError("human login evidence does not cover the inspect origin")
        human_login_ref = login.human_login_ref
        authenticated = True

    command = [
        "node",
        str(INSPECT_CLI),
        "--url",
        args.url,
        "--profile-dir",
        str(Path(args.profile_dir).expanduser()),
        "--channel",
        args.channel,
        "--timeout-ms",
        str(args.timeout_ms),
        "--headless",
    ]
    for origin in args.allowed_origin:
        command.extend(["--allowed-origin", origin])
    raw = _run_node_json(command)
    identity = inspect_identity_from_mapping(raw, expected_provider=args.provider)
    if identity.browser_channel != args.channel:
        raise ValueError("inspect result browser channel does not match requested channel")
    inspected_at = _now()
    token = issue_authenticated_inspect_evidence(
        runtime_token=runtime_token,
        runtime_secret=runtime_secret,
        evidence_secret=inspect_secret,
        provider_id=identity.provider,
        canonical_form_url=args.url,
        form_fingerprint=identity.form_fingerprint,
        validation_signature=identity.validation_signature,
        authenticated=authenticated,
        human_login_ref=human_login_ref,
        inspected_at=inspected_at,
        now=inspected_at,
        ttl_seconds=args.ttl_seconds,
    )
    token_target = _private_write(args.out_token, token + "\n")
    identity_payload = {
        "schema_version": "0.1.0",
        "provider": identity.provider,
        "page_url": identity.page_url,
        "form_fingerprint": identity.form_fingerprint,
        "validation_signature": identity.validation_signature,
        "browser_channel": identity.browser_channel,
        "profile_mode": identity.profile_mode,
        "authenticated": authenticated,
        "human_login_ref": human_login_ref,
        "inspected_at": inspected_at.isoformat(),
        "safety": {
            "form_values_read": False,
            "url_query_material_exported": False,
            "cookies_read": False,
            "storage_state_exported": False,
        },
    }
    identity_target = _private_write_json(args.identity_out, identity_payload)
    _safe_summary(
        {
            "status": "PASS",
            "inspect_token_artifact": str(token_target),
            "identity_artifact": str(identity_target),
            "provider": identity.provider,
            "form_fingerprint": identity.form_fingerprint,
            "validation_signature": identity.validation_signature,
            "authenticated": authenticated,
            "form_values_exported": False,
            "query_material_exported": False,
            "cookies_exported": False,
            "storage_state_exported": False,
        }
    )
    return 0


def command_provider_candidate(args: argparse.Namespace) -> int:
    origin = _origin(args.origin)
    payload = {
        "provider_id": args.provider,
        "manifest_version": args.manifest_version,
        "allowed_origins": [origin],
        "inspect_allowed": True,
        "human_login_allowed": bool(args.requires_human_login),
        "requires_human_login": bool(args.requires_human_login),
        "prefill_certified": False,
        "submit_certified": False,
        "certified_executor_versions": [_executor_version()],
        "certified_playwright_versions": [args.playwright_version],
        "certified_browser_channels": [args.channel],
        "evidence_refs": [],
        "local_fixture_only": False,
    }
    manifest = provider_manifest_from_activation_mapping(payload)
    if manifest.prefill_certified or manifest.submit_certified:
        raise RuntimeError("provider candidate unexpectedly grants write capability")
    target = _private_write_json(args.out, payload)
    _safe_summary(
        {
            "status": "PASS",
            "artifact": str(target),
            "provider": manifest.provider_id,
            "origin": origin,
            "prefill_certified": False,
            "submit_certified": False,
        }
    )
    return 0


def command_promotion_check(args: argparse.Namespace) -> int:
    plan = form_execution_plan_from_mapping(_read_json(args.plan))
    manifest = provider_manifest_from_activation_mapping(_read_json(args.manifest))
    runtime_token = Path(args.runtime_token).read_text(encoding="utf-8").strip()
    inspect_token = Path(args.inspect_token).read_text(encoding="utf-8").strip()
    runtime_secret = _secret_from_env(args.runtime_secret_env)
    inspect_secret = _secret_from_env(args.inspect_secret_env)
    decision = evaluate_prefill_promotion(
        plan=plan,
        runtime_token=runtime_token,
        runtime_secret=runtime_secret,
        inspect_token=inspect_token,
        inspect_secret=inspect_secret,
        manifest=manifest,
        now=_now(),
    )
    payload = promotion_decision_to_mapping(decision)
    payload["mode"] = "PREFILL_PROMOTION_CHECK_ONLY"
    payload["browser_write_executed"] = False
    payload["submit_executed"] = False
    _safe_summary(payload)
    return 0 if decision.allowed else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uex-form-activate",
        description="Target-Mac activation compiler. It produces evidence and promotion decisions; it never submits a form.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Run the network-isolated browser doctor and persist canonical evidence.")
    doctor.add_argument("--channel", choices=["chrome", "chromium", "msedge"], default="chrome")
    doctor.add_argument("--out", required=True)
    doctor.set_defaults(func=command_doctor)

    attest = sub.add_parser("attest-runtime", help="Issue a locally signed runtime attestation from doctor evidence.")
    attest.add_argument("--doctor", required=True)
    attest.add_argument("--runtime-ref", required=True)
    attest.add_argument("--out", required=True)
    attest.add_argument("--ttl-seconds", type=int, default=14_400)
    attest.add_argument("--secret-env", default=DEFAULT_RUNTIME_SECRET_ENV)
    attest.set_defaults(func=command_attest_runtime)

    login = sub.add_parser("human-login", help="Open the dedicated browser for human-only login/SSO/2FA and persist an opaque login ref.")
    login.add_argument("--url", required=True)
    login.add_argument("--profile-dir", required=True)
    login.add_argument("--allowed-origin", action="append", default=[])
    login.add_argument("--channel", choices=["chrome", "chromium", "msedge"], default="chrome")
    login.add_argument("--timeout-ms", type=int, default=20_000)
    login.add_argument("--out", required=True)
    login.set_defaults(func=command_human_login)

    inspect = sub.add_parser("inspect", help="Run value-free INSPECT and issue signed inspect evidence.")
    inspect.add_argument("--url", required=True)
    inspect.add_argument("--profile-dir", required=True)
    inspect.add_argument("--allowed-origin", action="append", default=[])
    inspect.add_argument("--channel", choices=["chrome", "chromium", "msedge"], default="chrome")
    inspect.add_argument("--timeout-ms", type=int, default=20_000)
    inspect.add_argument("--provider", default="generic_html")
    inspect.add_argument("--runtime-token", required=True)
    inspect.add_argument("--login-evidence")
    inspect.add_argument("--out-token", required=True)
    inspect.add_argument("--identity-out", required=True)
    inspect.add_argument("--ttl-seconds", type=int, default=1_800)
    inspect.add_argument("--runtime-secret-env", default=DEFAULT_RUNTIME_SECRET_ENV)
    inspect.add_argument("--inspect-secret-env", default=DEFAULT_INSPECT_SECRET_ENV)
    inspect.set_defaults(func=command_inspect)

    candidate = sub.add_parser("provider-candidate", help="Create an explicitly NON-CERTIFIED provider manifest candidate.")
    candidate.add_argument("--provider", required=True)
    candidate.add_argument("--origin", required=True)
    candidate.add_argument("--manifest-version", required=True)
    candidate.add_argument("--playwright-version", default="1.62.1")
    candidate.add_argument("--channel", choices=["chrome", "chromium", "msedge"], default="chrome")
    candidate.add_argument("--requires-human-login", action="store_true")
    candidate.add_argument("--out", required=True)
    candidate.set_defaults(func=command_provider_candidate)

    promotion = sub.add_parser("promotion-check", help="Evaluate the pure PREFILL promotion gate. No browser write is executed.")
    promotion.add_argument("--plan", required=True)
    promotion.add_argument("--manifest", required=True)
    promotion.add_argument("--runtime-token", required=True)
    promotion.add_argument("--inspect-token", required=True)
    promotion.add_argument("--runtime-secret-env", default=DEFAULT_RUNTIME_SECRET_ENV)
    promotion.add_argument("--inspect-secret-env", default=DEFAULT_INSPECT_SECRET_ENV)
    promotion.set_defaults(func=command_promotion_check)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as error:
        error_type = type(error).__name__.replace(" ", "_")
        sys.stderr.write(f"UEX_FORM_ACTIVATION_ERROR:{error_type}:{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
