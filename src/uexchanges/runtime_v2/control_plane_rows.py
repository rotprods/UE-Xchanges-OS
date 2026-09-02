from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class StableRow:
    row_number: int
    entity_id: str
    values: tuple[Any, ...]


class StableRowError(RuntimeError):
    pass


class StableRowMissing(StableRowError):
    pass


class StableRowDuplicate(StableRowError):
    pass


class StableRowIdentityChanged(StableRowError):
    pass


def resolve_stable_row(
    rows: Sequence[Sequence[Any]],
    *,
    entity_id: str,
    id_column: int = 0,
    first_row_number: int = 1,
) -> StableRow:
    """Resolve one mutable control-plane row by stable entity ID.

    Physical row numbers are provider layout details and must never be cached across
    concurrent append writers.  Call this immediately before every mutable row
    update and fail closed if the ID is missing or duplicated.
    """
    if not entity_id.strip():
        raise ValueError("entity_id must be non-empty")
    if id_column < 0:
        raise ValueError("id_column must be >= 0")
    matches: list[StableRow] = []
    for offset, raw in enumerate(rows):
        if id_column >= len(raw):
            continue
        value = raw[id_column]
        if str(value or "").strip() == entity_id:
            matches.append(
                StableRow(
                    row_number=first_row_number + offset,
                    entity_id=entity_id,
                    values=tuple(raw),
                )
            )
    if not matches:
        raise StableRowMissing(f"stable row not found: {entity_id}")
    if len(matches) > 1:
        raise StableRowDuplicate(f"duplicate stable entity ID: {entity_id}")
    return matches[0]


def assert_row_identity(
    rows: Sequence[Sequence[Any]],
    *,
    row_number: int,
    expected_entity_id: str,
    id_column: int = 0,
    first_row_number: int = 1,
) -> None:
    """Compare-before-write guard for a row resolved immediately beforehand."""
    offset = row_number - first_row_number
    if offset < 0 or offset >= len(rows):
        raise StableRowIdentityChanged("resolved row is outside current observed bounds")
    raw = rows[offset]
    actual = str(raw[id_column] if id_column < len(raw) else "").strip()
    if actual != expected_entity_id:
        raise StableRowIdentityChanged(
            f"row identity changed before write: expected={expected_entity_id} actual={actual or '<blank>'}"
        )


def resolve_then_verify(
    read_rows: callable,
    *,
    entity_id: str,
    id_column: int = 0,
    first_row_number: int = 1,
) -> StableRow:
    """Provider-neutral two-read guard used by connector-backed writers.

    `read_rows` must perform a fresh provider read each time.  This intentionally
    costs one extra read at mutation boundaries to eliminate cached-index races.
    """
    first = tuple(tuple(row) for row in read_rows())
    resolved = resolve_stable_row(
        first,
        entity_id=entity_id,
        id_column=id_column,
        first_row_number=first_row_number,
    )
    second = tuple(tuple(row) for row in read_rows())
    fresh = resolve_stable_row(
        second,
        entity_id=entity_id,
        id_column=id_column,
        first_row_number=first_row_number,
    )
    if fresh.row_number != resolved.row_number:
        # Row movement is legitimate under concurrent append/insert.  The second
        # location is the only valid mutation target.
        return fresh
    assert_row_identity(
        second,
        row_number=fresh.row_number,
        expected_entity_id=entity_id,
        id_column=id_column,
        first_row_number=first_row_number,
    )
    return fresh
