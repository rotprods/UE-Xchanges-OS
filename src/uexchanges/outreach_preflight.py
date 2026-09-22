"""UEX offline preflight candidate. Standard library only; NEVER sends or submits.

Integration must supply trusted, exact-ID, freshly reconciled facts and consume a
real writer authorization/atomic outbox reservation at the actual provider boundary.
A passing result here is NOT that authorization. No global concurrency guarantees.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from hashlib import sha1, sha256
from html import escape
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping, Sequence

PINNED_SIGNATURE_BLOB = "0a7a4ea118770f605896ad500eb7fe41e6b84fb8"
PINNED_FRAGMENT_SHA256 = "fca50f16aa68337100412a40506852817b5162b7d111cc12be20f84fa1c021dc"
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,180}$")
MAIL = re.compile(r"^[^\s@<>\r\n,;]+@[^\s@<>\r\n,;]+\.[^\s@<>\r\n,;]+$")

class Route(str, Enum):
    EMAIL = "EMAIL"
    FORM_REQUIRED = "FORM_REQUIRED"
    EMAIL_THEN_FORM = "EMAIL_THEN_FORM"
    UNKNOWN = "UNKNOWN"

class Intent(str, Enum):
    APPLICATION = "APPLICATION"
    FOLLOWUP = "FOLLOWUP"
    REQUESTED_REPLY = "REQUESTED_REPLY"

@dataclass(frozen=True)
class Contact:
    organization_id: str
    call_id: str
    application_id: str
    intent: Intent
    occurred_at: datetime
    outcome: str  # SENT, RESERVED, OUTCOME_UNKNOWN, VERIFIED_NOT_SENT

@dataclass(frozen=True)
class Candidate:
    organization_id: str
    call_id: str
    application_id: str
    recipient: str
    subject: str
    body: str
    route: Route
    route_evidence_ref: str
    eligibility_verified: bool
    project_state: str
    country_iso: str
    intent: Intent = Intent.APPLICATION
    requested_reply_message_id: str = ""
    # Explicit organiser authorship restrictions, not an imagined default.
    human_original_required: bool = False
    human_original_evidence_ref: str = ""

@dataclass(frozen=True)
class Preflight:
    preparation_ok: bool
    blockers: tuple[str, ...]
    send_authorized: bool = False  # Always false: broker is external to this candidate.


def aware(value: datetime) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def add_business_days(value: datetime, days: int) -> datetime:
    """Weekends only. No holiday-calendar claim is made."""
    while days:
        value += timedelta(days=1)
        if value.weekday() < 5:
            days -= 1
    return value


def load_signature(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    digest = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if digest != PINNED_SIGNATURE_BLOB:
        raise ValueError("OUTREACH_SIGNATURE_GATE_FAIL: canonical source mismatch")
    source = raw.decode("utf-8")
    fragment = source.split('    <div id="signature">\n', 1)[1].split(
        '\n    </div>\n  </div>\n  <script>', 1)[0] + '\n'
    if sha256(fragment.encode()).hexdigest() != PINNED_FRAGMENT_SHA256:
        raise ValueError("OUTREACH_SIGNATURE_GATE_FAIL: fragment mismatch")
    return fragment


def render_email(body: str, signature: str) -> str:
    """Escape candidate prose and append the pinned fragment ONCE at the end.

    This creates an inert HTML preparation. The display-page toolbar/script is NOT sent.
    Verify actual delivered MIME separately when integrating a provider adapter.
    """
    if sha256(signature.encode()).hexdigest() != PINNED_FRAGMENT_SHA256:
        raise ValueError("OUTREACH_SIGNATURE_GATE_FAIL")
    paragraphs = ''.join('<p>' + escape(p).replace('\n', '<br>') + '</p>'
                         for p in body.strip().split('\n\n') if p.strip())
    return paragraphs + '\n' + signature


def preflight(c: Candidate, history: Sequence[Contact], *, now: datetime,
              history_observed_at: datetime, history_complete: bool,
              signature: str, excluded_countries: frozenset[str] = frozenset(),
              history_ttl_seconds: int = 300) -> Preflight:
    errors: list[str] = []
    def fail(code: str) -> None:
        if code not in errors:
            errors.append(code)
    if not all(isinstance(x, str) and ID.fullmatch(x)
               for x in (c.organization_id, c.call_id, c.application_id)):
        fail("EXACT_ID_BINDING_REQUIRED")
    if not MAIL.fullmatch(c.recipient):
        fail("SINGLE_VERIFIED_RECIPIENT_REQUIRED")
    if '\r' in c.subject or '\n' in c.subject:
        fail("HEADER_INJECTION")
    if not c.subject.strip() or not c.body.strip():
        fail("EMPTY_MESSAGE")
    if not aware(now) or not aware(history_observed_at):
        fail("TIMEZONE_REQUIRED")
    elif not 0 <= (now - history_observed_at).total_seconds() <= history_ttl_seconds:
        fail("HISTORY_STALE_OR_FUTURE")
    if not history_complete:
        fail("CROSS_THREAD_ORGANIZATION_HISTORY_REQUIRED")
    if sha256(signature.encode()).hexdigest() != PINNED_FRAGMENT_SHA256:
        fail("OUTREACH_SIGNATURE_GATE_FAIL")
    if not isinstance(c.intent, Intent):
        fail("UNKNOWN_INTENT")
    if not isinstance(c.route, Route) or c.route == Route.UNKNOWN or not c.route_evidence_ref.strip():
        fail("APPLICATION_ROUTE_UNVERIFIED")
    if not c.country_iso or not re.fullmatch(r"[A-Z]{2}", c.country_iso):
        fail("COUNTRY_UNVERIFIED")
    if c.country_iso in excluded_countries:
        fail("USER_DESTINATION_EXCLUDED")
    requested = c.intent == Intent.REQUESTED_REPLY
    if c.project_state.upper() == "NO_CONTACT":
        fail("NO_CONTACT_REQUIRES_SEPARATE_CONSENT_RESET")
    if requested and not c.requested_reply_message_id.strip():
        fail("INBOUND_REQUEST_EVIDENCE_REQUIRED")
    terminal = {"WITHDRAWN", "CLOSED", "REJECTED", "DECLINED", "NO_CONTACT", "SELECTED", "CONFIRMED", "COMPLETED"}
    known_states = terminal | {"OPEN", "EMAIL_ROUTE_AVAILABLE", "FORM_PENDING", "WAITLIST", "WAITING_SELECTION"}
    if c.project_state.upper() not in known_states:
        fail("PROJECT_STATE_UNRECOGNIZED")
    if c.project_state.upper() in terminal and not requested:
        fail("NO_UNSOLICITED_CONTACT_IN_TERMINAL_STATE")
    if c.project_state.upper() in {"WAITLIST", "WAITING_SELECTION"} and not requested:
        fail("WAIT_WITHOUT_CHASING")
    if c.intent == Intent.APPLICATION:
        if not c.eligibility_verified:
            fail("ELIGIBILITY_NOT_VERIFIED")
        if c.route == Route.FORM_REQUIRED:
            fail("REQUIRED_FORM_NOT_REPLACED_BY_EMAIL")
    if c.human_original_required and not c.human_original_evidence_ref.strip():
        fail("EXPLICIT_AUTHORSHIP_REQUIREMENT")
    text = unicodedata.normalize("NFKC", c.subject + '\n' + c.body).casefold()
    # Conservative lint, not an AI detector. Technical AI experience remains valid.
    disclosure_phrases = ("ai-assisted editing", "rule on ai", "rules on ai", "ai policy",
                          "my ai agent", "using tinyfish", "uso de ia para", "política de ia",
                          "politica de ia", "norma sobre ia", "mi agente de ia", "utilizo tinyfish",
                          "runtimegraph", "writerauthorization", "not a claim that", "human frontier")
    if any(s in text for s in disclosure_phrases):
        fail("UNSOLICITED_INTERNAL_PROCESS_PROSE")
    max_words = 80 if c.intent == Intent.FOLLOWUP else 200
    if len(c.body.split()) > max_words:
        fail("MESSAGE_TOO_LONG")
    if c.body.count('?') > 1:
        fail("MULTIPLE_QUESTIONS_REVIEW")
    same = []
    for old in history:
        if old.organization_id != c.organization_id:
            continue
        if not aware(old.occurred_at):
            fail("HISTORY_TIMESTAMP_INVALID")
            continue
        if aware(now) and old.occurred_at > now:
            fail("HISTORY_TIMESTAMP_INVALID")
        if old.call_id == c.call_id or old.application_id == c.application_id:
            same.append(old)
        if old.outcome not in {"SENT", "RESERVED", "OUTCOME_UNKNOWN", "VERIFIED_NOT_SENT"}:
            fail("HISTORY_OUTCOME_UNRECOGNIZED")
        # Any ambiguous attempt to this organisation requires reconciliation first.
        if old.outcome in {"RESERVED", "OUTCOME_UNKNOWN"}:
            fail("RECONCILE_PRIOR_EFFECT_BEFORE_CONTACT")
        if not requested and old.outcome == "SENT" and aware(now) and old.occurred_at <= now:
            if now - old.occurred_at < timedelta(hours=24):
                fail("ORGANIZATION_24H_COOLDOWN")
    sent = [x for x in same if x.outcome == "SENT"]
    if c.intent == Intent.APPLICATION and any(x.intent == Intent.APPLICATION for x in sent):
        fail("DUPLICATE_CANDIDATURE_ACROSS_THREADS")
    if c.intent == Intent.FOLLOWUP:
        applications = [x for x in sent if x.intent == Intent.APPLICATION]
        if not applications:
            fail("NO_INITIAL_APPLICATION_EVIDENCE")
        if any(x.intent == Intent.FOLLOWUP for x in sent):
            fail("FOLLOWUP_BUDGET_EXHAUSTED")
        if applications and aware(now) and now < add_business_days(max(x.occurred_at for x in applications), 5):
            fail("FIVE_BUSINESS_DAY_COOLDOWN")
    return Preflight(not errors, tuple(errors))


def validate_receipt_structure(value: Any, application_id: str) -> bool:
    """Validate structure of a receipt normalized by a TRUSTED evidence adapter.

    This does not itself authenticate a provider or make arbitrary prose authoritative.
    Sending/receipt/selection evidence are deliberately different states.
    """
    if not isinstance(value, Mapping):
        return False
    if value.get('kind') not in {"FORM_SUBMITTED", "EMAIL_APPLICATION_SENT"}:
        return False
    if value.get('application_id') != application_id or value.get('adapter_verified') is not True:
        return False
    required = ("receipt_id", "provider_object_id", "evidence_ref", "captured_at", "submission_identity")
    if any(not isinstance(value.get(k), str) or not value[k].strip() for k in required):
        return False
    if not ID.fullmatch(value['receipt_id']):
        return False
    try:
        stamp = datetime.fromisoformat(value['captured_at'].replace('Z', '+00:00'))
    except ValueError:
        return False
    return aware(stamp)


def form_preflight(*, provider: str, required_fields: Sequence[str],
                   values: Mapping[str, Any], allowed_organizations: Sequence[str],
                   organization: str, steps: int, unchanged_steps: int) -> tuple[str, ...]:
    """Read-only bounded form plan; never selects a false sending organisation."""
    errors = []
    if provider != "TinyFish":
        errors.append("USE_TINYFISH")
    if organization not in allowed_organizations:
        errors.append("SENDING_ORGANIZATION_OPTION_MISMATCH")
    if steps >= 40 or unchanged_steps >= 3:
        errors.append("STOP_NO_PROGRESS_OR_BUDGET")
    for field in required_fields:
        # False is a valid confirmed answer. None/blank is not; never infer it.
        if field not in values or values[field] is None or (isinstance(values[field], str) and not values[field].strip()):
            errors.append("MISSING_REQUIRED:" + field)
    return tuple(errors)
