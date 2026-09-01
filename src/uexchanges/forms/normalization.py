from __future__ import annotations

import math
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import FieldOwnership, FormField, FormFieldType


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _normalized_text(value: Any, *, trim: bool) -> str:
    if not isinstance(value, str):
        raise ValueError("text-like answers must be strings")
    normalized = _nfc(value.replace("\r\n", "\n").replace("\r", "\n"))
    return normalized.strip() if trim else normalized


def _normalized_number(value: Any) -> str:
    if isinstance(value, bool):
        raise ValueError("boolean is not a canonical number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("number answers must be finite")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, (int, float, str)):
        raw = str(value).strip()
        if not raw:
            raise ValueError("number answer must not be empty")
        try:
            number = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError("number answer is not a valid decimal") from exc
    else:
        raise ValueError("number answers must be int, float, Decimal or decimal string")
    if not number.is_finite():
        raise ValueError("number answers must be finite")
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


def _normalized_date(value: Any) -> str:
    if isinstance(value, datetime):
        raise ValueError("datetime is not a canonical date answer")
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str):
        raise ValueError("date answers must be date or ISO YYYY-MM-DD strings")
    raw = value.strip()
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("date answer must use ISO YYYY-MM-DD") from exc
    return parsed.isoformat()


def _normalized_checkbox(value: Any) -> bool | list[str]:
    if isinstance(value, bool):
        return value
    if not isinstance(value, (list, tuple, set, frozenset)):
        raise ValueError("checkbox answer must be boolean or a collection of option strings")
    normalized: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError("checkbox option answers must be strings")
        option = _normalized_text(item, trim=True)
        if not option:
            raise ValueError("checkbox option answers must be non-empty")
        normalized.add(option)
    return sorted(normalized)


def normalize_answer(field: FormField) -> Any:
    """Return the deterministic identity form of one model-visible answer.

    This function is for hashing/comparison identity, not for displaying or
    rewriting the user's answer. It never accepts a model-visible BLACK value.
    """
    if field.ownership is FieldOwnership.BLACK:
        if field.answer is not None:
            raise ValueError("BLACK answers must never enter canonical normalization")
        return None

    value = field.answer
    if value is None:
        return None

    if field.field_type in {FormFieldType.TEXT, FormFieldType.TEXTAREA}:
        return _normalized_text(value, trim=False)
    if field.field_type is FormFieldType.EMAIL:
        return _normalized_text(value, trim=True)
    if field.field_type is FormFieldType.NUMBER:
        return _normalized_number(value)
    if field.field_type is FormFieldType.DATE:
        return _normalized_date(value)
    if field.field_type in {FormFieldType.SELECT, FormFieldType.RADIO}:
        normalized = _normalized_text(value, trim=True)
        if not normalized:
            raise ValueError("choice answer must be non-empty")
        return normalized
    if field.field_type is FormFieldType.CHECKBOX:
        return _normalized_checkbox(value)
    if field.field_type is FormFieldType.CONSENT:
        if not isinstance(value, bool):
            raise ValueError("consent answer must be boolean")
        return value
    if field.field_type in {FormFieldType.FILE, FormFieldType.UNKNOWN}:
        raise ValueError(f"{field.field_type.value} answers are outside canonical model-visible payload identity")
    raise ValueError(f"unsupported form field type for canonical normalization: {field.field_type.value}")
