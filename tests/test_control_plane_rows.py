import unittest

from uexchanges.runtime_v2.control_plane_rows import (
    StableRowDuplicate,
    StableRowIdentityChanged,
    StableRowMissing,
    assert_row_identity,
    resolve_stable_row,
    resolve_then_verify,
)


class ControlPlaneStableRowTests(unittest.TestCase):
    def test_resolve_exact_entity_id(self):
        rows = (("LSE-A", "a"), ("LSE-B", "b"))
        row = resolve_stable_row(rows, entity_id="LSE-B", first_row_number=10)
        self.assertEqual(row.row_number, 11)
        self.assertEqual(row.values[1], "b")

    def test_missing_and_duplicate_fail_closed(self):
        with self.assertRaises(StableRowMissing):
            resolve_stable_row((("A",),), entity_id="B")
        with self.assertRaises(StableRowDuplicate):
            resolve_stable_row((("A",), ("A",)), entity_id="A")

    def test_compare_before_write_detects_identity_change(self):
        rows = (("A",), ("B",))
        with self.assertRaises(StableRowIdentityChanged):
            assert_row_identity(rows, row_number=2, expected_entity_id="A")

    def test_concurrent_insert_moves_row_and_second_read_wins(self):
        reads = [
            (("A", "one"), ("TARGET", "old"), ("C", "three")),
            (("NEW", "inserted"), ("A", "one"), ("TARGET", "old"), ("C", "three")),
        ]
        calls = {"n": 0}

        def read_rows():
            index = min(calls["n"], len(reads) - 1)
            calls["n"] += 1
            return reads[index]

        resolved = resolve_then_verify(read_rows, entity_id="TARGET", first_row_number=20)
        self.assertEqual(resolved.row_number, 22)
        self.assertEqual(calls["n"], 2)

    def test_id_column_can_be_nonzero(self):
        rows = ((1, "SES-A", "x"), (2, "SES-B", "y"))
        row = resolve_stable_row(rows, entity_id="SES-B", id_column=1, first_row_number=5)
        self.assertEqual(row.row_number, 6)


if __name__ == "__main__":
    unittest.main()
