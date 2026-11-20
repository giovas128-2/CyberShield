"""Pruebas rápidas de escaneo pasivo, sin red ni LLM."""
import unittest
from unittest.mock import patch

from app.services.intelligence.code_review import (
    scan_sources, is_allowed, explain_with_llm, github_public_files,
)

class CodeReviewTests(unittest.TestCase):
    def test_find_dynamic_execution(self):
        data = scan_sources([{"path": "app.py", "content": "value = eval(user_input)"}])
        self.assertEqual(data["files_scanned"], 1)
        self.assertEqual(data["findings"][0]["rule"], "CS-CODE-01")
        self.assertEqual(data["incidents_created"], 0)

    def test_find_tls_disabled(self):
        data = scan_sources([{"path": "api.py", "content": "requests.get(url, verify=False)"}])
        self.assertTrue(any(x["cwe"] == "CWE-295" for x in data["findings"]))

    def test_no_findings_does_not_mean_safe(self):
        data = scan_sources([{"path": "safe.py", "content": "print('hello')"}])
        self.assertEqual(data["findings_total"], 0)
        self.assertIn("preliminares", data["note"])

    def test_reject_path_traversal_and_secret_files(self):
        self.assertFalse(is_allowed("../settings.py"))
        self.assertFalse(is_allowed("settings.env"))
        self.assertFalse(is_allowed("node_modules/index.js"))

    def test_reject_large_file(self):
        with self.assertRaises(ValueError):
            scan_sources([{"path": "app.py", "content": "x" * 60001}])

    def test_no_key_falls_back_to_rules(self):
        with patch.dict("os.environ", {}, clear=True):
            value = explain_with_llm({"findings": [], "files_scanned": 1}, True)
        self.assertEqual(value["mode"], "rules_only")

    def test_reject_arbitrary_urls(self):
        with self.assertRaises(ValueError):
            github_public_files("https://example.com", "repo")

if __name__ == "__main__":
    unittest.main()
