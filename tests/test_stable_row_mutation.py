import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.stable_row_mutation import (
    MutationRequest,
    StableRowErrorCode,
    StableRowMutationError,
    StableRowRef,
    TableSnapshot,
    column_letter,
    prepare_stable_row_mutation,
    resolve_unique_row,
    verify_stable_row_readback,
)

T0 = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
REF = StableRowRef("Work_Leases", "Lease ID", "LSE-2")


def snap(headers=("Lease ID", "Status", "Last Event ID", "Owner"), rows=None, at=T0):
    if rows is None:
        rows = (
            ("LSE-1", "RELEASED", "E1", "s1"),
            ("LSE-2", "ACTIVE", "E2", "s2"),
            ("LSE-3", "ACTIVE", "E3", "s3"),
        )
    return TableSnapshot("Work_Leases", tuple(headers), tuple(tuple(row) for row in rows), at)


class StableRowMutationTests(unittest.TestCase):
    def test_unique_resolution_uses_stable_id_not_cached_row(self):
        resolved = resolve_unique_row(snap(), REF)
        self.assertEqual(resolved.row_number, 3)
        moved = snap(
            rows=(
                ("LSE-3", "ACTIVE", "E3", "s3"),
                ("LSE-1", "RELEASED", "E1", "s1"),
                ("LSE-2", "ACTIVE", "E2", "s2"),
            ),
            at=T0 + timedelta(seconds=1),
        )
        self.assertEqual(resolve_unique_row(moved, REF).row_number, 4)

    def test_duplicate_stable_id_fails_closed(self):
        duplicate = snap(
            rows=(
                ("LSE-2", "ACTIVE", "E2", "s2"),
                ("LSE-2", "RELEASED", "E4", "s4"),
            )
        )
        with self.assertRaises(StableRowMutationError) as ctx:
            resolve_unique_row(duplicate, REF)
        self.assertEqual(ctx.exception.code, StableRowErrorCode.STABLE_ID_DUPLICATE)

    def test_missing_stable_id_fails_closed(self):
        missing = snap(rows=(("LSE-1", "ACTIVE", "E1", "s1"),))
        with self.assertRaises(StableRowMutationError) as ctx:
            resolve_unique_row(missing, REF)
        self.assertEqual(ctx.exception.code, StableRowErrorCode.STABLE_ID_NOT_FOUND)

    def test_row_can_move_between_two_reads_when_content_is_same(self):
        first = snap()
        second = snap(
            rows=(
                ("LSE-2", "ACTIVE", "E2", "s2"),
                ("LSE-1", "RELEASED", "E1", "s1"),
                ("LSE-3", "ACTIVE", "E3", "s3"),
            ),
            at=T0 + timedelta(seconds=1),
        )
        plan = prepare_stable_row_mutation(
            first_snapshot=first,
            second_snapshot=second,
            request=MutationRequest(REF, (("Status", "RELEASED"),), (("Status", "ACTIVE"),)),
        )
        self.assertTrue(plan.row_moved_between_reads)
        self.assertEqual(plan.first_row_number, 3)
        self.assertEqual(plan.target_row_number, 2)
        self.assertEqual(plan.mutations[0].a1, "B2")

    def test_columns_can_reorder_and_are_remapped_by_header(self):
        first = snap()
        second = snap(
            headers=("Owner", "Last Event ID", "Lease ID", "Status"),
            rows=(
                ("s1", "E1", "LSE-1", "RELEASED"),
                ("s2", "E2", "LSE-2", "ACTIVE"),
                ("s3", "E3", "LSE-3", "ACTIVE"),
            ),
            at=T0 + timedelta(seconds=1),
        )
        plan = prepare_stable_row_mutation(
            first_snapshot=first,
            second_snapshot=second,
            request=MutationRequest(REF, (("Status", "RELEASED"), ("Last Event ID", "E9"))),
        )
        self.assertTrue(plan.column_layout_changed_between_reads)
        by_header = {item.header: item for item in plan.mutations}
        self.assertEqual(by_header["Status"].a1, "D3")
        self.assertEqual(by_header["Last Event ID"].a1, "B3")

    def test_real_row_change_between_reads_aborts(self):
        first = snap()
        changed = snap(
            rows=(
                ("LSE-1", "RELEASED", "E1", "s1"),
                ("LSE-2", "RELEASED", "E2", "s2"),
                ("LSE-3", "ACTIVE", "E3", "s3"),
            ),
            at=T0 + timedelta(seconds=1),
        )
        with self.assertRaises(StableRowMutationError) as ctx:
            prepare_stable_row_mutation(
                first_snapshot=first,
                second_snapshot=changed,
                request=MutationRequest(REF, (("Last Event ID", "E9"),)),
            )
        self.assertEqual(ctx.exception.code, StableRowErrorCode.CONCURRENT_ROW_CHANGE)

    def test_expected_old_value_prevents_lost_update(self):
        with self.assertRaises(StableRowMutationError) as ctx:
            prepare_stable_row_mutation(
                first_snapshot=snap(),
                second_snapshot=snap(at=T0 + timedelta(seconds=1)),
                request=MutationRequest(
                    REF,
                    (("Status", "RELEASED"),),
                    (("Status", "WAITING"),),
                ),
            )
        self.assertEqual(ctx.exception.code, StableRowErrorCode.EXPECTED_OLD_VALUE_MISMATCH)

    def test_stable_id_is_immutable(self):
        with self.assertRaises(StableRowMutationError) as ctx:
            MutationRequest(REF, (("Lease ID", "LSE-OTHER"),))
        self.assertEqual(ctx.exception.code, StableRowErrorCode.IMMUTABLE_STABLE_ID)

    def test_unknown_header_fails(self):
        with self.assertRaises(StableRowMutationError) as ctx:
            prepare_stable_row_mutation(
                first_snapshot=snap(),
                second_snapshot=snap(at=T0 + timedelta(seconds=1)),
                request=MutationRequest(REF, (("No Such Column", "x"),)),
            )
        self.assertEqual(ctx.exception.code, StableRowErrorCode.UNKNOWN_UPDATE_HEADER)

    def test_expected_fingerprint_can_bind_caller_observation(self):
        observed = resolve_unique_row(snap(), REF)
        plan = prepare_stable_row_mutation(
            first_snapshot=snap(),
            second_snapshot=snap(at=T0 + timedelta(seconds=1)),
            request=MutationRequest(
                REF,
                (("Status", "RELEASED"),),
                expected_row_fingerprint=observed.row_fingerprint,
            ),
        )
        self.assertEqual(plan.before_row_fingerprint, observed.row_fingerprint)

    def test_readback_resolves_id_again_even_if_row_moves(self):
        plan = prepare_stable_row_mutation(
            first_snapshot=snap(),
            second_snapshot=snap(at=T0 + timedelta(seconds=1)),
            request=MutationRequest(REF, (("Status", "RELEASED"), ("Last Event ID", "E9"))),
        )
        readback = snap(
            rows=(
                ("LSE-2", "RELEASED", "E9", "s2"),
                ("LSE-1", "RELEASED", "E1", "s1"),
                ("LSE-3", "ACTIVE", "E3", "s3"),
            ),
            at=T0 + timedelta(seconds=2),
        )
        verified = verify_stable_row_readback(plan=plan, readback_snapshot=readback)
        self.assertTrue(verified.verified)
        self.assertTrue(verified.row_moved_after_write)

    def test_readback_mismatch_is_failure_not_warning(self):
        plan = prepare_stable_row_mutation(
            first_snapshot=snap(),
            second_snapshot=snap(at=T0 + timedelta(seconds=1)),
            request=MutationRequest(REF, (("Status", "RELEASED"),)),
        )
        with self.assertRaises(StableRowMutationError) as ctx:
            verify_stable_row_readback(
                plan=plan,
                readback_snapshot=snap(at=T0 + timedelta(seconds=2)),
            )
        self.assertEqual(ctx.exception.code, StableRowErrorCode.READBACK_MISMATCH)

    def test_mutation_key_is_deterministic(self):
        args = dict(
            first_snapshot=snap(),
            second_snapshot=snap(at=T0 + timedelta(seconds=1)),
            request=MutationRequest(REF, (("Status", "RELEASED"),)),
        )
        self.assertEqual(
            prepare_stable_row_mutation(**args).mutation_key,
            prepare_stable_row_mutation(**args).mutation_key,
        )

    def test_duplicate_headers_and_nonempty_overflow_are_rejected(self):
        with self.assertRaises(StableRowMutationError) as ctx:
            TableSnapshot("T", ("ID", "ID"), (("1", "1"),), T0)
        self.assertEqual(ctx.exception.code, StableRowErrorCode.INVALID_SCHEMA)
        overflow = TableSnapshot("T", ("ID",), (("1", "unexpected"),), T0)
        with self.assertRaises(StableRowMutationError) as ctx2:
            resolve_unique_row(overflow, StableRowRef("T", "ID", "1"))
        self.assertEqual(ctx2.exception.code, StableRowErrorCode.INVALID_SCHEMA)

    def test_column_letters(self):
        self.assertEqual(column_letter(1), "A")
        self.assertEqual(column_letter(26), "Z")
        self.assertEqual(column_letter(27), "AA")
        self.assertEqual(column_letter(52), "AZ")
        self.assertEqual(column_letter(53), "BA")


if __name__ == "__main__":
    unittest.main()
