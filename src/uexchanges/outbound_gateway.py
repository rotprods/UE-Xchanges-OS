"""Fenced at-most-once email effect gateway.

This module coordinates an outbound provider call but does not contain Gmail
credentials or a provider implementation. WriterAuthorization and external-email
capability authenticity are verified by injected trusted verifiers.

Safety rule: an unknown provider outcome is sticky. It must be reconciled before
another reservation can be created for the same exact effect key.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from enum import Enum
from hashlib import sha256
import json
import re
from threading import Lock
from typing import Callable, Protocol

HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,180}$")
MAIL = re.compile(r"^[^\s@<>\r\n,;]+@[^\s@<>\r\n,;]+\.[^\s@<>\r\n,;]+$")


class EffectState(str, Enum):
    NOT_SENT = "NOT_SENT"
    RESERVED = "RESERVED"
    SEND_IN_PROGRESS = "SEND_IN_PROGRESS"
    SEND_CONFIRMED = "SEND_CONFIRMED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    DELIVERY_FAILED = "DELIVERY_FAILED"


class ProviderDisposition(str, Enum):
    CONFIRMED = "CONFIRMED"
    DEFINITE_FAILURE = "DEFINITE_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EffectKey:
    organization_id: str
    call_id: str
    application_id: str
    intent: str
    authoritative_source_version: str

    def digest(self) -> str:
        raw = "|".join((self.organization_id, self.call_id, self.application_id,
                        self.intent, self.authoritative_source_version))
        return sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class AttachmentExpectation:
    filename: str
    sha256: str


@dataclass(frozen=True)
class PreparedEmail:
    key: EffectKey
    sender: str
    recipient: str
    subject: str
    html_body: str
    text_body: str
    signature_marker: str
    attachments: tuple[AttachmentExpectation, ...] = ()
    preflight_ref: str = ""
    preflight_allowed: bool = False

    def digest(self) -> str:
        obj = {
            "effect_key": self.key.digest(), "sender": self.sender, "recipient": self.recipient,
            "subject": self.subject, "html_sha256": sha256(self.html_body.encode()).hexdigest(),
            "text_sha256": sha256(self.text_body.encode()).hexdigest(),
            "attachments": [(a.filename, a.sha256) for a in self.attachments],
            "preflight_ref": self.preflight_ref,
        }
        return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class WriterFence:
    session_id: str
    agent_id: str
    writer_authorization_receipt_id: str
    writer_authorization_digest: str
    lease_id: str
    lease_expires_at: datetime
    observed_main_sha: str
    coordination_allowed: bool


@dataclass(frozen=True)
class EmailCapability:
    capability_id: str
    session_id: str
    action: str
    expires_at: datetime
    provider_connection_ref: str


@dataclass(frozen=True)
class ProviderResult:
    disposition: ProviderDisposition
    provider_message_id: str = ""
    provider_thread_id: str = ""
    raw_mime: bytes = b""
    error_ref: str = ""


@dataclass(frozen=True)
class EffectRecord:
    key_digest: str
    packet_digest: str
    state: EffectState
    generation: int
    fence_lease_id: str
    reserved_at: datetime
    provider_message_id: str = ""
    provider_thread_id: str = ""
    reconciliation_ref: str = ""


@dataclass(frozen=True)
class GatewayResult:
    state: EffectState
    key_digest: str
    generation: int
    provider_message_id: str = ""
    provider_thread_id: str = ""
    reason: str = ""


class EffectBlocked(RuntimeError):
    pass


class UnknownProviderOutcome(RuntimeError):
    pass


class DefiniteProviderFailure(RuntimeError):
    pass


class Outbox(Protocol):
    def reserve(self, key: EffectKey, packet_digest: str, lease_id: str, now: datetime) -> EffectRecord: ...
    def begin(self, key_digest: str, lease_id: str) -> EffectRecord: ...
    def finish(self, key_digest: str, state: EffectState, *, message_id: str = "", thread_id: str = "", ref: str = "") -> EffectRecord: ...
    def get(self, key_digest: str) -> EffectRecord | None: ...
    def reconcile_not_sent(self, key_digest: str, ref: str) -> EffectRecord: ...


def aware(x: datetime) -> bool:
    return isinstance(x, datetime) and x.tzinfo is not None and x.utcoffset() is not None


class InMemoryOutbox:
    """Reference atomic store for tests/local use; production must use durable CAS/transaction."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[str, EffectRecord] = {}

    def reserve(self, key: EffectKey, packet_digest: str, lease_id: str, now: datetime) -> EffectRecord:
        kd = key.digest()
        with self._lock:
            old = self._rows.get(kd)
            if old and old.state is not EffectState.NOT_SENT:
                raise EffectBlocked(f"EXISTING_EFFECT:{old.state.value}")
            gen = 1 if old is None else old.generation + 1
            row = EffectRecord(kd, packet_digest, EffectState.RESERVED, gen, lease_id, now)
            self._rows[kd] = row
            return row

    def begin(self, key_digest: str, lease_id: str) -> EffectRecord:
        with self._lock:
            old = self._rows.get(key_digest)
            if old is None or old.state is not EffectState.RESERVED:
                raise EffectBlocked("RESERVATION_REQUIRED")
            if old.fence_lease_id != lease_id:
                raise EffectBlocked("FENCE_TOKEN_MISMATCH")
            row = replace(old, state=EffectState.SEND_IN_PROGRESS)
            self._rows[key_digest] = row
            return row

    def finish(self, key_digest: str, state: EffectState, *, message_id: str = "", thread_id: str = "", ref: str = "") -> EffectRecord:
        if state not in {EffectState.SEND_CONFIRMED, EffectState.OUTCOME_UNKNOWN, EffectState.DELIVERY_FAILED}:
            raise ValueError("invalid finish state")
        with self._lock:
            old = self._rows.get(key_digest)
            if old is None or old.state is not EffectState.SEND_IN_PROGRESS:
                raise EffectBlocked("SEND_IN_PROGRESS_REQUIRED")
            row = replace(old, state=state, provider_message_id=message_id,
                          provider_thread_id=thread_id, reconciliation_ref=ref)
            self._rows[key_digest] = row
            return row

    def get(self, key_digest: str) -> EffectRecord | None:
        with self._lock:
            return self._rows.get(key_digest)

    def reconcile_not_sent(self, key_digest: str, ref: str) -> EffectRecord:
        if not ref.strip():
            raise ValueError("authoritative reconciliation ref required")
        with self._lock:
            old = self._rows.get(key_digest)
            if old is None or old.state not in {EffectState.OUTCOME_UNKNOWN, EffectState.DELIVERY_FAILED}:
                raise EffectBlocked("RECONCILIATION_NOT_APPLICABLE")
            row = replace(old, state=EffectState.NOT_SENT, reconciliation_ref=ref)
            self._rows[key_digest] = row
            return row


def _validate_ids(key: EffectKey) -> None:
    if not all(ID.fullmatch(x or "") for x in (key.organization_id, key.call_id, key.application_id, key.intent)):
        raise EffectBlocked("EXACT_ID_BINDING_REQUIRED")
    if not key.authoritative_source_version.strip():
        raise EffectBlocked("AUTHORITATIVE_SOURCE_VERSION_REQUIRED")


def validate_prepared(email: PreparedEmail) -> None:
    _validate_ids(email.key)
    if not MAIL.fullmatch(email.sender) or not MAIL.fullmatch(email.recipient):
        raise EffectBlocked("SINGLE_VERIFIED_ADDRESS_REQUIRED")
    if "\r" in email.subject or "\n" in email.subject or not email.subject.strip():
        raise EffectBlocked("INVALID_SUBJECT")
    if not email.preflight_allowed or not email.preflight_ref.strip():
        raise EffectBlocked("PREPARED_PREFLIGHT_REQUIRED")
    if not email.text_body.strip() or not email.html_body.strip():
        raise EffectBlocked("BODY_REQUIRED")
    if not email.signature_marker or email.html_body.count(email.signature_marker) != 1:
        raise EffectBlocked("SIGNATURE_EXACTLY_ONCE_REQUIRED")
    seen = set()
    for a in email.attachments:
        if not a.filename.strip() or a.filename in seen or not HEX64.fullmatch(a.sha256):
            raise EffectBlocked("ATTACHMENT_MANIFEST_INVALID")
        seen.add(a.filename)


def validate_fence(fence: WriterFence, *, now: datetime, current_main_sha: str) -> None:
    if not aware(now) or not aware(fence.lease_expires_at):
        raise EffectBlocked("TIMEZONE_REQUIRED")
    if not fence.coordination_allowed:
        raise EffectBlocked("WRITER_AUTHORIZATION_DENIED")
    if now >= fence.lease_expires_at:
        raise EffectBlocked("LEASE_EXPIRED")
    if fence.observed_main_sha != current_main_sha:
        raise EffectBlocked("MAIN_DRIFT")
    if not all(x.strip() for x in (fence.session_id, fence.agent_id, fence.writer_authorization_receipt_id,
                                    fence.writer_authorization_digest, fence.lease_id)):
        raise EffectBlocked("WRITER_FENCE_INCOMPLETE")


def validate_capability(cap: EmailCapability, *, session_id: str, now: datetime) -> None:
    if not aware(cap.expires_at) or not aware(now) or now >= cap.expires_at:
        raise EffectBlocked("EMAIL_CAPABILITY_EXPIRED")
    if cap.session_id != session_id or cap.action != "EMAIL_SEND":
        raise EffectBlocked("EMAIL_CAPABILITY_SCOPE_MISMATCH")
    if not cap.capability_id.strip() or not cap.provider_connection_ref.strip():
        raise EffectBlocked("EMAIL_CAPABILITY_INCOMPLETE")


def validate_delivered_mime(raw: bytes, prepared: PreparedEmail) -> None:
    if not raw:
        raise EffectBlocked("DELIVERED_MIME_REQUIRED")
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    senders = [a for _, a in getaddresses(msg.get_all("from", []))]
    recipients = [a for _, a in getaddresses(msg.get_all("to", []))]
    cc = [a for _, a in getaddresses(msg.get_all("cc", []))]
    bcc = [a for _, a in getaddresses(msg.get_all("bcc", []))]
    if (senders != [prepared.sender] or recipients != [prepared.recipient] or cc or bcc
            or str(msg.get("subject", "")) != prepared.subject):
        raise EffectBlocked("DELIVERED_HEADERS_MISMATCH")
    html_parts = []
    plain_parts = []
    attachments = {}
    duplicate_attachment_name = False
    for part in msg.walk():
        if part.is_multipart():
            continue
        disp = part.get_content_disposition()
        if disp == "attachment":
            name = part.get_filename() or ""
            if name in attachments:
                duplicate_attachment_name = True
            attachments[name] = sha256(part.get_payload(decode=True) or b"").hexdigest()
        elif part.get_content_type() == "text/html":
            html_parts.append(part.get_content())
        elif part.get_content_type() == "text/plain":
            plain_parts.append(part.get_content())
    if sum(x.count(prepared.signature_marker) for x in html_parts) != 1:
        raise EffectBlocked("DELIVERED_SIGNATURE_MISMATCH")
    if not any(x.strip() for x in plain_parts):
        raise EffectBlocked("DELIVERED_TEXT_FALLBACK_MISSING")
    expected = {a.filename: a.sha256 for a in prepared.attachments}
    if duplicate_attachment_name or attachments != expected:
        raise EffectBlocked("DELIVERED_ATTACHMENTS_MISMATCH")


def send_once(
    *, outbox: Outbox, prepared: PreparedEmail, fence: WriterFence, capability: EmailCapability,
    now: datetime, current_main_sha: str,
    writer_fence_verifier: Callable[[WriterFence], bool],
    email_capability_verifier: Callable[[EmailCapability], bool],
    provider_send: Callable[[PreparedEmail, str], ProviderResult],
) -> GatewayResult:
    """Invoke the provider at most once for one successful reservation.

    The injected verifiers are the trust boundary. Local dataclasses/booleans are
    not proof of WriterAuthorization or an external connector grant.
    """
    validate_prepared(prepared)
    validate_fence(fence, now=now, current_main_sha=current_main_sha)
    validate_capability(capability, session_id=fence.session_id, now=now)
    if not writer_fence_verifier(fence):
        raise EffectBlocked("WRITER_FENCE_NOT_AUTHENTICATED")
    if not email_capability_verifier(capability):
        raise EffectBlocked("EMAIL_CAPABILITY_NOT_AUTHENTICATED")

    row = outbox.reserve(prepared.key, prepared.digest(), fence.lease_id, now)
    row = outbox.begin(row.key_digest, fence.lease_id)
    try:
        result = provider_send(prepared, f"{row.key_digest}:{row.generation}")
    except DefiniteProviderFailure as exc:
        row = outbox.finish(row.key_digest, EffectState.DELIVERY_FAILED, ref=str(exc))
        return GatewayResult(row.state, row.key_digest, row.generation, reason=str(exc))
    except Exception as exc:
        row = outbox.finish(row.key_digest, EffectState.OUTCOME_UNKNOWN, ref=type(exc).__name__)
        return GatewayResult(row.state, row.key_digest, row.generation, reason=type(exc).__name__)

    if not isinstance(result, ProviderResult) or not isinstance(result.disposition, ProviderDisposition):
        row = outbox.finish(row.key_digest, EffectState.OUTCOME_UNKNOWN, ref="INVALID_PROVIDER_RESULT")
    elif result.disposition is ProviderDisposition.DEFINITE_FAILURE:
        row = outbox.finish(row.key_digest, EffectState.DELIVERY_FAILED, ref=result.error_ref)
    elif result.disposition is ProviderDisposition.UNKNOWN:
        row = outbox.finish(row.key_digest, EffectState.OUTCOME_UNKNOWN, ref=result.error_ref)
    else:
        try:
            if not result.provider_message_id.strip() or not result.provider_thread_id.strip():
                raise EffectBlocked("PROVIDER_IDS_REQUIRED")
            validate_delivered_mime(result.raw_mime, prepared)
        except Exception as exc:
            row = outbox.finish(row.key_digest, EffectState.OUTCOME_UNKNOWN,
                                message_id=result.provider_message_id, thread_id=result.provider_thread_id,
                                ref=f"MIME_RECONCILIATION:{type(exc).__name__}")
        else:
            row = outbox.finish(row.key_digest, EffectState.SEND_CONFIRMED,
                                message_id=result.provider_message_id, thread_id=result.provider_thread_id)
    return GatewayResult(row.state, row.key_digest, row.generation, row.provider_message_id,
                         row.provider_thread_id, row.reconciliation_ref)
