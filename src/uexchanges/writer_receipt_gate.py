"""Pure integration boundary for exact writer authorization receipts.

This module composes the existing broker, issuer, shape guard, content-integrity
check and full verifier. It performs no provider writes and supplies no lock or
external capability. Callers must persist the receipt before acquiring the exact
lease through their own concurrency-safe provider adapter. A shape-valid receipt
alone is insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from .bootstrap_guard import BootstrapAckSnapshot, LeaseSnapshot, PreLeaseRefresh, SessionSnapshot
from .control_plane_health import ControlPlaneHealthReport
from .writer_authorization import (
    WriteIntent,
    WriterAuthorizationDecision,
    WriterAuthorizationPolicy,
    authorize_writer,
)
from .writer_authorization_receipt import (
    DEFAULT_RECEIPT_TTL_SECONDS,
    ReceiptVerification,
    WriterAuthorizationReceipt,
    issue_writer_authorization_receipt,
    verify_writer_authorization_receipt,
)
from .writer_receipt_integrity import ReceiptIntegrityError, require_receipt_integrity
from .writer_receipt_payload import require_valid_receipt_payload


class WriterPreparationDenied(ValueError):
    """Only fixed reason codes are exposed, never source values or private IDs."""

    def __init__(self, codes: tuple[str, ...]):
        self.codes = codes
        super().__init__("writer preparation denied: " + ",".join(codes))


@dataclass(frozen=True)
class PreparedWriterAuthorization:
    decision: WriterAuthorizationDecision
    receipt: WriterAuthorizationReceipt
    verification: ReceiptVerification

    def authorization_event_payload(self) -> dict[str, object]:
        """Return the canonical payload, not an envelope with extra metadata."""

        payload = self.receipt.event_payload()
        require_valid_receipt_payload(payload)
        require_receipt_integrity(self.receipt, decision=self.decision)
        return payload

    def acquisition_event_refs(self) -> dict[str, str]:
        """References only: caller must not claim acquisition until it occurred."""

        return {
            "authorization_receipt_id": self.receipt.receipt_id,
            "authorization_decision_digest": self.decision.decision_digest,
            "writer_authorization_receipt_version": "1.0.0",
        }


def _integrity_or_denied(
    receipt: WriterAuthorizationReceipt,
    *,
    decision: WriterAuthorizationDecision,
) -> None:
    try:
        require_receipt_integrity(receipt, decision=decision)
    except ReceiptIntegrityError as exc:
        raise WriterPreparationDenied(tuple(code.value for code in exc.codes)) from exc


def prepare_writer_authorization(
    *,
    policy: WriterAuthorizationPolicy,
    session: SessionSnapshot,
    ack: BootstrapAckSnapshot,
    proposed_lease: LeaseSnapshot,
    prelease: PreLeaseRefresh,
    health: ControlPlaneHealthReport,
    now: datetime,
    overlapping_unexpired_lease_ids: Sequence[str],
    intent: WriteIntent = WriteIntent.VERSIONED_CODE,
    repair_plan_id: str | None = None,
    ttl_seconds: int = DEFAULT_RECEIPT_TTL_SECONDS,
) -> PreparedWriterAuthorization:
    """Evaluate and serialize a new receipt; never accept a caller's ALLOWED flag.

    The explicitly supplied overlap inventory is mandatory even when empty.
    Health and snapshots must come from the caller's fresh authoritative reads.
    This function cannot itself establish that those reads were truthful.
    """

    decision = authorize_writer(
        policy=policy,
        session=session,
        ack=ack,
        proposed_lease=proposed_lease,
        prelease=prelease,
        health=health,
        now=now,
        overlapping_unexpired_lease_ids=overlapping_unexpired_lease_ids,
        intent=intent,
        repair_plan_id=repair_plan_id,
    )
    if not decision.coordination_allowed:
        raise WriterPreparationDenied(tuple(code.value for code in decision.codes))
    receipt = issue_writer_authorization_receipt(
        decision=decision,
        session=session,
        proposed_lease=proposed_lease,
        prelease=prelease,
        health=health,
        manifest_version=policy.bootstrap.manifest_version,
        observed_main_sha=policy.bootstrap.current_main_sha,
        issued_at=now,
        ttl_seconds=ttl_seconds,
    )
    require_valid_receipt_payload(receipt.event_payload())
    _integrity_or_denied(receipt, decision=decision)
    verification = verify_writer_authorization_receipt(
        receipt=receipt,
        decision=decision,
        session=session,
        lease=proposed_lease,
        prelease=prelease,
        health=health,
        manifest_version=policy.bootstrap.manifest_version,
        observed_main_sha=policy.bootstrap.current_main_sha,
    )
    if not verification.allowed:
        raise WriterPreparationDenied(tuple(code.value for code in verification.codes))
    return PreparedWriterAuthorization(decision, receipt, verification)


def verify_prepared_acquisition(
    *,
    prepared: PreparedWriterAuthorization,
    policy: WriterAuthorizationPolicy,
    session: SessionSnapshot,
    ack: BootstrapAckSnapshot,
    lease: LeaseSnapshot,
    prelease: PreLeaseRefresh,
    health: ControlPlaneHealthReport,
    now: datetime,
    overlapping_unexpired_lease_ids: Sequence[str],
) -> ReceiptVerification:
    """Re-evaluate at an acquisition boundary without granting any lease.

    The fresh broker decision proves the writer is still coordination-eligible.
    The persisted receipt remains bound to the *original* decision that issued it;
    using the freshly evaluated decision for receipt verification would silently
    discard the original ``authorization_evaluated_at`` binding because the v1
    decision digest intentionally does not contain that timestamp.

    Changing receipt-bound refresh/health/scope/main/intent evidence therefore
    requires a new preparation. Expired issuance windows are never extended
    silently. This check is not an atomic compare-and-set and cannot remove TOCTOU
    races in the provider adapter.
    """

    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise WriterPreparationDenied(("TIMEZONE_REQUIRED",))
    if not (prepared.receipt.issued_at <= now <= prepared.receipt.expires_at):
        raise WriterPreparationDenied(("RECEIPT_NOT_CURRENT",))
    if lease.acquired_at > now:
        raise WriterPreparationDenied(("ACQUISITION_IN_FUTURE",))
    if prelease.lease_scan_at > now or now - prelease.lease_scan_at > policy.bootstrap.max_prelease_scan_age:
        raise WriterPreparationDenied(("PRELEASE_REFRESH_NOT_CURRENT",))

    current = authorize_writer(
        policy=policy,
        session=session,
        ack=ack,
        proposed_lease=lease,
        prelease=prelease,
        health=health,
        now=now,
        overlapping_unexpired_lease_ids=overlapping_unexpired_lease_ids,
        intent=prepared.decision.intent,
        repair_plan_id=prepared.decision.repair_plan_id,
    )
    if not current.coordination_allowed:
        raise WriterPreparationDenied(tuple(code.value for code in current.codes))

    require_valid_receipt_payload(prepared.receipt.event_payload())
    _integrity_or_denied(prepared.receipt, decision=prepared.decision)
    verification = verify_writer_authorization_receipt(
        receipt=prepared.receipt,
        decision=prepared.decision,
        session=session,
        lease=lease,
        prelease=prelease,
        health=health,
        manifest_version=policy.bootstrap.manifest_version,
        observed_main_sha=policy.bootstrap.current_main_sha,
    )
    if not verification.allowed:
        raise WriterPreparationDenied(tuple(code.value for code in verification.codes))
    return verification
