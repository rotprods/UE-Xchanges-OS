#!/usr/bin/env python3
"""Record a measured zero-context recovery drill from offline evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uexchanges.bootstrap_guard import parse_iso8601
from uexchanges.recovery_drill import RecoveryObjective, record_recovery_drill
from uexchanges.recovery_manifest import (
    PrivateRecoverySource,
    RecoveryArtifactDigest,
    RecoveryManifest,
)
from uexchanges.recovery_verifier import RecoveryStatus


def _manifest(payload: dict[str, object]) -> RecoveryManifest:
    artifacts = tuple(
        RecoveryArtifactDigest(
            path=str(item["path"]),
            sha256=str(item["sha256"]),
            role=str(item["role"]),
            required=bool(item["required"]),
        )
        for item in payload["public_artifacts"]  # type: ignore[index]
    )
    sources = tuple(
        PrivateRecoverySource(
            name=str(item["name"]),
            available=bool(item["available"]),
            watermark=str(item["watermark"]),
        )
        for item in payload["private_sources"]  # type: ignore[index]
    )
    return RecoveryManifest(
        generated_at=parse_iso8601(str(payload["generated_at"])),
        current_main_sha=str(payload["current_main_sha"]),
        event_watermark=str(payload["event_watermark"]),
        bootstrap_manifest_version=str(payload["bootstrap_manifest_version"]),
        command_center_ref=str(payload["command_center_ref"]),
        command_center_watermark=str(payload["command_center_watermark"]),
        public_artifacts=artifacts,
        private_sources=sources,
        bundle_hash=str(payload["bundle_hash"]),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out")
    parser.add_argument("--fail-on-objective", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        objective_data = payload.get("objective") or {}
        objective = RecoveryObjective(
            max_rto_seconds=int(objective_data.get("max_rto_seconds", 300)),
            max_event_loss=int(objective_data.get("max_event_loss", 0)),
        )
        report = record_recovery_drill(
            drill_id=str(payload["drill_id"]),
            started_at=parse_iso8601(str(payload["started_at"])),
            completed_at=parse_iso8601(str(payload["completed_at"])),
            manifest=_manifest(payload["manifest"]),
            source_event_ids=tuple(str(value) for value in payload["source_event_ids"]),
            recovered_event_ids=tuple(str(value) for value in payload["recovered_event_ids"]),
            required_steps={str(key): bool(value) for key, value in payload["required_steps"].items()},
            recovery_status=RecoveryStatus(str(payload["recovery_status"])),
            objective=objective,
        )
        output = json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID_INPUT", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    if args.fail_on_objective and report.status.value != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
