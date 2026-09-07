"""Strict, pure shape guard for canonical Writer Authorization Receipt v1 payloads.

This guard is NOT an authorization broker, lease lock or receipt-signature verifier.
Passing only establishes payload shape. The original decision, health, bootstrap
and exact lease must still pass verify_writer_authorization_receipt(). Never use
this result to acquire a lease by itself. No provider or filesystem effects occur.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

CONTRACT = "UEX_WRITER_AUTHORIZATION_RECEIPT"
VERSION = "1.0.0"
IDENTITY_FIELDS = frozenset({
    "session_id", "agent_id", "context_id", "manifest_version",
    "proposed_lease_id", "prelease_event_watermark",
})
DATE_FIELDS = frozenset({
    "issued_at", "expires_at", "authorization_evaluated_at",
    "health_generated_at", "prelease_lease_scan_at",
})
PATTERNS = {
    "receipt_id": r"WAZ-[0-9a-f]{24}",
    "observed_main_sha": r"[0-9a-f]{40}",
    "scope_sha256": r"[0-9a-f]{64}",
    "authorization_decision_digest": r"[0-9a-f]{64}",
    "health_report_sha256": r"[0-9a-f]{64}",
}
CONSTANTS = {
    "contract": CONTRACT, "version": VERSION,
    "coordination_allowed": True, "domain_authority": False,
    "external_capability": False,
}
INTENTS = frozenset({
    "VERSIONED_CODE", "CONTROL_PLANE_REPAIR", "DERIVED_PROJECTION",
    "CANONICAL_DOMAIN", "EXTERNAL_SIDE_EFFECT",
})
REQUIRED_FIELDS = frozenset(
    IDENTITY_FIELDS | DATE_FIELDS | PATTERNS.keys() | CONSTANTS.keys()
    | {"intent", "overlapping_lease_ids", "repair_plan_id"}
)
_DATE_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)"
)


@dataclass(frozen=True, order=True)
class PayloadIssue:
    field: str
    code: str


class ReceiptPayloadError(ValueError):
    """Value-safe failure: payload values are never embedded in the exception."""
    def __init__(self, issues: tuple[PayloadIssue, ...]) -> None:
        self.issues = issues
        # Do not print unknown property names: provider input may put PII in keys.
        details = ", ".join(
            f"{i.field if i.field in REQUIRED_FIELDS else '$'}:{i.code}"
            for i in issues
        )
        super().__init__("invalid writer receipt payload: " + details)


def _date(value: object) -> datetime | None:
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("z", "+00:00").replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None


def inspect_receipt_payload(raw: object) -> tuple[PayloadIssue, ...]:
    """Validate exact JSON field names/types without coercion or alias repair.

    Like the v1 JSON schema, this checks shape only, not historical validity or
    current acquisition eligibility. An expired historical receipt can have valid
    shape. Receipt TTL/lease timing/broker decisions remain in their own verifier.
    """
    if not isinstance(raw, dict):
        return (PayloadIssue("$", "OBJECT_REQUIRED"),)
    issues: list[PayloadIssue] = []
    if any(not isinstance(key, str) for key in raw):
        issues.append(PayloadIssue("$", "NON_STRING_KEY"))
    for field in sorted(REQUIRED_FIELDS - raw.keys()):
        issues.append(PayloadIssue(field, "REQUIRED_FIELD_MISSING"))
    if raw.keys() - REQUIRED_FIELDS:
        issues.append(PayloadIssue("$", "UNEXPECTED_FIELDS"))
    for field in sorted(IDENTITY_FIELDS):
        if field in raw and (not isinstance(raw[field], str) or not raw[field]):
            issues.append(PayloadIssue(field, "NONEMPTY_STRING_REQUIRED"))
    for field, expected in CONSTANTS.items():
        if field in raw and (type(raw[field]) is not type(expected) or raw[field] != expected):
            issues.append(PayloadIssue(field, "CONSTANT_MISMATCH"))
    for field, pattern in PATTERNS.items():
        if field in raw and (not isinstance(raw[field], str) or re.fullmatch(pattern, raw[field]) is None):
            issues.append(PayloadIssue(field, "PATTERN_MISMATCH"))
    for field in sorted(DATE_FIELDS):
        if field in raw and _date(raw[field]) is None:
            issues.append(PayloadIssue(field, "RFC3339_TIMESTAMP_REQUIRED"))
    if "intent" in raw and (not isinstance(raw["intent"], str) or raw["intent"] not in INTENTS):
        issues.append(PayloadIssue("intent", "UNKNOWN_INTENT"))
    if "overlapping_lease_ids" in raw:
        value = raw["overlapping_lease_ids"]
        if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
            issues.append(PayloadIssue("overlapping_lease_ids", "STRING_ARRAY_REQUIRED"))
        elif len(set(value)) != len(value):
            issues.append(PayloadIssue("overlapping_lease_ids", "DUPLICATE_ITEM"))
    if "repair_plan_id" in raw:
        value = raw["repair_plan_id"]
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"RPL-[0-9a-f]{16}", value)):
            issues.append(PayloadIssue("repair_plan_id", "INVALID_PLAN_REFERENCE"))
    return tuple(sorted(issues))


def require_valid_receipt_payload(raw: object) -> None:
    issues = inspect_receipt_payload(raw)
    if issues:
        raise ReceiptPayloadError(issues)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReceiptPayloadError((PayloadIssue("$", "DUPLICATE_JSON_KEY"),))
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ReceiptPayloadError((PayloadIssue("$", "NONFINITE_JSON_NUMBER"),))


def load_strict_json(text: str) -> Any:
    """Parse JSON with duplicate-key and nonfinite-number rejection at every depth."""
    if not isinstance(text, str):
        raise ReceiptPayloadError((PayloadIssue("$", "JSON_TEXT_REQUIRED"),))
    try:
        raw = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ReceiptPayloadError((PayloadIssue("$", "INVALID_JSON"),)) from exc
    return raw


def load_receipt_json(text: str) -> dict[str, Any]:
    """Decode an exact receipt without type coercion or silent key replacement."""
    raw = load_strict_json(text)
    require_valid_receipt_payload(raw)
    return raw
