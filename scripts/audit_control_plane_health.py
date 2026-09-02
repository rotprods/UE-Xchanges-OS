#!/usr/bin/env python3
"""Offline CLI for UE-Xchanges control-plane health and recovery drills.

Inputs are exported JSON snapshots.  The command performs no network/provider
writes and is safe to run in CI, a recovery environment or on the local Mac.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from uexchanges.control_plane_health import (
    ContextHealthRecord,
    HealthPolicy,
    LeaseHealthRecord,
    ProjectionHealthRecord,
    SessionHealthRecord,
    evaluate_control_plane_health,
)
from uexchanges.recovery_verifier import (
    RecoveryArtifact,
    RecoveryPolicy,
    verify_recovery,
)
from uexchanges.bootstrap_guard import parse_iso8601


def _load(path: str) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("input JSON must be an object")
    return loaded


def _session(item: dict[str, Any]) -> SessionHealthRecord:
    return SessionHealthRecord(
        session_id=str(item["session_id"]),
        agent_id=str(item["agent_id"]),
        context_id=str(item["context_id"]),
        started_at=parse_iso8601(str(item["started_at"])),
        last_heartbeat=parse_iso8601(str(item["last_heartbeat"])),
        status=str(item["status"]),
    )


def _lease(item: dict[str, Any]) -> LeaseHealthRecord:
    return LeaseHealthRecord(
        lease_id=str(item["lease_id"]),
        owner_session_id=str(item["owner_session_id"]),
        owner_agent_id=str(item["owner_agent_id"]),
        context_id=str(item["context_id"]),
        scope=str(item["scope"]),
        acquired_at=parse_iso8601(str(item["acquired_at"])),
        expires_at=parse_iso8601(str(item["expires_at"])),
        last_heartbeat=parse_iso8601(str(item["last_heartbeat"])),
        status=str(item["status"]),
    )


def _context(item: dict[str, Any]) -> ContextHealthRecord:
    return ContextHealthRecord(
        context_id=str(item["context_id"]),
        updated_at=parse_iso8601(str(item["updated_at"])),
        status=str(item["status"]),
        last_event_id=str(item.get("last_event_id", "")),
    )


def _projection(item: dict[str, Any]) -> ProjectionHealthRecord:
    return ProjectionHealthRecord(
        name=str(item["name"]),
        generated_at=parse_iso8601(str(item["generated_at"])),
        watermark=str(item.get("watermark", "")),
    )


def run_health(payload: dict[str, Any]) -> dict[str, object]:
    policy_data = payload.get("policy") or {}
    policy = HealthPolicy(**policy_data)
    report = evaluate_control_plane_health(
        now=parse_iso8601(str(payload["now"])),
        sessions=tuple(_session(item) for item in payload.get("sessions", [])),
        leases=tuple(_lease(item) for item in payload.get("leases", [])),
        contexts=tuple(_context(item) for item in payload.get("contexts", [])),
        projections=tuple(_projection(item) for item in payload.get("projections", [])),
        bootstrap_noncompliant_count=int(payload.get("bootstrap_noncompliant_count", 0)),
        dead_letter_count=int(payload.get("dead_letter_count", 0)),
        policy=policy,
    )
    return report.as_dict()


def _artifact(item: dict[str, Any]) -> RecoveryArtifact:
    updated = item.get("updated_at")
    return RecoveryArtifact(
        path=str(item["path"]),
        exists=bool(item["exists"]),
        role=str(item["role"]),
        updated_at=parse_iso8601(str(updated)) if updated else None,
        embedded_main_sha=str(item["embedded_main_sha"]) if item.get("embedded_main_sha") else None,
        snapshot=bool(item.get("snapshot", False)),
    )


def run_recovery(payload: dict[str, Any]) -> dict[str, object]:
    policy_data = payload.get("policy") or {}
    if "required_private_sources" in policy_data:
        policy_data = dict(policy_data)
        policy_data["required_private_sources"] = tuple(policy_data["required_private_sources"])
    policy = RecoveryPolicy(**policy_data)
    report = verify_recovery(
        now=parse_iso8601(str(payload["now"])),
        current_main_sha=payload.get("current_main_sha"),
        event_watermark=payload.get("event_watermark"),
        required_public_paths=tuple(str(v) for v in payload.get("required_public_paths", [])),
        manifest_required_reads=tuple(str(v) for v in payload.get("manifest_required_reads", [])),
        artifacts=tuple(_artifact(item) for item in payload.get("artifacts", [])),
        private_sources_available={str(k): bool(v) for k, v in (payload.get("private_sources_available") or {}).items()},
        command_center_available=bool(payload.get("command_center_available", False)),
        stable_documents={str(k): str(v) for k, v in (payload.get("stable_documents") or {}).items()},
        policy=policy,
    )
    return report.as_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("health", "recovery"))
    parser.add_argument("input")
    parser.add_argument("--fail-on-degraded", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = _load(args.input)
        result = run_health(payload) if args.mode == "health" else run_recovery(payload)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID_INPUT", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.fail_on_degraded:
        status = str(result.get("overall") or result.get("status"))
        if status not in {"GREEN", "RECOVERABLE"}:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
