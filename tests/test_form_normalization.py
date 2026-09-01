from __future__ import annotations

import math
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from uexchanges.forms import (
    FieldOwnership,
    FieldSensitivity,
    FormField,
    FormFieldType,
    normalize_answer,
)


def field(field_type: FormFieldType, answer, **overrides) -> FormField:
    base = dict(
        field_key="value",
        label="Value",
        field_type=field_type,
        required=True,
        answer=answer,
        answer_source="test",
        evidence_ids=("ev",),
        ownership=FieldOwnership.GREEN,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=True,
    )
    base.update(overrides)
    return FormField(**base)


class FormNormalizationTests(unittest.TestCase):
    def test_text_normalizes_unicode_and_line_endings_without_trimming_content(self):
        composed = normalize_answer(field(FormFieldType.TEXTAREA, " A\r\ncafe\u0301\r"))
        self.assertEqual(composed, " A\ncafé\n")

    def test_email_trims_outer_whitespace_without_lowercasing_local_part(self):
        self.assertEqual(
            normalize_answer(field(FormFieldType.EMAIL, "  Roberto.Example@Example.COM \r\n")),
            "Roberto.Example@Example.COM",
        )

    def test_numbers_have_one_decimal_identity(self):
        values = ["1", "1.0", "1.00", 1, Decimal("1.000")]
        self.assertEqual({normalize_answer(field(FormFieldType.NUMBER, value)) for value in values}, {"1"})
        self.assertEqual(normalize_answer(field(FormFieldType.NUMBER, "1000.00")), "1000")
        self.assertEqual(normalize_answer(field(FormFieldType.NUMBER, "-0.000")), "0")

    def test_non_finite_and_boolean_numbers_are_rejected(self):
        for value in [math.nan, math.inf, -math.inf, True, "NaN", "Infinity"]:
            with self.assertRaises(ValueError):
                normalize_answer(field(FormFieldType.NUMBER, value))

    def test_date_is_strict_iso_calendar_date(self):
        self.assertEqual(normalize_answer(field(FormFieldType.DATE, date(2026, 10, 20))), "2026-10-20")
        self.assertEqual(normalize_answer(field(FormFieldType.DATE, " 2026-10-20 ")), "2026-10-20")
        with self.assertRaises(ValueError):
            normalize_answer(field(FormFieldType.DATE, datetime(2026, 10, 20, tzinfo=timezone.utc)))
        with self.assertRaises(ValueError):
            normalize_answer(field(FormFieldType.DATE, "20/10/2026"))

    def test_checkbox_groups_are_unique_sorted_and_unicode_normalized(self):
        first = normalize_answer(field(FormFieldType.CHECKBOX, [" Video ", "Photograph\u0079", "Video"]))
        second = normalize_answer(field(FormFieldType.CHECKBOX, ("Photography", "Video")))
        self.assertEqual(first, ["Photography", "Video"])
        self.assertEqual(first, second)
        self.assertIs(normalize_answer(field(FormFieldType.CHECKBOX, True)), True)

    def test_consent_requires_boolean(self):
        self.assertTrue(normalize_answer(field(FormFieldType.CONSENT, True)))
        with self.assertRaises(ValueError):
            normalize_answer(field(FormFieldType.CONSENT, "yes"))

    def test_file_and_unknown_values_never_enter_canonical_model_payload(self):
        for field_type in (FormFieldType.FILE, FormFieldType.UNKNOWN):
            with self.assertRaises(ValueError):
                normalize_answer(field(field_type, "opaque"))

    def test_black_field_has_no_model_visible_normalized_answer(self):
        black = FormField(
            field_key="otp",
            label="OTP",
            field_type=FormFieldType.TEXT,
            required=True,
            answer=None,
            ownership=FieldOwnership.BLACK,
            sensitivity=FieldSensitivity.SECRET,
            editable_by_agent=False,
        )
        self.assertIsNone(normalize_answer(black))


if __name__ == "__main__":
    unittest.main()
