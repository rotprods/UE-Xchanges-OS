import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_bootstrap_watchdog.py"


def load_script():
    spec = importlib.util.spec_from_file_location("run_bootstrap_watchdog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def audit_report(*, violation=True):
    findings = []
    if violation:
        findings.append(
            {
                "subject_type": "lease",
                "subject_id": "LSE-1",
                "session_id": "SES-1",
                "allowed": False,
                "codes": ["MISSING_BOOTSTRAP_ACK"],
            }
        )
    return {
        "contract": "UEX_BOOTSTRAP_COMPLIANCE_AUDIT",
        "manifest_version": "1.0.0",
        "observed_main_sha": "a" * 40,
        "now": "2026-09-02T09:00:00+02:00",
        "findings": findings,
    }


class BootstrapWatchdogCliTests(unittest.TestCase):
    def test_build_report_preserves_source_metadata(self):
        module = load_script()
        report, encoded = module.build_report(audit_report())
        self.assertFalse(report.healthy)
        self.assertEqual(encoded["source_manifest_version"], "1.0.0")
        self.assertEqual(encoded["source_main_sha"], "a" * 40)

    def test_bad_contract_rejected(self):
        module = load_script()
        with self.assertRaises(ValueError):
            module.build_report({"contract": "WRONG", "findings": []})

    def test_fail_on_high_exit_code_and_state_write(self):
        module = load_script()
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.json"
            state = Path(tmp) / "state.json"
            audit.write_text(json.dumps(audit_report()), encoding="utf-8")
            code = module.main([
                str(audit),
                "--write-state",
                str(state),
                "--fail-on-high",
            ])
            self.assertEqual(code, 2)
            saved = json.loads(state.read_text(encoding="utf-8"))
            self.assertIn("lease:LSE-1", saved)

    def test_clean_report_exits_zero(self):
        module = load_script()
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.json"
            audit.write_text(json.dumps(audit_report(violation=False)), encoding="utf-8")
            self.assertEqual(module.main([str(audit), "--fail-on-high"]), 0)

    def test_report_schema_present(self):
        schema = json.loads((ROOT / "schemas" / "bootstrap-watchdog-report.schema.json").read_text())
        self.assertEqual(schema["properties"]["contract"]["const"], "UEX_BOOTSTRAP_COMPLIANCE_WATCHDOG")
        self.assertIn("alerts", schema["required"])


if __name__ == "__main__":
    unittest.main()
