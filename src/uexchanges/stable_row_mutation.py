"""Stable-ID, header-aware optimistic mutation planning.

Physical row/column positions are observations, never identity.  This module is
provider-agnostic and plan-only: it resolves a unique stable ID twice, compares
canonical row fingerprints, maps updates by header name against the second
snapshot, and verifies read-back after a provider performs the bounded write.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class StableRowErrorCode(str, Enum):
    TABLE_MISMATCH = "TABLE_MISMATCH"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    ID_HEADER_MISSING = "ID_HEADER_MISSING"
    STABLE_ID_NOT_FOUND = "STABLE_ID_NOT_FOUND"
    STABLE_ID_DUPLICATE = "STABLE_ID_DUPLICATE"
    UNKNOWN_UPDATE_HEADER = "UNKNOWN_UPDATE_HEADER"
    IMMUTABLE_STABLE_ID = "IMMUTABLE_STABLE_ID"
    EXPECTED_FINGERPRINT_MISMATCH = "EXPECTED_FINGERPRINT_MISMATCH"
    EXPECTED_OLD_VALUE_MISMATCH = "EXPECTED_OLD_VALUE_MISMATCH"
    CONCURRENT_ROW_CHANGE = "CONCURRENT_ROW_CHANGE"
    READBACK_MISMATCH = "READBACK_MISMATCH"
    UNSUPPORTED_CELL_VALUE = "UNSUPPORTED_CELL_VALUE"


class StableRowMutationError(ValueError):
    def __init__(self, code: StableRowErrorCode, detail: str):
        super().__init__(f"{code.value}: {detail}")
        self.code = code
        self.detail = detail


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _canonical_cell(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StableRowMutationError(
                StableRowErrorCode.UNSUPPORTED_CELL_VALUE,
                "non-finite floats cannot participate in mutation identity",
            )
        if value == 0:
            return 0.0
        return value
    raise StableRowMutationError(
        StableRowErrorCode.UNSUPPORTED_CELL_VALUE,
        f"unsupported cell value type: {type(value).__name__}",
    )


def _hash_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_row_map(headers: Sequence[str], values: Sequence[Any]) -> dict[str, Any]:
    if len(values) > len(headers):
        extras = values[len(headers) :]
        if any(item not in (None, "") for item in extras):
            raise StableRowMutationError(
                StableRowErrorCode.INVALID_SCHEMA,
                "row contains non-empty cells beyond the declared header width",
            )
    padded = list(values[: len(headers)]) + [None] * max(0, len(headers) - len(values))
    return {header: _canonical_cell(padded[index]) for index, header in enumerate(headers)}


def row_fingerprint(row_map: Mapping[str, Any]) -> str:
    return _hash_json({str(key): _canonical_cell(value) for key, value in row_map.items()})


def header_set_fingerprint(headers: Sequence[str]) -> str:
    return _hash_json(sorted(headers))


def header_layout_fingerprint(headers: Sequence[str]) -> str:
    return _hash_json(list(headers))


def column_letter(index_1based: int) -> str:
    if index_1based < 1:
        raise ValueError("column index must be >= 1")
    result = ""
    current = index_1based
    while current:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


@dataclass(frozen=True)
class StableRowRef:
    table: str
    stable_id_header: str
    stable_id: str

    def __post_init__(self) -> None:
        if not self.table or not self.stable_id_header or not self.stable_id:
            raise ValueError("table, stable_id_header and stable_id are required")
        if any("\n" in value or "\r" in value for value in (self.table, self.stable_id_header, self.stable_id)):
            raise ValueError("stable row identity must be single-line")

    @property
    def identity(self) -> str:
        return f"{self.table}:{self.stable_id_header}={self.stable_id}"


@dataclass(frozen=True)
class TableSnapshot:
    table: str
    headers: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    observed_at: datetime
    header_row_number: int = 1

    def __post_init__(self) -> None:
        _aware(self.observed_at, "observed_at")
        if not self.table:
            raise ValueError("table is required")
        if self.header_row_number < 1:
            raise ValueError("header_row_number must be >= 1")
        if not self.headers or any(not header for header in self.headers):
            raise StableRowMutationError(StableRowErrorCode.INVALID_SCHEMA, "headers must be non-empty")
        if len(set(self.headers)) != len(self.headers):
            raise StableRowMutationError(StableRowErrorCode.INVALID_SCHEMA, "duplicate headers are forbidden")

    @property
    def data_start_row_number(self) -> int:
        return self.header_row_number + 1

    @property
    def header_positions(self) -> dict[str, int]:
        return {header: index + 1 for index, header in enumerate(self.headers)}


@dataclass(frozen=True)
class ResolvedRow:
    ref: StableRowRef
    row_number: int
    values_by_header: tuple[tuple[str, Any], ...]
    header_positions: tuple[tuple[str, int], ...]
    row_fingerprint: str
    header_set_fingerprint: str
    header_layout_fingerprint: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _aware(self.observed_at, "observed_at")
        if self.row_number < 1:
            raise ValueError("row_number must be positive")
        if len(self.row_fingerprint) != 64:
            raise ValueError("row_fingerprint must be SHA-256 hex")

    @property
    def values(self) -> dict[str, Any]:
        return dict(self.values_by_header)

    @property
    def positions(self) -> dict[str, int]:
        return dict(self.header_positions)


@dataclass(frozen=True)
class MutationRequest:
    ref: StableRowRef
    updates: tuple[tuple[str, Any], ...]
    expected_old_values: tuple[tuple[str, Any], ...] = ()
    expected_row_fingerprint: str | None = None

    def __post_init__(self) -> None:
        update_headers = [header for header, _ in self.updates]
        expected_headers = [header for header, _ in self.expected_old_values]
        if not self.updates:
            raise ValueError("updates cannot be empty")
        if len(update_headers) != len(set(update_headers)):
            raise ValueError("duplicate update headers are forbidden")
        if len(expected_headers) != len(set(expected_headers)):
            raise ValueError("duplicate expected_old_values headers are forbidden")
        if self.ref.stable_id_header in update_headers:
            raise StableRowMutationError(
                StableRowErrorCode.IMMUTABLE_STABLE_ID,
                "stable ID column cannot be mutated by this protocol",
            )
        for _, value in self.updates + self.expected_old_values:
            _canonical_cell(value)
        if self.expected_row_fingerprint is not None:
            if not isinstance(self.expected_row_fingerprint, str) or len(self.expected_row_fingerprint) != 64:
                raise ValueError("expected_row_fingerprint must be SHA-256 hex")


@dataclass(frozen=True)
class CellMutation:
    header: str
    row_number: int
    column_index_1based: int
    old_value: Any
    new_value: Any

    @property
    def a1(self) -> str:
        return f"{column_letter(self.column_index_1based)}{self.row_number}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "header": self.header,
            "row_number": self.row_number,
            "column_index_1based": self.column_index_1based,
            "a1": self.a1,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass(frozen=True)
class StableRowMutationPlan:
    mutation_key: str
    ref: StableRowRef
    first_row_number: int
    target_row_number: int
    row_moved_between_reads: bool
    column_layout_changed_between_reads: bool
    before_row_fingerprint: str
    after_row_fingerprint: str
    header_set_fingerprint: str
    mutations: tuple[CellMutation, ...]
    first_observed_at: datetime
    second_observed_at: datetime
    provider_write_executed: bool = False

    def __post_init__(self) -> None:
        _aware(self.first_observed_at, "first_observed_at")
        _aware(self.second_observed_at, "second_observed_at")
        if self.second_observed_at < self.first_observed_at:
            raise ValueError("second observation cannot precede first")
        if self.provider_write_executed:
            raise ValueError("stable-row mutation v1 is plan-only")
        if not self.mutation_key.startswith("SRM-") or len(self.mutation_key) != 68:
            raise ValueError("mutation_key must be SRM- plus SHA-256")
        if not self.mutations:
            raise ValueError("mutations cannot be empty")

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract": "UEX_STABLE_ROW_MUTATION",
            "version": "1.0.0",
            "mutation_key": self.mutation_key,
            "table": self.ref.table,
            "stable_id_header": self.ref.stable_id_header,
            "stable_id": self.ref.stable_id,
            "first_row_number": self.first_row_number,
            "target_row_number": self.target_row_number,
            "row_moved_between_reads": self.row_moved_between_reads,
            "column_layout_changed_between_reads": self.column_layout_changed_between_reads,
            "before_row_fingerprint": self.before_row_fingerprint,
            "after_row_fingerprint": self.after_row_fingerprint,
            "header_set_fingerprint": self.header_set_fingerprint,
            "mutations": [item.as_dict() for item in self.mutations],
            "first_observed_at": self.first_observed_at.isoformat(),
            "second_observed_at": self.second_observed_at.isoformat(),
            "provider_write_executed": False,
        }


@dataclass(frozen=True)
class ReadbackVerification:
    verified: bool
    ref: StableRowRef
    observed_row_number: int
    expected_fingerprint: str
    observed_fingerprint: str
    row_moved_after_write: bool
    observed_at: datetime

    def __post_init__(self) -> None:
        _aware(self.observed_at, "observed_at")

    def as_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "table": self.ref.table,
            "stable_id_header": self.ref.stable_id_header,
            "stable_id": self.ref.stable_id,
            "observed_row_number": self.observed_row_number,
            "expected_fingerprint": self.expected_fingerprint,
            "observed_fingerprint": self.observed_fingerprint,
            "row_moved_after_write": self.row_moved_after_write,
            "observed_at": self.observed_at.isoformat(),
        }


def resolve_unique_row(snapshot: TableSnapshot, ref: StableRowRef) -> ResolvedRow:
    if snapshot.table != ref.table:
        raise StableRowMutationError(
            StableRowErrorCode.TABLE_MISMATCH,
            f"snapshot table {snapshot.table!r} != ref table {ref.table!r}",
        )
    if ref.stable_id_header not in snapshot.headers:
        raise StableRowMutationError(
            StableRowErrorCode.ID_HEADER_MISSING,
            f"stable ID header {ref.stable_id_header!r} not present",
        )
    matches: list[tuple[int, dict[str, Any]]] = []
    for offset, row in enumerate(snapshot.rows):
        row_map = canonical_row_map(snapshot.headers, row)
        if row_map[ref.stable_id_header] == ref.stable_id:
            matches.append((snapshot.data_start_row_number + offset, row_map))
    if not matches:
        raise StableRowMutationError(
            StableRowErrorCode.STABLE_ID_NOT_FOUND,
            f"stable ID {ref.stable_id!r} not found in {ref.table}",
        )
    if len(matches) > 1:
        raise StableRowMutationError(
            StableRowErrorCode.STABLE_ID_DUPLICATE,
            f"stable ID {ref.stable_id!r} appears {len(matches)} times",
        )
    row_number, row_map = matches[0]
    return ResolvedRow(
        ref=ref,
        row_number=row_number,
        values_by_header=tuple(sorted(row_map.items())),
        header_positions=tuple(sorted(snapshot.header_positions.items())),
        row_fingerprint=row_fingerprint(row_map),
        header_set_fingerprint=header_set_fingerprint(snapshot.headers),
        header_layout_fingerprint=header_layout_fingerprint(snapshot.headers),
        observed_at=snapshot.observed_at,
    )


def _mutation_key(ref: StableRowRef, before_fingerprint: str, updates: Mapping[str, Any]) -> str:
    payload = {
        "identity": ref.identity,
        "before_fingerprint": before_fingerprint,
        "updates": {key: _canonical_cell(value) for key, value in sorted(updates.items())},
    }
    return "SRM-" + _hash_json(payload)


def prepare_stable_row_mutation(
    *,
    first_snapshot: TableSnapshot,
    second_snapshot: TableSnapshot,
    request: MutationRequest,
) -> StableRowMutationPlan:
    """Prepare an optimistic mutation after two independent stable-ID reads."""

    if second_snapshot.observed_at < first_snapshot.observed_at:
        raise ValueError("second snapshot cannot precede first snapshot")
    first = resolve_unique_row(first_snapshot, request.ref)
    second = resolve_unique_row(second_snapshot, request.ref)

    if first.header_set_fingerprint != second.header_set_fingerprint:
        raise StableRowMutationError(
            StableRowErrorCode.CONCURRENT_ROW_CHANGE,
            "header set changed between reads; re-read schema before mutation",
        )
    if first.row_fingerprint != second.row_fingerprint:
        raise StableRowMutationError(
            StableRowErrorCode.CONCURRENT_ROW_CHANGE,
            "row content changed between stable-ID reads",
        )
    if request.expected_row_fingerprint is not None and (
        first.row_fingerprint != request.expected_row_fingerprint
        or second.row_fingerprint != request.expected_row_fingerprint
    ):
        raise StableRowMutationError(
            StableRowErrorCode.EXPECTED_FINGERPRINT_MISMATCH,
            "observed row fingerprint does not match caller expectation",
        )

    current_values = second.values
    positions = second.positions
    updates = dict(request.updates)
    unknown = sorted(set(updates) - set(current_values))
    if unknown:
        raise StableRowMutationError(
            StableRowErrorCode.UNKNOWN_UPDATE_HEADER,
            f"unknown update headers: {', '.join(unknown)}",
        )
    for header, expected in request.expected_old_values:
        if header not in current_values:
            raise StableRowMutationError(
                StableRowErrorCode.UNKNOWN_UPDATE_HEADER,
                f"expected-old header {header!r} not present",
            )
        if current_values[header] != _canonical_cell(expected):
            raise StableRowMutationError(
                StableRowErrorCode.EXPECTED_OLD_VALUE_MISMATCH,
                f"{header!r} changed before mutation",
            )

    after = dict(current_values)
    mutations: list[CellMutation] = []
    for header, new_value in sorted(updates.items()):
        canonical_new = _canonical_cell(new_value)
        mutations.append(
            CellMutation(
                header=header,
                row_number=second.row_number,
                column_index_1based=positions[header],
                old_value=current_values[header],
                new_value=canonical_new,
            )
        )
        after[header] = canonical_new

    return StableRowMutationPlan(
        mutation_key=_mutation_key(request.ref, second.row_fingerprint, updates),
        ref=request.ref,
        first_row_number=first.row_number,
        target_row_number=second.row_number,
        row_moved_between_reads=first.row_number != second.row_number,
        column_layout_changed_between_reads=(
            first.header_layout_fingerprint != second.header_layout_fingerprint
        ),
        before_row_fingerprint=second.row_fingerprint,
        after_row_fingerprint=row_fingerprint(after),
        header_set_fingerprint=second.header_set_fingerprint,
        mutations=tuple(mutations),
        first_observed_at=first.observed_at,
        second_observed_at=second.observed_at,
    )


def verify_stable_row_readback(
    *,
    plan: StableRowMutationPlan,
    readback_snapshot: TableSnapshot,
) -> ReadbackVerification:
    """Verify provider output by resolving the stable ID again after mutation."""

    observed = resolve_unique_row(readback_snapshot, plan.ref)
    if observed.row_fingerprint != plan.after_row_fingerprint:
        raise StableRowMutationError(
            StableRowErrorCode.READBACK_MISMATCH,
            f"expected {plan.after_row_fingerprint}, observed {observed.row_fingerprint}",
        )
    return ReadbackVerification(
        verified=True,
        ref=plan.ref,
        observed_row_number=observed.row_number,
        expected_fingerprint=plan.after_row_fingerprint,
        observed_fingerprint=observed.row_fingerprint,
        row_moved_after_write=observed.row_number != plan.target_row_number,
        observed_at=observed.observed_at,
    )
