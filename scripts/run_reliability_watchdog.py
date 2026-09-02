#!/usr/bin/env python3
"""Run the observation-only UE-Xchanges reliability watchdog from JSON reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uexchanges.bootstrap_guard import parse_iso8601
from uexchanges.control_plane_health import (
    ControlPlaneHealthReport,
    HealthCode,
    HealthFinding,
    HealthSeverity,
    OverallHealth,
    SloResult,
)
from uexchanges.recovery_verifier import (
    RecoveryCode,
    RecoveryFinding,
    RecoveryReport,
    RecoverySeverity,
    RecoveryStatus,
)
from uexchanges.reliability_watchdog import (
    AlertSeverity,
    PreviousAlertState,
    evaluate_reliability_watchdog,
)


def _load(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input JSON must be an object")
    return value


def _health(payload: dict[str, object]) -> ControlPlaneHealthReport:
    findings = tuple(
        HealthFinding(
            code=HealthCode(str(item["code"])),
            severity=HealthSeverity(str(item["severity"])),
            subject_type=str(item["subject_type"]),
            subject_id=str(item["subject_id"]),
            detail=str(item["detail"]),
            repair_action=str(item["repair_action"]),
        )
        for item in payload.get("findings", [])  # type: ignore[union-attr]
    )
    slos = tuple(
        SloResult(
            name=str(item["name"]),
            passed=bool(item["passed"]),
            observed=float(item["observed"]),
            target=str(item["target"]),
        )
        for item in payload.get("slos", [])  # type: ignore[union-attr]
    )
    return ControlPlaneHealthReport(
        generated_at=parse_iso8601(str(payload["generated_at"])),
        overall=OverallHealth(str(payload["overall"])),
        findings=findings,
        metrics={str(k): int(v) for k, v in payload.get("metrics", {}).items()},  # type: ignore[union-attr]
        slos=slos,
    )


def _recovery(payload: dict[str, object] | None) -> RecoveryReport | None:
    if payload is None:
        return None
    findings = tuple(
        RecoveryFinding(
            code=RecoveryCode(str(item["code"])),
            severity=RecoverySeverity(str(item["severity"])),
            subject=str(item["subject"]),
            detail=str(item["detail"]),
            repair_action=str(item["repair_action"]),
        )
        for item in payload.get("findings", [])  # type: ignore[union-attr]
    )
    return RecoveryReport(
        generated_at=parse_iso8601(str(payload["generated_at"])),
        status=RecoveryStatus(str(payload["status"])),
        score=int(payload["score"]),
        findings=findings,
        current_main_sha=str(payload["current_main_sha"]) if payload.get("current_main_sha") else None,
        event_watermark=str(payload["event_watermark"]) if payload.get("event_watermark") else None,
    )


def _previous(values: list[dict[str, object]]) -> tuple[PreviousAlertState, ...]:
    return tuple(
        PreviousAlertState(
            alert_key=str(item["alert_key"]),
            fingerprint=str(item["fingerprint"]),
            severity=AlertSeverity(str(item["severity"])),
            occurrence_count=int(item["occurrence_count"]),
            active=bool(item.get("active", True)),
        )
        for item in values
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out")
    parser.add_argument("--state-out")
    args = parser.parse_args(argv)
    try:
        payload = _load(args.input)
        report = evaluate_reliability_watchdog(
            now=parse_iso8601(str(payload["now"])),
            health=_health(payload["health"]),  # type: ignore[arg-type]
            recovery=_recovery(payload.get("recovery")),  # type: ignore[arg-type]
            previous=_previous(payload.get("previous", [])),  # type: ignore[arg-type]
        )
        report_json = json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"
        state_json = json.dumps(
            [
                {
                    "alert_key": item.alert_key,
                    "fingerprint": item.fingerprint,
                    "severity": item.severity.value,
                    "occurrence_count": item.occurrence_count,
                    "active": item.active,
                }
                for item in report.next_state()
            ],
            indent=2,
            sort_keys=True,
        ) + "\n"
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID_INPUT", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(report_json, encoding="utf-8")
    else:
        sys.stdout.write(report_json)
    if args.state_out:
        Path(args.state_out).write_text(state_json, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
