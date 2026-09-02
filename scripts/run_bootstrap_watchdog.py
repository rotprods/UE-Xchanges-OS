#!/usr/bin/env python3
"""Convert a BootstrapGuard audit report into deduplicated watchdog alerts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uexchanges.bootstrap_guard import ComplianceFinding, GuardCode
from uexchanges.bootstrap_watchdog import (
    WatchdogSeverity,
    build_watchdog_report,
    current_state_as_json,
    previous_state_from_json,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_report", type=Path)
    parser.add_argument("--state", type=Path, help="Previous watchdog state JSON")
    parser.add_argument("--write-state", type=Path, help="Write current open-alert state")
    parser.add_argument(
        "--notify-threshold",
        choices=[item.name for item in WatchdogSeverity],
        default="HIGH",
    )
    parser.add_argument("--fail-on-high", action="store_true")
    return parser.parse_args(argv)


def _finding(row):
    codes = row.get("codes")
    if not isinstance(codes, list) or not codes:
        raise ValueError("finding codes must be a non-empty list")
    return ComplianceFinding(
        subject_type=row["subject_type"],
        subject_id=row["subject_id"],
        session_id=row.get("session_id"),
        allowed=bool(row["allowed"]),
        codes=tuple(GuardCode(code) for code in codes),
    )


def build_report(audit_data, *, previous=None, notify_threshold=WatchdogSeverity.HIGH):
    if audit_data.get("contract") != "UEX_BOOTSTRAP_COMPLIANCE_AUDIT":
        raise ValueError("unsupported audit contract")
    findings = [_finding(row) for row in audit_data.get("findings", [])]
    report = build_watchdog_report(
        findings,
        previous=previous,
        notify_threshold=notify_threshold,
    )
    result = report.as_dict()
    result["source_manifest_version"] = audit_data.get("manifest_version")
    result["source_main_sha"] = audit_data.get("observed_main_sha")
    result["source_now"] = audit_data.get("now")
    return report, result


def main(argv=None):
    args = parse_args(argv)
    try:
        audit_data = json.loads(args.audit_report.read_text(encoding="utf-8"))
        previous = {}
        if args.state and args.state.exists():
            previous = previous_state_from_json(json.loads(args.state.read_text(encoding="utf-8")))
        report, result = build_report(
            audit_data,
            previous=previous,
            notify_threshold=WatchdogSeverity[args.notify_threshold],
        )
        if args.write_state:
            args.write_state.parent.mkdir(parents=True, exist_ok=True)
            args.write_state.write_text(
                json.dumps(current_state_as_json(report), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        return 3
    if args.fail_on_high and not report.healthy:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
