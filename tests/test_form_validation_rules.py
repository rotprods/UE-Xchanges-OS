from __future__ import annotations

import unittest

from uexchanges.forms.validation_rules import (
    NativeConstraints,
    ValidationExpectation,
    ValidationField,
    validation_signature,
)


class FormValidationRulesTests(unittest.TestCase):
    def test_signature_changes_for_material_native_constraint_change(self):
        base = ValidationField(
            field_key="motivation",
            label="Motivation",
            field_type="textarea",
            required=True,
            constraints=NativeConstraints(minlength=20, maxlength=250),
        )
        changed = ValidationField(
            field_key="motivation",
            label="Motivation",
            field_type="textarea",
            required=True,
            constraints=NativeConstraints(minlength=50, maxlength=250),
        )
        first = validation_signature(
            provider="generic_html",
            canonical_form_url="https://EXAMPLE.COM:443/form?call=2026#private",
            fields=(base,),
        )
        second = validation_signature(
            provider="generic_html",
            canonical_form_url="https://EXAMPLE.COM:443/form?call=2026#private",
            fields=(changed,),
        )
        self.assertNotEqual(first, second)

    def test_expectation_rejects_tampered_signature(self):
        field = ValidationField(
            field_key="email",
            label="Email",
            field_type="email",
            required=True,
        )
        signature = validation_signature(
            provider="generic_html",
            canonical_form_url="https://example.org/form",
            fields=(field,),
        )
        valid = ValidationExpectation(
            provider="generic_html",
            canonical_form_url="https://example.org/form",
            fields=(field,),
            signature=signature,
        )
        self.assertEqual(valid.signature, signature)
        with self.assertRaisesRegex(ValueError, "signature does not match"):
            ValidationExpectation(
                provider="generic_html",
                canonical_form_url="https://example.org/form",
                fields=(field,),
                signature="sha256:" + "0" * 64,
            )

    def test_duplicate_keys_and_invalid_constraints_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            NativeConstraints(minlength=-1)
        field = ValidationField(field_key="x", label="X", field_type="text", required=False)
        with self.assertRaisesRegex(ValueError, "unique"):
            validation_signature(
                provider="generic_html",
                canonical_form_url="https://example.org/form",
                fields=(field, field),
            )


if __name__ == "__main__":
    unittest.main()
