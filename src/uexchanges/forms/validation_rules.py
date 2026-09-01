from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .fingerprint import canonicalize_form_url


@dataclass(frozen=True)
class NativeConstraints:
    minlength: int | None = None
    maxlength: int | None = None
    pattern: str | None = None
    min_value: str | None = None
    max_value: str | None = None
    step: str | None = None
    multiple: bool = False
    accept: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name, value in (("minlength", self.minlength), ("maxlength", self.maxlength)):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if any(not item.strip() for item in self.accept):
            raise ValueError("accept entries must be non-empty")

    def as_payload(self) -> dict[str, Any]:
        return {
            "minlength": self.minlength,
            "maxlength": self.maxlength,
            "pattern": self.pattern,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "step": self.step,
            "multiple": self.multiple,
            "accept": list(self.accept),
        }


@dataclass(frozen=True)
class ValidationField:
    field_key: str
    label: str
    field_type: str
    required: bool
    options: tuple[str, ...] = field(default_factory=tuple)
    constraints: NativeConstraints = field(default_factory=NativeConstraints)

    def __post_init__(self) -> None:
        if not self.field_key.strip() or not self.label.strip() or not self.field_type.strip():
            raise ValueError("validation field key/label/type must be non-empty")

    def as_payload(self) -> dict[str, Any]:
        return {
            "field_key": self.field_key,
            "label": self.label,
            "field_type": self.field_type,
            "required": self.required,
            "options": list(self.options),
            "constraints": self.constraints.as_payload(),
        }


@dataclass(frozen=True)
class ValidationExpectation:
    provider: str
    canonical_form_url: str
    fields: tuple[ValidationField, ...]
    signature: str

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.canonical_form_url.strip() or not self.signature.strip():
            raise ValueError("validation expectation metadata must be non-empty")
        keys = [field.field_key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("validation expectation field keys must be unique")
        expected = validation_signature(
            provider=self.provider,
            canonical_form_url=self.canonical_form_url,
            fields=self.fields,
        )
        if expected != self.signature:
            raise ValueError("validation expectation signature does not match its snapshot")


def validation_signature(*, provider: str, canonical_form_url: str, fields: tuple[ValidationField, ...]) -> str:
    """Hash native validation semantics independently from answer payloads.

    This complements the existing structural form fingerprint. External browser
    promotion must eventually bind both values before prefill/approval/submit.
    """
    if not provider.strip():
        raise ValueError("provider must be non-empty")
    keys = [field.field_key for field in fields]
    if len(keys) != len(set(keys)):
        raise ValueError("validation field keys must be unique")
    payload = {
        "provider": provider.strip().lower(),
        "url": canonicalize_form_url(canonical_form_url),
        "fields": [field.as_payload() for field in fields],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
