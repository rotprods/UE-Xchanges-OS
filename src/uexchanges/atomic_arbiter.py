"""Pure contract helpers for the UE-Xchanges atomic coordination arbiter.

The PostgreSQL implementation lives in ``sql/atomic_arbiter_v1.sql``.  This module
contains only deterministic identities and state-transition guards so callers can
construct requests without requiring a database driver.

External effect identity is operational, not payload-derived: editing prose or
refreshing an infopack must never create permission for a second initial send.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable
from urllib.parse import quote


_SCOPE_SEPARATOR = "\x1f"


class ArbiterContractError(ValueError):
    """Raised when a request violates an anti-collision contract."""


class LeaseState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class ExternalEffectState(str, Enum):
    RESERVED = "RESERVED"
    STARTED = "STARTED"
    CONFIRMED = "CONFIRMED"
    FAILED_NO_EFFECT = "FAILED_NO_EFFECT"
    UNCERTAIN = "UNCERTAIN"
    CANCELLED_BEFORE_START = "CANCELLED_BEFORE_START"


class ExternalEffectType(str, Enum):
    EMAIL_INITIAL = "EMAIL_INITIAL"
    EMAIL_FOLLOWUP = "EMAIL_FOLLOWUP"
    EMAIL_REPLY = "EMAIL_REPLY"
    FORM_INITIAL = "FORM_INITIAL"
    FORM_RESUBMISSION = "FORM_RESUBMISSION"


@dataclass(frozen=True)
class ScopeSet:
    scopes: tuple[str, ...]
    sha256: str


@dataclass(frozen=True)
class Fence:
    lease_id: str
    session_id: str
    fencing_token: int

    def __post_init__(self) -> None:
        if not self.lease_id.strip() or not self.session_id.strip():
            raise ArbiterContractError("lease_id and session_id are required")
        if self.fencing_token < 1:
            raise ArbiterContractError("fencing_token must be positive")


def _component(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArbiterContractError(f"{name} must be a non-empty string")
    if any(ord(ch) < 32 for ch in value):
        raise ArbiterContractError(f"{name} contains a control character")
    return quote(value.strip(), safe="-._~")


def canonical_scope_set(scopes: Iterable[str]) -> tuple[str, ...]:
    """Return a deterministic scope tuple and reject blanks/duplicates.

    Sorting is mandatory so independent agents acquire advisory locks in the same
    order.  A duplicate is rejected instead of silently collapsed because a caller
    should know the exact set it is asking to fence.
    """
    if isinstance(scopes, (str, bytes)):
        raise ArbiterContractError("scopes must be an iterable of scope strings")
    raw = tuple(scopes)
    if not raw:
        raise ArbiterContractError("at least one scope is required")
    cleaned: list[str] = []
    for scope in raw:
        if not isinstance(scope, str) or not scope.strip():
            raise ArbiterContractError("scope values must be non-empty strings")
        value = scope.strip()
        if any(ord(ch) < 32 for ch in value):
            raise ArbiterContractError("scope contains a control character")
        cleaned.append(value)
    if len(set(cleaned)) != len(cleaned):
        raise ArbiterContractError("scope set contains duplicates")
    return tuple(sorted(cleaned))


def scope_set_hash(scopes: Iterable[str]) -> str:
    """Hash scopes identically to the PostgreSQL arbiter (ASCII unit separator)."""
    canonical = canonical_scope_set(scopes)
    return sha256(_SCOPE_SEPARATOR.join(canonical).encode("utf-8")).hexdigest()


def build_scope_set(scopes: Iterable[str]) -> ScopeSet:
    canonical = canonical_scope_set(scopes)
    return ScopeSet(canonical, sha256(_SCOPE_SEPARATOR.join(canonical).encode()).hexdigest())


def application_scope(application_id: str) -> str:
    return f"APPLICATION:{_component(application_id, 'application_id')}"


def organisation_call_scope(organisation_id: str, call_id: str) -> str:
    return (
        f"ORGCALL:{_component(organisation_id, 'organisation_id')}:"
        f"{_component(call_id, 'call_id')}"
    )


def initial_email_effect_key(application_id: str) -> str:
    return f"v1:EMAIL_INITIAL:{_component(application_id, 'application_id')}"


def initial_form_effect_key(application_id: str, form_id: str) -> str:
    return (
        f"v1:FORM_INITIAL:{_component(application_id, 'application_id')}:"
        f"{_component(form_id, 'form_id')}"
    )


def followup_email_effect_key(application_id: str, followup_number: int) -> str:
    if not isinstance(followup_number, int) or isinstance(followup_number, bool) or followup_number < 1:
        raise ArbiterContractError("followup_number must be a positive integer")
    return (
        f"v1:EMAIL_FOLLOWUP:{_component(application_id, 'application_id')}:"
        f"{followup_number}"
    )


def reply_email_effect_key(thread_id: str, inbound_message_id: str, purpose: str) -> str:
    return (
        f"v1:EMAIL_REPLY:{_component(thread_id, 'thread_id')}:"
        f"{_component(inbound_message_id, 'inbound_message_id')}:"
        f"{_component(purpose, 'purpose')}"
    )


def authorised_resubmission_effect_key(
    application_id: str,
    form_id: str,
    provider_authorisation_ref: str,
) -> str:
    """Create a distinct resubmission key only from explicit provider authority.

    A changed answer/payload is deliberately insufficient to produce a new key.
    """
    auth_digest = sha256(
        _component(provider_authorisation_ref, "provider_authorisation_ref").encode("utf-8")
    ).hexdigest()[:24]
    return (
        f"v1:FORM_RESUBMISSION:{_component(application_id, 'application_id')}:"
        f"{_component(form_id, 'form_id')}:{auth_digest}"
    )


def can_reserve_effect(current: ExternalEffectState | None) -> bool:
    """Only absence or proven-no-effect/cancelled states permit another attempt."""
    return current is None or current in {
        ExternalEffectState.FAILED_NO_EFFECT,
        ExternalEffectState.CANCELLED_BEFORE_START,
    }


def require_effect_reservable(current: ExternalEffectState | None) -> None:
    if not can_reserve_effect(current):
        raise ArbiterContractError(f"effect is not reservable from {current.value}")


def validate_effect_transition(
    current: ExternalEffectState,
    target: ExternalEffectState,
) -> None:
    """Fail closed on every state transition not explicitly required by v1."""
    allowed: dict[ExternalEffectState, set[ExternalEffectState]] = {
        ExternalEffectState.RESERVED: {
            ExternalEffectState.STARTED,
            ExternalEffectState.CANCELLED_BEFORE_START,
        },
        ExternalEffectState.STARTED: {
            ExternalEffectState.CONFIRMED,
            ExternalEffectState.FAILED_NO_EFFECT,
            ExternalEffectState.UNCERTAIN,
        },
        ExternalEffectState.UNCERTAIN: {
            ExternalEffectState.CONFIRMED,
            ExternalEffectState.FAILED_NO_EFFECT,
        },
        ExternalEffectState.FAILED_NO_EFFECT: {ExternalEffectState.RESERVED},
        ExternalEffectState.CANCELLED_BEFORE_START: {ExternalEffectState.RESERVED},
        ExternalEffectState.CONFIRMED: set(),
    }
    if target not in allowed[current]:
        raise ArbiterContractError(f"invalid effect transition {current.value}->{target.value}")


def assert_current_fence(*, current_token: int, presented: Fence) -> None:
    """Reject a zombie worker carrying an older fencing token."""
    if current_token < 1:
        raise ArbiterContractError("current fencing token must be positive")
    if presented.fencing_token != current_token:
        raise ArbiterContractError("stale fencing token")
