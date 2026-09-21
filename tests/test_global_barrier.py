from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from uexchanges.global_barrier import (
    BarrierCheckCode,
    BarrierRecord,
    BarrierState,
    evaluate_global_barrier,
    resolve_global_barriers,
    scope_sha256,
)

NOW = datetime(2026, 9, 21, 20, 0, tzinfo=timezone.utc)
PROJECT = "UE-Xchanges-OS"
CONTEXT = "CTX-UEX-GLOBAL-EXPANSION-INCOME-V1"
SCOPE = "github:src/uexchanges/writer_authorization.py"
INTENT = "VERSIONED_CODE"


def record(
    barrier_id="BAR-C0",
    *,
    revision=1,
    state=BarrierState.ACTIVE,
    intents=(INTENT,),
    scope_hash=None,
    event_id=None,
):
    return BarrierRecord(
        barrier_id=barrier_id,
        revision=revision,
        event_id=event_id or f"EVT-{barrier_id}-{revision}",
        project_id=PROJECT,
        context_id=CONTEXT,
        state=state,
        blocked_intents=tuple(sorted(intents)),
        updated_at=NOW,
        scope_sha256=scope_hash,
    )


def snapshot(records=(), *, scope=SCOPE, intent=INTENT, observed_at=NOW, complete=True):
    return resolve_global_barriers(
        records=records,
        project_id=PROJECT,
        context_id=CONTEXT,
        intent=intent,
        scope=scope,
        observed_at=observed_at,
        event_watermark="EVT-WM-100",
        source_complete=complete,
    )


class GlobalBarrierTests(unittest.TestCase):
    def test_complete_empty_history_is_clear(self):
        item = snapshot()
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope=SCOPE,
            now=NOW,
            max_age_seconds=120,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.codes, (BarrierCheckCode.CLEAR,))
        self.assertEqual(item.active_barrier_ids, ())

    def test_project_wide_active_barrier_blocks(self):
        item = snapshot((record(),))
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope=SCOPE,
            now=NOW,
            max_age_seconds=120,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.codes, (BarrierCheckCode.ACTIVE,))
        self.assertEqual(item.active_barrier_ids, ("BAR-C0",))

    def test_exact_scope_barrier_does_not_block_other_scope(self):
        restricted = scope_sha256("github:other")
        item = snapshot((record(scope_hash=restricted),))
        self.assertEqual(item.active_barrier_ids, ())

    def test_explicit_higher_release_revision_clears(self):
        item = snapshot(
            (
                record(revision=1, state=BarrierState.ACTIVE),
                record(revision=2, state=BarrierState.RELEASED),
            )
        )
        self.assertEqual(item.active_barrier_ids, ())
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope=SCOPE,
            now=NOW,
            max_age_seconds=120,
        )
        self.assertTrue(result.allowed)

    def test_silence_does_not_release_active_barrier(self):
        item = snapshot((record(revision=4, state=BarrierState.ACTIVE),))
        self.assertTrue(item.blocked)

    def test_incomplete_source_fails_unknown(self):
        item = snapshot((), complete=False)
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope=SCOPE,
            now=NOW,
            max_age_seconds=120,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.codes, (BarrierCheckCode.UNKNOWN,))

    def test_conflicting_same_revision_fails_unknown(self):
        first = record(revision=3, state=BarrierState.ACTIVE, event_id="EVT-A")
        second = replace(first, event_id="EVT-B", state=BarrierState.RELEASED)
        item = snapshot((first, second))
        self.assertEqual(item.conflict_barrier_ids, ("BAR-C0",))
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope=SCOPE,
            now=NOW,
            max_age_seconds=120,
        )
        self.assertEqual(result.codes, (BarrierCheckCode.UNKNOWN,))

    def test_concurrent_barriers_are_deterministic(self):
        item = snapshot((record("BAR-Z"), record("BAR-A")))
        self.assertEqual(item.active_barrier_ids, ("BAR-A", "BAR-Z"))
        again = snapshot(tuple(reversed((record("BAR-Z"), record("BAR-A")))))
        self.assertEqual(item.revision_sha256, again.revision_sha256)

    def test_stale_snapshot_fails_closed(self):
        item = snapshot(observed_at=NOW - timedelta(seconds=121))
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope=SCOPE,
            now=NOW,
            max_age_seconds=120,
        )
        self.assertEqual(result.codes, (BarrierCheckCode.STALE,))

    def test_identity_or_scope_mismatch_fails_closed(self):
        item = snapshot()
        result = evaluate_global_barrier(
            item,
            project_id=PROJECT,
            context_id=CONTEXT,
            intent=INTENT,
            scope="github:different",
            now=NOW,
            max_age_seconds=120,
        )
        self.assertEqual(result.codes, (BarrierCheckCode.MISMATCH,))


if __name__ == "__main__":
    unittest.main()
