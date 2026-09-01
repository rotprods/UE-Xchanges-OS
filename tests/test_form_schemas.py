from __future__ import annotations

import json
import unittest
from pathlib import Path


SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text())


class FormSchemaContractTests(unittest.TestCase):
    def test_form_execution_plan_schema_references_existing_field_schema(self):
        schema = load("form-execution-plan.schema.json")
        self.assertEqual(schema["properties"]["fields"]["items"]["$ref"], "form-field.schema.json")
        self.assertTrue((SCHEMAS / "form-field.schema.json").exists())

    def test_contract_schemas_use_draft_2020_12_and_closed_objects(self):
        for name in (
            "form-field.schema.json",
            "form-execution-plan.schema.json",
            "submission-attempt.schema.json",
            "submission-receipt.schema.json",
        ):
            schema = load(name)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")
            self.assertFalse(schema["additionalProperties"])

    def test_plan_schema_has_submission_boundary_fields(self):
        required = set(load("form-execution-plan.schema.json")["required"])
        self.assertTrue({
            "application_id",
            "form_fingerprint",
            "ai_policy",
            "auth_requirement",
            "submit_authority",
            "allowed_origins",
            "expires_at",
        } <= required)

    def test_receipt_schema_does_not_store_credentials_or_cookie_material(self):
        props = set(load("submission-receipt.schema.json")["properties"])
        forbidden = {"password", "cookie", "cookies", "token", "otp", "authorization"}
        self.assertTrue(props.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
