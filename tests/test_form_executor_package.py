from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "form-executor"


class FormExecutorPackageTests(unittest.TestCase):
    def test_node_20_plus_is_available_to_validate_browser_tool(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required to validate the browser executor")
        result = subprocess.run([node, "--version"], check=True, capture_output=True, text=True)
        major = int(result.stdout.strip().lstrip("v").split(".", 1)[0])
        self.assertGreaterEqual(major, 20)

    def test_package_pins_playwright_and_does_not_expose_raw_mcp(self):
        package = json.loads((TOOL / "package.json").read_text())
        self.assertEqual(package["engines"]["node"], ">=20")
        self.assertEqual(package["dependencies"], {"playwright": "1.62.1"})
        self.assertNotIn("@playwright/mcp", package.get("dependencies", {}))
        self.assertNotIn("submit", package["scripts"])
        self.assertEqual(package["scripts"]["human-login"], "node src/login-cli.mjs")

    def test_node_guard_and_arg_tests_pass(self):
        node = shutil.which("node")
        result = subprocess.run(
            [
                node,
                "--test",
                str(TOOL / "test" / "guard.test.mjs"),
                str(TOOL / "test" / "args.test.mjs"),
                str(TOOL / "test" / "login.test.mjs"),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=f"Node tests failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

    def test_browser_entrypoints_parse_without_installing_playwright(self):
        node = shutil.which("node")
        for path in (
            TOOL / "src" / "inspect.mjs",
            TOOL / "src" / "cli.mjs",
            TOOL / "src" / "login.mjs",
            TOOL / "src" / "login-cli.mjs",
        ):
            result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, msg=f"node --check failed for {path}:\n{result.stderr}")

    def test_inspect_only_source_contains_no_browser_write_or_secret_export_api(self):
        source = (TOOL / "src" / "inspect.mjs").read_text()
        forbidden_patterns = {
            r"\.fill\s*\(": "Playwright fill",
            r"\.click\s*\(": "Playwright click",
            r"\.check\s*\(": "Playwright check",
            r"\.uncheck\s*\(": "Playwright uncheck",
            r"\.selectOption\s*\(": "Playwright selectOption",
            r"\.setInputFiles\s*\(": "Playwright file upload",
            r"keyboard\.press\s*\(": "keyboard press",
            r"\.cookies\s*\(": "cookie extraction",
            r"storageState\s*\(": "storage-state extraction",
            r"localStorage": "local-storage access",
            r"sessionStorage": "session-storage access",
        }
        for pattern, name in forbidden_patterns.items():
            self.assertIsNone(re.search(pattern, source), f"inspect-only source contains forbidden {name} API")

        self.assertIn("mutating_http_methods_blocked: true", source)
        self.assertIn("form_values_read: false", source)
        self.assertIn("url_query_material_exported: false", source)
        self.assertIn("cookies_read: false", source)
        self.assertIn("safeUrl", source)
        self.assertIn("UEX_INSPECT_ONLY_SUBMIT_BLOCKED", source)

    def test_human_login_source_has_no_dom_read_or_programmatic_interaction_api(self):
        source = (TOOL / "src" / "login.mjs").read_text()
        forbidden_patterns = {
            r"\.evaluate\s*\(": "DOM evaluate",
            r"\.locator\s*\(": "locator inspection",
            r"\.fill\s*\(": "fill",
            r"\.click\s*\(": "click",
            r"\.check\s*\(": "check",
            r"\.uncheck\s*\(": "uncheck",
            r"\.selectOption\s*\(": "selectOption",
            r"\.setInputFiles\s*\(": "file upload",
            r"keyboard\.": "keyboard automation",
            r"\.cookies\s*\(": "cookie extraction",
            r"storageState\s*\(": "storage state export",
            r"inputValue\s*\(": "input value read",
            r"textContent\s*\(": "text content read",
            r"innerText\s*\(": "inner text read",
            r"getAttribute\s*\(": "attribute read",
            r"localStorage": "local storage access",
            r"sessionStorage": "session storage access",
        }
        for pattern, name in forbidden_patterns.items():
            self.assertIsNone(re.search(pattern, source), f"human-login source contains forbidden {name} API")
        self.assertIn("process.stdin.isTTY", source)
        self.assertIn("confirmation !== 'DONE'", source)
        self.assertIn("headless: false", source)
        self.assertIn("launchPersistentContext", source)

    def test_browser_clis_never_emit_raw_playwright_error_content(self):
        for filename, marker in (
            ("cli.mjs", "UEX_FORM_INSPECT_ERROR"),
            ("login-cli.mjs", "UEX_HUMAN_LOGIN_ERROR"),
        ):
            source = (TOOL / "src" / filename).read_text()
            forbidden = (
                "error?.stack",
                "error.stack",
                "error?.message",
                "error.message",
                "String(error)",
                "JSON.stringify(error",
            )
            for fragment in forbidden:
                self.assertNotIn(fragment, source)
            self.assertIn(marker, source)
            self.assertIn("error?.name", source)


if __name__ == "__main__":
    unittest.main()
