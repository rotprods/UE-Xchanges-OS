"""Offline packet guard, not a provider adapter or authorization service.

Feed only facts from authenticated, exact-ID adapters. A dataclass, hash, or
adapter_verified flag is not evidence authenticity. No network/send/mutation API.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import re
from typing import Sequence
from .outreach_preflight import Candidate, Contact, Intent, Preflight, aware, preflight

@dataclass(frozen=True)
class Attachment:
    path: str
    sha256: str
    role: str  # CV, YOUTHPASS, PORTFOLIO; audit/private profile dumps excluded

@dataclass(frozen=True)
class InboundRequest:
    message_id: str
    organization_id: str
    call_id: str
    application_id: str
    sender: str
    received_at: datetime
    requested_action: bool
    resolved: bool = False

@dataclass(frozen=True)
class Timing:
    observed_at: datetime
    deadline: datetime | None = None
    late_permission_ref: str = ''

@dataclass(frozen=True)
class Packet:
    preparation_ok: bool
    blockers: tuple[str, ...]
    attachments: tuple[str, ...]
    send_authorized: bool = False


def prepare_packet(c: Candidate, history: Sequence[Contact], *, now: datetime,
                   history_observed_at: datetime, history_complete: bool,
                   signature: str, timing: Timing, attachment_root: Path,
                   attachments: Sequence[Attachment], inbound: InboundRequest | None = None,
                   excluded_countries: frozenset[str] = frozenset(),
                   source_ttl_seconds: int = 86400, max_bytes: int = 10_000_000) -> Packet:
    """Fail closed; validate actual files rather than a sentence saying 'attached'.

    Returned paths must be rechecked at provider invocation to avoid file replacement
    between preflight and send. Distributed single-writer/fencing remains external.
    A required form is not replaced by an email application. Unknown deadline is
    NOT invented; trusted current source evidence is still required.
    """
    base: Preflight = preflight(c, history, now=now, history_observed_at=history_observed_at,
        history_complete=history_complete, signature=signature, excluded_countries=excluded_countries)
    errors = list(base.blockers)
    if not aware(now) or not aware(timing.observed_at):
        errors.append('SOURCE_TIMEZONE_REQUIRED')
    elif not 0 <= (now-timing.observed_at).total_seconds() <= source_ttl_seconds:
        errors.append('SOURCE_STALE_OR_FUTURE')
    if timing.deadline is not None:
        if not aware(timing.deadline):
            errors.append('DEADLINE_TIMEZONE_REQUIRED')
        elif c.intent == Intent.APPLICATION and aware(now) and now >= timing.deadline and not timing.late_permission_ref.strip():
            errors.append('DEADLINE_PASSED_NO_EXPLICIT_LATE_PERMISSION')
    if c.intent == Intent.REQUESTED_REPLY:
        exact = inbound is not None and (
            inbound.message_id == c.requested_reply_message_id and
            inbound.organization_id == c.organization_id and inbound.call_id == c.call_id and
            inbound.application_id == c.application_id and
            inbound.sender.casefold() == c.recipient.casefold() and
            inbound.requested_action is True and inbound.resolved is False)
        if not exact:
            errors.append('INBOUND_REQUEST_EXACT_BINDING_REQUIRED')
        elif not aware(inbound.received_at) or (aware(now) and inbound.received_at > now):
            errors.append('INBOUND_TIMESTAMP_INVALID')
    root = attachment_root.resolve()
    valid = []
    cv_valid = False
    seen = set()
    total = 0
    for a in attachments:
        if a.role not in {'CV','YOUTHPASS','PORTFOLIO'}:
            errors.append('ATTACHMENT_ROLE_NOT_FOR_ORGANISER'); continue
        try:
            path = Path(a.path).resolve(strict=True)
            if not path.is_relative_to(root) or Path(a.path).is_symlink():
                errors.append('ATTACHMENT_OUTSIDE_APPROVED_ROOT'); continue
            if path in seen:
                errors.append('DUPLICATE_ATTACHMENT'); continue
            seen.add(path)
            if path.stat().st_size > max_bytes:
                errors.append('ATTACHMENT_SIZE_LIMIT'); continue
            data = path.read_bytes()
        except (OSError, ValueError):
            errors.append('ATTACHMENT_NOT_READABLE'); continue
        total += len(data)
        if total > max_bytes:
            errors.append('ATTACHMENT_SIZE_LIMIT'); continue
        if path.suffix.lower() != '.pdf' or not data.startswith(b'%PDF-'):
            errors.append('ATTACHMENT_NOT_PDF'); continue
        if not re.fullmatch(r'[0-9a-f]{64}', a.sha256) or sha256(data).hexdigest() != a.sha256:
            errors.append('ATTACHMENT_DIGEST_MISMATCH'); continue
        valid.append(str(path))
        cv_valid |= a.role == 'CV'
    if c.intent == Intent.APPLICATION and not cv_valid:
        errors.append('INITIAL_CANDIDATURE_CV_REQUIRED')
    # A PDF header alone does not certify a safe/valid PDF or substantiate its claims.
    errors = list(dict.fromkeys(errors))
    return Packet(not errors, tuple(errors), tuple(valid), send_authorized=False)
