from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from uexchanges.forms import FieldOwnership, FieldSensitivity, FormField, FormFieldType, form_schema_fingerprint


ROOT = Path(__file__).resolve().parents[1]
NODE_MODULE = (ROOT / "tools" / "form-executor" / "src" / "fingerprint.mjs").as_uri()


def node_fingerprint(*, provider: str, url: str, fields: list[dict]) -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required for fingerprint parity test")
    script = f"""
import fs from 'node:fs';
import {{ formSchemaFingerprint }} from {json.dumps(NODE_MODULE)};
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(formSchemaFingerprint({{
  provider: payload.provider,
  canonicalFormUrl: payload.url,
  fields: payload.fields,
}}));
"""
    result = subprocess.run(
        [node, "--input-type=module", "--eval", script],
        input=json.dumps({"provider": provider, "url": url, "fields": fields}, ensure_ascii=False),
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise AssertionError(f"Node fingerprint failed: {result.stderr}")
    return result.stdout.strip()


def py_field(raw: dict) -> FormField:
    return FormField(
        field_key=raw["field_key"],
        label=raw["label"],
        field_type=FormFieldType(raw["field_type"]),
        required=raw["required"],
        options=tuple(raw.get("options", [])),
        maxlength=raw.get("maxlength"),
        ownership=FieldOwnership.UNRESOLVED,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=False,
    )


class FormFingerprintParityTests(unittest.TestCase):
    def assert_parity(self, provider: str, url: str, fields: list[dict]) -> None:
        python_value = form_schema_fingerprint(
            provider=provider,
            canonical_form_url=url,
            fields=tuple(py_field(item) for item in fields),
        )
        node_value = node_fingerprint(provider=provider, url=url, fields=fields)
        self.assertEqual(python_value, node_value)

    def test_parity_for_unicode_options_query_and_fragment(self):
        self.assert_parity(
            "Generic_HTML",
            "https://EXAMPLE.COM:443/forms/apply?call=España%202026#private",
            [
                {"field_key":"name","label":"Nombre y apellidos","field_type":"text","required":True,"options":[],"maxlength":120},
                {"field_key":"country","label":"País","field_type":"select","required":True,"options":["España","Portugal","Türkiye"],"maxlength":None},
                {"field_key":"role","label":"Participant","field_type":"radio","required":False,"options":["Participant","Group leader"],"maxlength":None},
            ],
        )

    def test_parity_for_root_url_default_path_and_explicit_http_port(self):
        self.assert_parity(
            "google_forms",
            "http://LOCALHOST:80?x=1#ignored",
            [
                {"field_key":"email","label":"Email","field_type":"email","required":True,"options":[],"maxlength":None},
            ],
        )


if __name__ == "__main__":
    unittest.main()
