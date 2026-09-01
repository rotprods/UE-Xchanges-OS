from __future__ import annotations

import hashlib
import json
from urllib.parse import urlsplit, urlunsplit

from .models import FormField


def canonicalize_form_url(url: str) -> str:
    """Remove fragments while preserving provider-significant query parameters."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("form URL must be absolute HTTP(S)")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def form_schema_fingerprint(*, provider: str, canonical_form_url: str, fields: tuple[FormField, ...]) -> str:
    """Hash structural form state only; answers/evidence never affect form identity."""
    if not provider.strip():
        raise ValueError("provider must be non-empty")
    payload = {
        "provider": provider.strip().lower(),
        "url": canonicalize_form_url(canonical_form_url),
        "fields": [
            {
                "field_key": field.field_key,
                "label": field.label,
                "field_type": field.field_type.value,
                "required": field.required,
                "options": list(field.options),
                "maxlength": field.maxlength,
            }
            for field in fields
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
