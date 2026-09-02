#!/usr/bin/env python3
"""Build a value-safe UE-Xchanges recovery manifest from an offline JSON input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uexchanges.bootstrap_guard import parse_iso8601
from uexchanges.recovery_manifest import (
    PrivateRecoverySource,
    RecoveryArtifactDigest,
    build_recovery_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        artifacts = tuple(
            RecoveryArtifactDigest(
                path=str(item["path"]),
                sha256=str(item["sha256"]),
                role=str(item["role"]),
                required=bool(item.get("required", True)),
            )
            for item in payload["public_artifacts"]
        )
        sources = tuple(
            PrivateRecoverySource(
                name=str(item["name"]),
                available=bool(item["available"]),
                watermark=str(item.get("watermark", "")),
            )
            for item in payload["private_sources"]
        )
        manifest = build_recovery_manifest(
            generated_at=parse_iso8601(str(payload["generated_at"])),
            current_main_sha=str(payload["current_main_sha"]),
            event_watermark=str(payload["event_watermark"]),
            bootstrap_manifest_version=str(payload["bootstrap_manifest_version"]),
            command_center_ref=str(payload["command_center_ref"]),
            command_center_watermark=str(payload["command_center_watermark"]),
            public_artifacts=artifacts,
            private_sources=sources,
        )
        output = json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n"
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID_INPUT", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
