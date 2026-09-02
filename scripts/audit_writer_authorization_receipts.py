#!/usr/bin/env python3
"""Offline structural audit for Writer Authorization Receipt v1.

Input is a JSON snapshot containing ``effective_at``, ``leases`` and ``receipts``.
The command performs no provider/network/Drive/GitHub writes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from uexchanges.bootstrap_guard import LeaseSnapshot
from uexchanges.writer_authorization import WriteIntent
from uexchanges.writer_authorization_receipt import (
    WriterAuthorizationReceipt,
    audit_lease_receipt_bindings,
)


def dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return parsed


def lease_from_dict(raw: dict[str, object]) -> LeaseSnapshot:
    return LeaseSnapshot(
        lease_id=str(raw["lease_id"]),
        owner_session_id=str(raw["owner_session_id"]),
        owner_agent_id=str(raw["owner_agent_id"]),
        context_id=str(raw["context_id"]),
        scope=str(raw["scope"]),
        acquired_at=dt(str(raw["acquired_at"])),
        expires_at=dt(str(raw["expires_at"])),
        status=str(raw.get("status", "ACTIVE")),
    )


def receipt_from_dict(raw: dict[str, object]) -> WriterAuthorizationReceipt:
    if raw.get("contract") != "UEX_WRITER_AUTHORIZATION_RECEIPT":
        raise ValueError("unexpected receipt contract")
    if raw.get("version") != "1.0.0":
        raise ValueError("unsupported receipt version")
    overlaps = raw.get("overlapping_lease_ids", [])
    if not isinstance(overlaps, list) or not all(isinstance(item, str) for item in overlaps):
        raise ValueError("overlapping_lease_ids must be a list of strings")
    repair_plan = raw.get("repair_plan_id")
    if repair_plan is not None and not isinstance(repair_plan, str):
        raise ValueError("repair_plan_id must be string or null")
    if raw.get("coordination_allowed") is not True:
        raise ValueError("receipt must assert coordination_allowed=true")
    if raw.get("domain_authority") is not False or raw.get("external_capability") is not False:
        raise ValueError("receipt cannot assert domain/external authority")
    return WriterAuthorizationReceipt(
        receipt_id=str(raw["receipt_id"]),
        issued_at=dt(str(raw["issued_at"])),
        expires_at=dt(str(raw["expires_at"])),
        session_id=str(raw["session_id"]),
        agent_id=str(raw["agent_id"]),
        context_id=str(raw["context_id"]),
        manifest_version=str(raw["manifest_version"]),
        observed_main_sha=str(raw["observed_main_sha"]),
        intent=WriteIntent(str(raw["intent"])),
        proposed_lease_id=str(raw["proposed_lease_id"]),
        scope_sha256=str(raw["scope_sha256"]),
        authorization_decision_digest=str(raw["authorization_decision_digest"]),
        authorization_evaluated_at=dt(str(raw["authorization_evaluated_at"])),
        health_report_sha256=str(raw["health_report_sha256"]),
        health_generated_at=dt(str(raw["health_generated_at"])),
        prelease_event_watermark=str(raw["prelease_event_watermark"]),
        prelease_lease_scan_at=dt(str(raw["prelease_lease_scan_at"])),
        overlapping_lease_ids=tuple(overlaps),
        repair_plan_id=repair_plan,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.snapshot.read_text())
    leases_raw = payload.get("leases", [])
    receipts_raw = payload.get("receipts", [])
    if not isinstance(leases_raw, list) or not isinstance(receipts_raw, list):
        raise ValueError("leases and receipts must be arrays")

    findings = audit_lease_receipt_bindings(
        leases=tuple(lease_from_dict(item) for item in leases_raw),
        receipts=tuple(receipt_from_dict(item) for item in receipts_raw),
        effective_at=dt(str(payload["effective_at"])),
    )
    output = {
        "contract": "UEX_WRITER_AUTHORIZATION_RECEIPT_AUDIT",
        "version": "1.0.0",
        "finding_count": sum(1 for item in findings if not item.allowed),
        "lease_count": len(findings),
        "findings": [item.as_dict() for item in findings],
    }
    print(json.dumps(output, sort_keys=True, indent=2))
    return 2 if args.fail_on_findings and output["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
