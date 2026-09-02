"""Auditable receipts binding WriterAuthorization decisions to exact write leases.

A WriterAuthorizationReceipt is coordination evidence, not a capability, credential,
lease grant, domain authority or permission for an external side effect.  It proves
that a positive WriterAuthorizationDecision was evaluated for one exact proposed
lease/scope against one pre-lease refresh and one health snapshot before the lease
was acquired.

The receipt is intentionally deterministic and secret-free so it can be persisted
in the append-only Agent_Event_Bus and audited later without a signing-key
lifecycle.  Browser/form capabilities remain a separate security boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Sequence

from .bootstrap_guard import LeaseSnapshot, PreLeaseRefresh, SessionSnapshot
from .control_plane_health import ControlPlaneHealthReport
from .writer_authorization import (
    AuthorizationCode,
    WriterAuthorizationDecision,
    WriteIntent,
)

RECEIPT_CONTRACT = "UEX_WRITER_AUTHORIZATION_RECEIPT"
RECEIPT_VERSION = "1.0.0"
DEFAULT_RECEIPT_TTL_SECONDS = 120
MAX_RECEIPT_TTL_SECONDS = 300

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA64 = re.compile(r"^[0-9a-f]{64}$")
_RECEIPT_ID = re.compile(r"^WAZ-[0-9a-f]{24}$")


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def canonical_scope_sha256(scope: str) -> str:
    """Bind authorization to the exact non-empty scope representation.

    We deliberately do not normalize whitespace or reorder scope fragments.  If a
    writer wants to change the representation/scope, it must request a new receipt.
    This is safer than silently broadening an authorization through normalization.
    """

    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("scope must be a non-empty string")
    return hashlib.sha256(scope.encode("utf-8")).hexdigest()


def health_report_sha256(report: ControlPlaneHealthReport) -> str:
    return _canonical_sha256(report.as_dict())


class ReceiptVerificationCode(str, Enum):
    VALID = "VALID"
    AUTHORIZATION_NOT_ALLOWED = "AUTHORIZATION_NOT_ALLOWED"
    AUTHORIZATION_DIGEST_MISMATCH = "AUTHORIZATION_DIGEST_MISMATCH"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    AGENT_MISMATCH = "AGENT_MISMATCH"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    LEASE_ID_MISMATCH = "LEASE_ID_MISMATCH"
    INTENT_MISMATCH = "INTENT_MISMATCH"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    MAIN_SHA_MISMATCH = "MAIN_SHA_MISMATCH"
    MANIFEST_VERSION_MISMATCH = "MANIFEST_VERSION_MISMATCH"
    PRELEASE_EVENT_WATERMARK_MISMATCH = "PRELEASE_EVENT_WATERMARK_MISMATCH"
    PRELEASE_SCAN_MISMATCH = "PRELEASE_SCAN_MISMATCH"
    HEALTH_REPORT_MISMATCH = "HEALTH_REPORT_MISMATCH"
    HEALTH_GENERATION_MISMATCH = "HEALTH_GENERATION_MISMATCH"
    REPAIR_PLAN_MISMATCH = "REPAIR_PLAN_MISMATCH"
    OVERLAP_INVENTORY_MISMATCH = "OVERLAP_INVENTORY_MISMATCH"
    RECEIPT_ISSUED_AFTER_LEASE_ACQUIRE = "RECEIPT_ISSUED_AFTER_LEASE_ACQUIRE"
    RECEIPT_EXPIRED_BEFORE_LEASE_ACQUIRE = "RECEIPT_EXPIRED_BEFORE_LEASE_ACQUIRE"
    MISSING_AUTHORIZATION_RECEIPT = "MISSING_AUTHORIZATION_RECEIPT"
    DUPLICATE_AUTHORIZATION_RECEIPT = "DUPLICATE_AUTHORIZATION_RECEIPT"


@dataclass(frozen=True)
class WriterAuthorizationReceipt:
    receipt_id: str
    issued_at: datetime
    expires_at: datetime
    session_id: str
    agent_id: str
    context_id: str
    manifest_version: str
    observed_main_sha: str
    intent: WriteIntent
    proposed_lease_id: str
    scope_sha256: str
    authorization_decision_digest: str
    authorization_evaluated_at: datetime
    health_report_sha256: str
    health_generated_at: datetime
    prelease_event_watermark: str
    prelease_lease_scan_at: datetime
    overlapping_lease_ids: tuple[str, ...] = ()
    repair_plan_id: str | None = None

    def __post_init__(self) -> None:
        if not _RECEIPT_ID.fullmatch(self.receipt_id):
            raise ValueError("receipt_id must match WAZ-<24 lowercase hex>")
        _aware(self.issued_at, "issued_at")
        _aware(self.expires_at, "expires_at")
        _aware(self.authorization_evaluated_at, "authorization_evaluated_at")
        _aware(self.health_generated_at, "health_generated_at")
        _aware(self.prelease_lease_scan_at, "prelease_lease_scan_at")
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        if not self.session_id or not self.agent_id or not self.context_id:
            raise ValueError("receipt identity fields are required")
        if not self.manifest_version:
            raise ValueError("manifest_version is required")
        if not _SHA40.fullmatch(self.observed_main_sha):
            raise ValueError("observed_main_sha must be lowercase 40-char git SHA")
        if not self.proposed_lease_id:
            raise ValueError("proposed_lease_id is required")
        for field_name in (
            "scope_sha256",
            "authorization_decision_digest",
            "health_report_sha256",
        ):
            if not _SHA64.fullmatch(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be 64 lowercase hex chars")
        if not self.prelease_event_watermark.strip():
            raise ValueError("prelease_event_watermark is required")
        if tuple(sorted(set(self.overlapping_lease_ids))) != self.overlapping_lease_ids:
            raise ValueError("overlapping_lease_ids must be sorted and unique")
        if any(not value for value in self.overlapping_lease_ids):
            raise ValueError("overlapping_lease_ids cannot contain empty values")

    @property
    def coordination_allowed(self) -> bool:
        return True

    @property
    def domain_authority(self) -> bool:
        return False

    @property
    def external_capability(self) -> bool:
        return False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": RECEIPT_CONTRACT,
            "version": RECEIPT_VERSION,
            "receipt_id": self.receipt_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "context_id": self.context_id,
            "manifest_version": self.manifest_version,
            "observed_main_sha": self.observed_main_sha,
            "intent": self.intent.value,
            "proposed_lease_id": self.proposed_lease_id,
            "scope_sha256": self.scope_sha256,
            "authorization_decision_digest": self.authorization_decision_digest,
            "authorization_evaluated_at": self.authorization_evaluated_at.isoformat(),
            "health_report_sha256": self.health_report_sha256,
            "health_generated_at": self.health_generated_at.isoformat(),
            "prelease_event_watermark": self.prelease_event_watermark,
            "prelease_lease_scan_at": self.prelease_lease_scan_at.isoformat(),
            "overlapping_lease_ids": list(self.overlapping_lease_ids),
            "repair_plan_id": self.repair_plan_id,
            "coordination_allowed": True,
            "domain_authority": False,
            "external_capability": False,
        }

    def event_payload(self) -> dict[str, object]:
        """Payload for a WRITER_AUTHORIZATION_GRANTED EventBus event."""

        return self.as_dict()


@dataclass(frozen=True)
class ReceiptVerification:
    allowed: bool
    receipt_id: str
    lease_id: str
    codes: tuple[ReceiptVerificationCode, ...]

    @property
    def primary_code(self) -> ReceiptVerificationCode:
        return self.codes[0]

    def as_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "receipt_id": self.receipt_id,
            "lease_id": self.lease_id,
            "codes": [code.value for code in self.codes],
        }


@dataclass(frozen=True)
class ReceiptAuditFinding:
    lease_id: str
    session_id: str
    receipt_id: str | None
    allowed: bool
    codes: tuple[ReceiptVerificationCode, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "session_id": self.session_id,
            "receipt_id": self.receipt_id,
            "allowed": self.allowed,
            "codes": [code.value for code in self.codes],
        }


def _receipt_claims_without_id(
    *,
    issued_at: datetime,
    expires_at: datetime,
    session: SessionSnapshot,
    manifest_version: str,
    observed_main_sha: str,
    decision: WriterAuthorizationDecision,
    proposed_lease: LeaseSnapshot,
    prelease: PreLeaseRefresh,
    health: ControlPlaneHealthReport,
) -> dict[str, object]:
    return {
        "contract": RECEIPT_CONTRACT,
        "version": RECEIPT_VERSION,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "session_id": session.session_id,
        "agent_id": session.agent_id,
        "context_id": session.context_id,
        "manifest_version": manifest_version,
        "observed_main_sha": observed_main_sha,
        "intent": decision.intent.value,
        "proposed_lease_id": proposed_lease.lease_id,
        "scope_sha256": canonical_scope_sha256(proposed_lease.scope),
        "authorization_decision_digest": decision.decision_digest,
        "authorization_evaluated_at": decision.evaluated_at.isoformat(),
        "health_report_sha256": health_report_sha256(health),
        "health_generated_at": health.generated_at.isoformat(),
        "prelease_event_watermark": prelease.private_event_watermark,
        "prelease_lease_scan_at": prelease.lease_scan_at.isoformat(),
        "overlapping_lease_ids": list(decision.overlapping_lease_ids),
        "repair_plan_id": decision.repair_plan_id,
        "coordination_allowed": True,
        "domain_authority": False,
        "external_capability": False,
    }


def issue_writer_authorization_receipt(
    *,
    decision: WriterAuthorizationDecision,
    session: SessionSnapshot,
    proposed_lease: LeaseSnapshot,
    prelease: PreLeaseRefresh,
    health: ControlPlaneHealthReport,
    manifest_version: str,
    observed_main_sha: str,
    issued_at: datetime,
    ttl_seconds: int = DEFAULT_RECEIPT_TTL_SECONDS,
) -> WriterAuthorizationReceipt:
    """Issue one short-lived coordination receipt for an already-allowed decision.

    The proposed lease's ``acquired_at`` is the intended provider write timestamp.
    The receipt must exist no later than that timestamp and remain valid through it.
    """

    _aware(issued_at, "issued_at")
    if not manifest_version:
        raise ValueError("manifest_version is required")
    if not _SHA40.fullmatch(observed_main_sha):
        raise ValueError("observed_main_sha must be lowercase 40-char git SHA")
    if ttl_seconds <= 0 or ttl_seconds > MAX_RECEIPT_TTL_SECONDS:
        raise ValueError(f"ttl_seconds must be between 1 and {MAX_RECEIPT_TTL_SECONDS}")
    if not decision.coordination_allowed or decision.codes != (AuthorizationCode.ALLOWED,):
        raise ValueError("cannot issue receipt from denied writer authorization")
    if proposed_lease.owner_session_id != session.session_id:
        raise ValueError("proposed lease/session mismatch")
    if proposed_lease.owner_agent_id != session.agent_id:
        raise ValueError("proposed lease/agent mismatch")
    if proposed_lease.context_id != session.context_id:
        raise ValueError("proposed lease/context mismatch")
    if observed_main_sha != prelease.observed_main_sha:
        raise ValueError("observed_main_sha must equal the prelease main SHA")
    if decision.evaluated_at > issued_at:
        raise ValueError("authorization decision cannot be evaluated after receipt issuance")
    if prelease.lease_scan_at > issued_at:
        raise ValueError("prelease scan cannot occur after receipt issuance")
    if issued_at > proposed_lease.acquired_at:
        raise ValueError("receipt must be issued before lease acquisition")

    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    if proposed_lease.acquired_at > expires_at:
        raise ValueError("receipt TTL does not cover proposed lease acquisition")

    claims = _receipt_claims_without_id(
        issued_at=issued_at,
        expires_at=expires_at,
        session=session,
        manifest_version=manifest_version,
        observed_main_sha=observed_main_sha,
        decision=decision,
        proposed_lease=proposed_lease,
        prelease=prelease,
        health=health,
    )
    receipt_id = f"WAZ-{_canonical_sha256(claims)[:24]}"
    return WriterAuthorizationReceipt(
        receipt_id=receipt_id,
        issued_at=issued_at,
        expires_at=expires_at,
        session_id=session.session_id,
        agent_id=session.agent_id,
        context_id=session.context_id,
        manifest_version=manifest_version,
        observed_main_sha=observed_main_sha,
        intent=decision.intent,
        proposed_lease_id=proposed_lease.lease_id,
        scope_sha256=canonical_scope_sha256(proposed_lease.scope),
        authorization_decision_digest=decision.decision_digest,
        authorization_evaluated_at=decision.evaluated_at,
        health_report_sha256=health_report_sha256(health),
        health_generated_at=health.generated_at,
        prelease_event_watermark=prelease.private_event_watermark,
        prelease_lease_scan_at=prelease.lease_scan_at,
        overlapping_lease_ids=tuple(decision.overlapping_lease_ids),
        repair_plan_id=decision.repair_plan_id,
    )


def _dedupe_codes(values: Iterable[ReceiptVerificationCode]) -> tuple[ReceiptVerificationCode, ...]:
    seen: set[ReceiptVerificationCode] = set()
    result: list[ReceiptVerificationCode] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def verify_writer_authorization_receipt(
    *,
    receipt: WriterAuthorizationReceipt,
    decision: WriterAuthorizationDecision,
    session: SessionSnapshot,
    lease: LeaseSnapshot,
    prelease: PreLeaseRefresh,
    health: ControlPlaneHealthReport,
    manifest_version: str,
    observed_main_sha: str,
) -> ReceiptVerification:
    """Fully revalidate a receipt against the exact acquisition evidence."""

    codes: list[ReceiptVerificationCode] = []
    if not decision.coordination_allowed or decision.codes != (AuthorizationCode.ALLOWED,):
        codes.append(ReceiptVerificationCode.AUTHORIZATION_NOT_ALLOWED)
    if receipt.authorization_decision_digest != decision.decision_digest:
        codes.append(ReceiptVerificationCode.AUTHORIZATION_DIGEST_MISMATCH)
    if receipt.session_id != session.session_id or lease.owner_session_id != session.session_id:
        codes.append(ReceiptVerificationCode.SESSION_MISMATCH)
    if receipt.agent_id != session.agent_id or lease.owner_agent_id != session.agent_id:
        codes.append(ReceiptVerificationCode.AGENT_MISMATCH)
    if receipt.context_id != session.context_id or lease.context_id != session.context_id:
        codes.append(ReceiptVerificationCode.CONTEXT_MISMATCH)
    if receipt.proposed_lease_id != lease.lease_id:
        codes.append(ReceiptVerificationCode.LEASE_ID_MISMATCH)
    if receipt.intent is not decision.intent:
        codes.append(ReceiptVerificationCode.INTENT_MISMATCH)
    if receipt.scope_sha256 != canonical_scope_sha256(lease.scope):
        codes.append(ReceiptVerificationCode.SCOPE_MISMATCH)
    if receipt.observed_main_sha != observed_main_sha or prelease.observed_main_sha != observed_main_sha:
        codes.append(ReceiptVerificationCode.MAIN_SHA_MISMATCH)
    if receipt.manifest_version != manifest_version:
        codes.append(ReceiptVerificationCode.MANIFEST_VERSION_MISMATCH)
    if receipt.prelease_event_watermark != prelease.private_event_watermark:
        codes.append(ReceiptVerificationCode.PRELEASE_EVENT_WATERMARK_MISMATCH)
    if receipt.prelease_lease_scan_at != prelease.lease_scan_at:
        codes.append(ReceiptVerificationCode.PRELEASE_SCAN_MISMATCH)
    if receipt.health_report_sha256 != health_report_sha256(health):
        codes.append(ReceiptVerificationCode.HEALTH_REPORT_MISMATCH)
    if receipt.health_generated_at != health.generated_at:
        codes.append(ReceiptVerificationCode.HEALTH_GENERATION_MISMATCH)
    if receipt.repair_plan_id != decision.repair_plan_id:
        codes.append(ReceiptVerificationCode.REPAIR_PLAN_MISMATCH)
    if receipt.overlapping_lease_ids != tuple(decision.overlapping_lease_ids):
        codes.append(ReceiptVerificationCode.OVERLAP_INVENTORY_MISMATCH)
    if receipt.issued_at > lease.acquired_at:
        codes.append(ReceiptVerificationCode.RECEIPT_ISSUED_AFTER_LEASE_ACQUIRE)
    if receipt.expires_at < lease.acquired_at:
        codes.append(ReceiptVerificationCode.RECEIPT_EXPIRED_BEFORE_LEASE_ACQUIRE)

    final = _dedupe_codes(codes)
    if not final:
        final = (ReceiptVerificationCode.VALID,)
    return ReceiptVerification(
        allowed=final == (ReceiptVerificationCode.VALID,),
        receipt_id=receipt.receipt_id,
        lease_id=lease.lease_id,
        codes=final,
    )


def audit_lease_receipt_bindings(
    *,
    leases: Sequence[LeaseSnapshot],
    receipts: Sequence[WriterAuthorizationReceipt],
    effective_at: datetime,
) -> tuple[ReceiptAuditFinding, ...]:
    """Structural audit usable from EventBus/lease snapshots without broker internals.

    This deliberately does not reconstruct a health report or authorization
    decision.  It answers whether each post-contract lease has exactly one receipt
    bound to the same stable identities/scope and valid at acquisition time.
    Full verification is provided by :func:`verify_writer_authorization_receipt`.
    """

    _aware(effective_at, "effective_at")
    by_lease: dict[str, list[WriterAuthorizationReceipt]] = {}
    for receipt in receipts:
        by_lease.setdefault(receipt.proposed_lease_id, []).append(receipt)

    findings: list[ReceiptAuditFinding] = []
    for lease in sorted(leases, key=lambda item: (item.acquired_at, item.lease_id)):
        if lease.acquired_at < effective_at:
            continue
        matches = by_lease.get(lease.lease_id, [])
        if not matches:
            findings.append(
                ReceiptAuditFinding(
                    lease_id=lease.lease_id,
                    session_id=lease.owner_session_id,
                    receipt_id=None,
                    allowed=False,
                    codes=(ReceiptVerificationCode.MISSING_AUTHORIZATION_RECEIPT,),
                )
            )
            continue
        if len(matches) != 1:
            findings.append(
                ReceiptAuditFinding(
                    lease_id=lease.lease_id,
                    session_id=lease.owner_session_id,
                    receipt_id=None,
                    allowed=False,
                    codes=(ReceiptVerificationCode.DUPLICATE_AUTHORIZATION_RECEIPT,),
                )
            )
            continue

        receipt = matches[0]
        codes: list[ReceiptVerificationCode] = []
        if receipt.session_id != lease.owner_session_id:
            codes.append(ReceiptVerificationCode.SESSION_MISMATCH)
        if receipt.agent_id != lease.owner_agent_id:
            codes.append(ReceiptVerificationCode.AGENT_MISMATCH)
        if receipt.context_id != lease.context_id:
            codes.append(ReceiptVerificationCode.CONTEXT_MISMATCH)
        if receipt.scope_sha256 != canonical_scope_sha256(lease.scope):
            codes.append(ReceiptVerificationCode.SCOPE_MISMATCH)
        if receipt.issued_at > lease.acquired_at:
            codes.append(ReceiptVerificationCode.RECEIPT_ISSUED_AFTER_LEASE_ACQUIRE)
        if receipt.expires_at < lease.acquired_at:
            codes.append(ReceiptVerificationCode.RECEIPT_EXPIRED_BEFORE_LEASE_ACQUIRE)
        final = _dedupe_codes(codes)
        if not final:
            final = (ReceiptVerificationCode.VALID,)
        findings.append(
            ReceiptAuditFinding(
                lease_id=lease.lease_id,
                session_id=lease.owner_session_id,
                receipt_id=receipt.receipt_id,
                allowed=final == (ReceiptVerificationCode.VALID,),
                codes=final,
            )
        )
    return tuple(findings)
