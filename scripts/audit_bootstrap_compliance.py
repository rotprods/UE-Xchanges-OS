#!/usr/bin/env python3
"""Audit UE-Xchanges agent bootstrap compliance from a JSON snapshot.

This CLI is intentionally provider-agnostic. Connectors/exporters may build the
input snapshot, but the authorization decision itself stays deterministic and
o-network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uexchanges.bootstrap_guard import (
    BootstrapAckSnapshot,
    BootstrapPolicy,
    LeaseSnapshot,
    PreLeaseRefresh,
    SessionSnapshot,
    audit_control_plane,
    parse_iso8601,
)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="JSON control-plane snapshot")
    parser.add_argument("--fail-on-violation", action="store_true")
    return parser.parse_args(argv)


def _session(row):
    return SessionSnapshot(
        session_id=row["session_id"],
        agent_id=row["agent_id"],
        context_id=row["context_id"],
        started_at=parse_iso8601(row["started_at"]),
        status=row.get("status", "ACTIVE"),
    )


def _ack(row):
    return BootstrapAckSnapshot.from_event_payload(
        event_id=row["event_id"],
        event_at=parse_iso8601(row["event_at"]),
        payload=row["payload"],
    )


def _lease(row):
    return LeaseSnapshot(
        lease_id=row["lease_id"],
        owner_session_id=row["owner_session_id"],
        owner_agent_id=row["owner_agent_id"],
        context_id=row["context_id"],
        scope=row.get("scope", ""),
        acquired_at=parse_iso8601(row["acquired_at"]),
        expires_at=parse_iso8601(row["expires_at"]),
        status=row.get("status", "ACTIVE"),
    )


def _refresh(row):
    return PreLeaseRefresh(
        observed_main_sha=row["observed_main_sha"],
        lease_scan_at=parse_iso8601(row["lease_scan_at"]),
        private_event_watermark=row["private_event_watermark"],
    )


def audit_snapshot(data):
    policy_data = data["policy"]
    policy = BootstrapPolicy(
        manifest_version=policy_data["manifest_version"],
        current_main_sha=policy_data["current_main_sha"],
        context_id=policy_data["context_id"],
        effective_at=parse_iso8601(policy_data["effective_at"]),
        max_prelease_scan_age_seconds=policy_data.get("max_prelease_scan_age_seconds", 120),
    )
    sessions = [_session(row) for row in data.get("sessions", [])]
    acks = [_ack(row) for row in data.get("acks", [])]
    leases = [_lease(row) for row in data.get("leases", [])]
    prelease = {
        lease_id: _refresh(row)
        for lease_id, row in data.get("prelease_refreshes", {}).items()
    }
    now = parse_iso8601(data["now"])
    findings = audit_control_plane(
        policy=policy,
        sessions=sessions,
        acks=acks,
        leases=leases,
        prelease_by_lease=prelease,
        now=now,
    )
    violations = [finding for finding in findings if not finding.allowed]
    return {
        "contract": "UEX_BOOTSTRAP_COMPLIANCE_AUDIT",
        "manifest_version": policy.manifest_version,
        "observed_main_sha": policy.current_main_sha,
        "now": data["now"],
        "finding_count": len(findings),
        "violation_count": len(violations),
        "compliant": not violations,
        "findings": [finding.as_dict() for finding in findings],
    }


def main(argv=None):
    args = _parse_args(argv)
    try:
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
        report = audit_snapshot(data)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        return 3
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.fail_on_violation and not report["compliant"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
