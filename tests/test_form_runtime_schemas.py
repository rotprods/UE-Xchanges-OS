from __future__ import annotations

import json
import unittest
from pathlib import Path

from uexchanges.forms import provider_manifest_from_mapping


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
MANIFESTS = ROOT / "config" / "form-providers"


class RuntimeSchemaContractTests(unittest.TestCase):
    def test_runtime_schemas_are_closed_draft_2020_12_objects(self):
        for name in (
            "form-runtime-doctor-evidence.schema.json",
            "form-runtime-attestation.schema.json",
            "form-authenticated-inspect.schema.json",
            "form-provider-capability.schema.json",
        ):
            schema = json.loads((SCHEMAS / name).read_text())
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")
            self.assertFalse(schema["additionalProperties"])

    def test_doctor_schema_requires_network_isolation_and_ephemeral_profile(self):
        props = json.loads((SCHEMAS / "form-runtime-doctor-evidence.schema.json").read_text())["properties"]
        self.assertEqual(props["status"]["const"], "ok")
        self.assertEqual(props["launch"]["const"], "ok")
        self.assertEqual(props["network"]["const"], "blocked")
        self.assertEqual(props["profile"]["const"], "ephemeral")
        self.assertEqual(props["node_major"]["minimum"], 20)

    def test_inspect_schema_forbids_value_cookie_and_storage_export_claims(self):
        props = json.loads((SCHEMAS / "form-authenticated-inspect.schema.json").read_text())["properties"]
        self.assertIs(props["form_values_read"]["const"], False)
        self.assertIs(props["cookies_read"]["const"], False)
        self.assertIs(props["storage_state_exported"]["const"], False)

    def test_all_committed_provider_manifests_parse_strictly(self):
        files = sorted(MANIFESTS.glob("*.json"))
        self.assertTrue(files)
        for path in files:
            manifest = provider_manifest_from_mapping(json.loads(path.read_text()))
            self.assertTrue(manifest.provider_id)
            self.assertTrue(manifest.manifest_version)


if __name__ == "__main__":
    unittest.main()
