import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.runtime_v2.source_cursor import SourceCursorStore

NOW = datetime(2026, 9, 2, 0, 35, tzinfo=timezone(timedelta(hours=2)))


class SourceCursorMonotonicityTests(unittest.TestCase):
    def test_sequence_less_late_unique_event_does_not_rewind_cursor_head(self):
        store = SourceCursorStore()
        newest = store.advance(
            source_id="gmail:organiser-replies",
            source_item_id="gmail:newest",
            observed_at=NOW,
            sequence=None,
        )
        late = store.advance(
            source_id="gmail:organiser-replies",
            source_item_id="gmail:late-but-unique",
            observed_at=NOW - timedelta(hours=3),
            sequence=None,
        )
        self.assertEqual(newest.last_source_item_id, "gmail:newest")
        self.assertEqual(late.last_source_item_id, "gmail:newest")
        self.assertEqual(late.last_observed_at, NOW)
        self.assertEqual(late.high_watermark, 0)
        self.assertEqual(late.revision, 2)

    def test_sequence_source_rejects_lower_or_older_equal_sequence_as_cursor_head(self):
        store = SourceCursorStore()
        store.advance(
            source_id="provider:events",
            source_item_id="event-10",
            observed_at=NOW,
            sequence=10,
        )
        lower = store.advance(
            source_id="provider:events",
            source_item_id="event-5",
            observed_at=NOW + timedelta(hours=1),
            sequence=5,
        )
        self.assertEqual(lower.high_watermark, 10)
        self.assertEqual(lower.last_source_item_id, "event-10")
        self.assertEqual(lower.last_observed_at, NOW)

        older_equal = store.advance(
            source_id="provider:events",
            source_item_id="event-10-older",
            observed_at=NOW - timedelta(minutes=1),
            sequence=10,
        )
        self.assertEqual(older_equal.last_source_item_id, "event-10")
        self.assertEqual(older_equal.last_observed_at, NOW)

        newer_equal = store.advance(
            source_id="provider:events",
            source_item_id="event-10-newer",
            observed_at=NOW + timedelta(minutes=1),
            sequence=10,
        )
        self.assertEqual(newer_equal.last_source_item_id, "event-10-newer")
        self.assertEqual(newer_equal.last_observed_at, NOW + timedelta(minutes=1))


if __name__ == "__main__":
    unittest.main()
