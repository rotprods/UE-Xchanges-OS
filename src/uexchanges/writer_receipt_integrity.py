"""Content-integrity checks for Writer Authorization Receipt v1.

This module is deliberately pure. It does not authorize a writer, acquire a lease,
mutate a provider, or grant domain/external capability. It closes two audit gaps:

- the content-addressed ``receipt_id`` must equal the canonical digest of every
  receipt claim except ``receipt_id`` itself;
- when the original WriterAuthorizationDecision is available, the receipt's
  ``authorization_evaluated_at`` must equal that decision's evaluation timestamp.

The existing full verifier still owns identity/scope/main/health/lease binding.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from .writer_authorization import WriterAuthorizationDecision
from .writer_authorization_receipt import WriterAuthorizationReceipt


class ReceiptIntegrityCode(str, Enum):
    RECEIPT_ID_MISMATCH = "RECEIPT_ID_MISMATCH"
    AUTHORIZATION_EVALUATED_AT_MISMATCH = "AUTHORIZATION_EVALUATED_AT_MISMATCH"


@dataclass(frozen=True)
class ReceiptIntegrityResult:
    allowed: bool
    codes: tuple[ReceiptIntegrityCode, ...]


class ReceiptIntegrityError(ValueError):
    """Value-safe integrity failure containing fixed reason codes only."""

    def __init__(self, codes: tuple[ReceiptIntegrityCode, ...]) -> None:
        self.codes = codes
        super().__init__("writer receipt integrity failure: " + ",".join(code.value for code in codes))


def canonical_receipt_claims(receipt: WriterAuthorizationReceipt) -> dict[str, object]:
    """Return the exact issuer claim set used to derive the content address."""

    claims = receipt.as_dict()
    claims.pop("receipt_id")
    return claims


def expected_receipt_id(receipt: WriterAuthorizationReceipt) -> str:
    encoded = json.dumps(
        canonical_receipt_claims(receipt),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "WAZ-" + hashlib.sha256(encoded).hexdigest()[:24]


def inspect_receipt_integrity(
    receipt: WriterAuthorizationReceipt,
    *,
    decision: WriterAuthorizationDecision | None = None,
) -> ReceiptIntegrityResult:
    codes: list[ReceiptIntegrityCode] = []
    if receipt.receipt_id != expected_receipt_id(receipt):
        codes.append(ReceiptIntegrityCode.RECEIPT_ID_MISMATCH)
    if decision is not None and receipt.authorization_evaluated_at != decision.evaluated_at:
        codes.append(ReceiptIntegrityCode.AUTHORIZATION_EVALUATED_AT_MISMATCH)
    final = tuple(codes)
    return ReceiptIntegrityResult(allowed=not final, codes=final)


def require_receipt_integrity(
    receipt: WriterAuthorizationReceipt,
    *,
    decision: WriterAuthorizationDecision | None = None,
) -> None:
    result = inspect_receipt_integrity(receipt, decision=decision)
    if not result.allowed:
        raise ReceiptIntegrityError(result.codes)
