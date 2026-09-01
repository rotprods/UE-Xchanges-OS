from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from uexchanges.forms import (
    FieldOwnership,
    FieldSensitivity,
    FormField,
    FormFieldType,
    normalize_answer,
)


ROOT = Path(__file__).resolve().parents[1]
NODE_MODULE = (ROOT / "tools" / "form-executor" / "src" / "normalization.mjs").as_uri()


def node_normalize(field_type: str, value):
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required for normalization parity test")
    script = f"""
import fs from 'node:fs';
import {{ canonicalizeAnswer }} from {json.dumps(NODE_MODULE)};
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(canonicalizeAnswer(payload.field_type, payload.value)));
"""
    result = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        input=json.dumps({"field_type": field_type, "value": value}, ensure_ascii=False),
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise AssertionError(f"Node normalization failed: {result.stderr}")
    return json.loads(result.stdout)


def py_field(field_type: FormFieldType, value) -> FormField:
    options = ("Spain", "Portugal") if field_type in {FormFieldType.SELECT, FormFieldType.RADIO} else ()
    return FormField(
        field_key="value",
        label="Value",
        field_type=field_type,
        required=True,
        options=options,
        answer=value,
        answer_source="parity",
        evidence_ids=("ev",),
        ownership=FieldOwnership.GREEN,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=True,
    )


class FormNormalizationParityTests(unittest.TestCase):
    def assert_parity(self, field_type: FormFieldType, value) -> None:
        self.assertEqual(normalize_answer(py_field(field_type, value)), node_normalize(field_type.value, value))

    def test_text_email_unicode_and_line_endings(self):
        self.assert_parity(FormFieldType.TEXTAREA, " A\r\ncafe\u0301\r")
        self.assert_parity(FormFieldType.EMAIL, " Roberto.Example@Example.COM \r\n")

    def test_decimal_identity_parity(self):
        for value in ["1", "1.0", "1.00", 1, "-0.000", "1000.00", "1e3", "0.00100"]:
            self.assert_parity(FormFieldType.NUMBER, value)

    def test_date_choice_checkbox_and_consent_parity(self):
        self.assert_parity(FormFieldType.DATE, "2026-10-20")
        self.assert_parity(FormFieldType.SELECT, " Spain ")
        self.assert_parity(FormFieldType.RADIO, " Portugal ")
        self.assert_parity(FormFieldType.CHECKBOX, ["Video", " Photography ", "Video"])
        self.assert_parity(FormFieldType.CHECKBOX, True)
        self.assert_parity(FormFieldType.CONSENT, False)


if __name__ == "__main__":
    unittest.main()
