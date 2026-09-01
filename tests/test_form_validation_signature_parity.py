from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from uexchanges.forms.validation_rules import NativeConstraints, ValidationField, validation_signature


ROOT = Path(__file__).resolve().parents[1]
NODE_MODULE = (ROOT / "tools" / "form-executor" / "src" / "validation-signature.mjs").as_uri()


def node_signature(*, provider: str, url: str, fields: list[dict]) -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required for validation signature parity test")
    script = f"""
import fs from 'node:fs';
import {{ validationSignature }} from {json.dumps(NODE_MODULE)};
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(validationSignature({{
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
        raise AssertionError(f"Node validation signature failed: {result.stderr}")
    return result.stdout.strip()


def py_field(raw: dict) -> ValidationField:
    constraints = raw["constraints"]
    return ValidationField(
        field_key=raw["field_key"],
        label=raw["label"],
        field_type=raw["field_type"],
        required=raw["required"],
        options=tuple(raw.get("options", [])),
        constraints=NativeConstraints(
            minlength=constraints.get("minlength"),
            maxlength=constraints.get("maxlength"),
            pattern=constraints.get("pattern"),
            min_value=constraints.get("min_value"),
            max_value=constraints.get("max_value"),
            step=constraints.get("step"),
            multiple=constraints.get("multiple", False),
            accept=tuple(constraints.get("accept", [])),
        ),
    )


class ValidationSignatureParityTests(unittest.TestCase):
    def test_parity_for_full_constraint_surface(self):
        fields = [
            {
                "field_key":"motivation","label":"Motivación","field_type":"textarea","required":True,"options":[],
                "constraints":{"minlength":20,"maxlength":250,"pattern":".{20,}","min_value":None,"max_value":None,"step":None,"multiple":False,"accept":[]},
            },
            {
                "field_key":"age","label":"Age","field_type":"number","required":True,"options":[],
                "constraints":{"minlength":None,"maxlength":None,"pattern":None,"min_value":"18","max_value":"30","step":"1","multiple":False,"accept":[]},
            },
            {
                "field_key":"portfolio","label":"Portfolio files","field_type":"file","required":False,"options":[],
                "constraints":{"minlength":None,"maxlength":None,"pattern":None,"min_value":None,"max_value":None,"step":None,"multiple":True,"accept":["image/png","image/jpeg"]},
            },
        ]
        provider = "Generic_HTML"
        url = "https://EXAMPLE.COM:443/form?call=España%202026#private"
        python_value = validation_signature(
            provider=provider,
            canonical_form_url=url,
            fields=tuple(py_field(item) for item in fields),
        )
        node_value = node_signature(provider=provider, url=url, fields=fields)
        self.assertEqual(python_value, node_value)


if __name__ == "__main__":
    unittest.main()
