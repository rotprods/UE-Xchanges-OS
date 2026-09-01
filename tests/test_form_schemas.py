from __future__ import annotations

import json
from pathlib import Path


SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text())


def test_form_execution_plan_schema_references_existing_field_schema():
    schema = load("form-execution-plan.schema.json")
    assert schema["properties"]["fields"]["items"]["$ref"] == "form-field.schema.json"
    assert (SCHEMAS / "form-field.schema.json").exists()


def test_contract_schemas_use_draft_2020_12_and_closed_objects():
    for name in (
        "form-field.schema.json",
        "form-execution-plan.schema.json",
        "submission-attempt.schema.json",
        "submission-receipt.schema.json",
    ):
        schema = load(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False


def test_plan_schema_has_submission_boundary_fields():
    schema = load("form-execution-plan.schema.json")
    required = set(schema["required"])
    assert {
        "application_id",
        "form_fingerprint",
        "ai_policy",
        "auth_requirement",
        "submit_authority",
        "allowed_origins",
        "expires_at",
    } <= required


def test_receipt_schema_does_not_store_credentials_or_cookie_material():
    props = set(load("submission-receipt.schema.json")["properties"])
    forbidden = {"password", "cookie", "cookies", "token", "otp", "authorization"}
    assert props.isdisjoint(forbidden)
