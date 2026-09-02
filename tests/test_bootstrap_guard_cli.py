import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_bootstrap_compliance.py"


def load_script():
    spec = importlib.util.spec_from_file_location("audit_bootstrap_compliance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MAIN = "a" * 40
CTX = "CTX-UEX-GLOBAL-EXPANSION-INCOME-V1"


def snapshot(*, include_ack=True, include_prelease=True):
    data = {
        "now": "2026-09-02T05:04:00+00:00",
        "policy": {
            "manifest_version": "1.0.0",
            "current_main_sha": MAIN,
            "context_id": CTX,
            "effective_at": "2026-09-02T05:00:00+00:00",
            "max_prelease_scan_age_seconds": 120,
        },
        "sessions": [
            {
                "session_id": "SES-1",
                "agent_id": "AGT-1",
                "context_id": CTX,
                "started_at": "2026-09-02T05:01:00+00:00",
                "status": "ACTIVE",
            }
        ],
        "acks": [],
        "leases": [
            {
                "lease_id": "LSE-1",
                "owner_session_id": "SES-1",
                "owner_agent_id": "AGT-1",
                "context_id": CTX,
                "scope": "github:test",
                "acquired_at": "2026-09-02T05:03:00+00:00",
                "expires_at": "2026-09-02T06:03:00+00:00",
                "status": "ACTIVE",
            }
        ],
        "prelease_refreshes": {},
    }
    if include_ack:
        data["acks"] = [
            {
                "event_id": "EVT-ACK",
                "event_at": "2026-09-02T05:02:00+00:00",
                "payload": {
                    "manifest_version": "1.0.0",
                    "observed_main_sha": MAIN,
                    "context_id": CTX,
                    "public_read_refs": ["goal.md", "AGENTS.md"],
                    "private_event_watermark": "EVT-PREV",
                    "lease_scan_at": "2026-09-02T05:01:50+00:00",
                    "agent_id": "AGT-1",
                    "session_id": "SES-1",
                },
            }
        ]
    if include_prelease:
        data["prelease_refreshes"] = {
            "LSE-1": {
                "observed_main_sha": MAIN,
                "lease_scan_at": "2026-09-02T05:02:50+00:00",
                "private_event_watermark": "EVT-TAIL",
            }
        }
    return data


class BootstrapGuardCliTests(unittest.TestCase):
    def test_audit_snapshot_reports_compliant(self):
        module = load_script()
        report = module.audit_snapshot(snapshot())
        self.assertTrue(report["compliant"])
        self.assertEqual(report["violation_count"], 0)
        self.assertEqual(report["findings"][0]["codes"], ["COMPLIANT"])

    def test_audit_snapshot_reports_missing_ack(self):
        module = load_script()
        report = module.audit_snapshot(snapshot(include_ack=False))
        self.assertFalse(report["compliant"])
        self.assertGreaterEqual(report["violation_count"], 1)
        codes = {code for row in report["findings"] for code in row["codes"]}
        self.assertIn("MISSING_BOOTSTRAP_ACK", codes)

    def test_audit_snapshot_reports_missing_prelease_refresh(self):
        module = load_script()
        report = module.audit_snapshot(snapshot(include_prelease=False))
        self.assertFalse(report["compliant"])
        codes = {code for row in report["findings"] for code in row["codes"]}
        self.assertIn("MISSING_PRELEASE_REFRESH", codes)

    def test_main_exit_codes(self):
        module = load_script()
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.json"
            bad = Path(tmp) / "bad.json"
            good.write_text(json.dumps(snapshot()), encoding="utf-8")
            bad.write_text(json.dumps(snapshot(include_ack=False)), encoding="utf-8")
            self.assertEqual(module.main([str(good), "--fail-on-violation"]), 0)
            self.assertEqual(module.main([str(bad), "--fail-on-violation"]), 2)

    def test_schema_is_closed_and_requires_identity(self):
        schema = json.loads((ROOT / "schemas" / "agent-bootstrap-ack.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        required = set(schema["required"])
        self.assertTrue({"manifest_version", "observed_main_sha", "context_id", "agent_id", "session_id"} <= required)
        self.assertIn("allOf", schema)


if __name__ == "__main__":
    unittest.main()
