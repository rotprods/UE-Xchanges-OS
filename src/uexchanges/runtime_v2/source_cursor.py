from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


@dataclass(frozen=True)
class SourceCursor:
    """Durable monotonic high-watermark for one ingress source.

    A cursor summarizes the newest durable observation known for polling and recovery.
    It is not an exclusivity guarantee: a late unique event with an older timestamp or
    lower sequence may still be processed by the dispatcher, but it must never rewind
    ``high_watermark``, ``last_observed_at`` or ``last_source_item_id``.
    """

    source_id: str
    high_watermark: int = 0
    last_source_item_id: str | None = None
    last_observed_at: datetime | None = None
    revision: int = 0

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must be non-empty")
        if self.high_watermark < 0:
            raise ValueError("high_watermark must be >= 0")
        if self.revision < 0:
            raise ValueError("revision must be >= 0")
        if self.last_observed_at is not None:
            _aware(self.last_observed_at, "last_observed_at")


class SourceCursorStore:
    def __init__(self) -> None:
        self._cursors: dict[str, SourceCursor] = {}

    def get(self, source_id: str) -> SourceCursor:
        if not source_id.strip():
            raise ValueError("source_id must be non-empty")
        return self._cursors.get(source_id, SourceCursor(source_id=source_id))

    def advance(
        self,
        *,
        source_id: str,
        source_item_id: str,
        observed_at: datetime,
        sequence: int | None,
    ) -> SourceCursor:
        _aware(observed_at, "observed_at")
        if not source_item_id.strip():
            raise ValueError("source_item_id must be non-empty")
        if sequence is not None and sequence < 0:
            raise ValueError("sequence must be >= 0")

        current = self.get(source_id)
        next_watermark = max(current.high_watermark, sequence or 0)
        is_new_cursor_head = _is_new_cursor_head(
            current=current,
            observed_at=observed_at,
            sequence=sequence,
        )
        updated = replace(
            current,
            high_watermark=next_watermark,
            last_source_item_id=(
                source_item_id if is_new_cursor_head else current.last_source_item_id
            ),
            last_observed_at=(
                observed_at if is_new_cursor_head else current.last_observed_at
            ),
            revision=current.revision + 1,
        )
        self._cursors[source_id] = updated
        return updated

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {
            source_id: {
                "source_id": cursor.source_id,
                "high_watermark": cursor.high_watermark,
                "last_source_item_id": cursor.last_source_item_id,
                "last_observed_at": (
                    cursor.last_observed_at.isoformat()
                    if cursor.last_observed_at is not None
                    else None
                ),
                "revision": cursor.revision,
            }
            for source_id, cursor in sorted(self._cursors.items())
        }


def _is_new_cursor_head(
    *,
    current: SourceCursor,
    observed_at: datetime,
    sequence: int | None,
) -> bool:
    """Return whether an applied event may replace the polling/recovery cursor head.

    Sequence-aware sources use sequence first and timestamp as the tie-breaker.
    Sequence-less sources use timestamp only.  Late events remain processable but do
    not become the cursor head.
    """
    current_time = current.last_observed_at
    if sequence is None:
        return current_time is None or observed_at >= current_time
    if sequence > current.high_watermark:
        return True
    if sequence < current.high_watermark:
        return False
    return current_time is None or observed_at >= current_time
