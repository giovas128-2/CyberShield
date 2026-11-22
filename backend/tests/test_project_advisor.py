"""Pruebas aisladas de propuestas contextuales, sin ejecutar proyectos."""
import unittest

from app.services.intelligence.project_advisor import project_advice


class ProjectAdvisorTests(unittest.TestCase):
    def test_requires_concrete_pattern_to_label_code_evidence(self):
        scan = {"files_scanned": 2, "findings": [{
            "rule": "CS-CODE-03", "file": "api/db.py", "line": 35,
            "cwe": "CWE-89", "severity": "high",
        }]}
        result = project_advice(scan, ["api/db.py", "client/main.tsx"], {
            "name": "Inventario", "description": "Aplicación de inventario",
            "project_type": "web", "uses_authentication": True,
        })
        self.assertEqual(result["project"]["name"], "Inventario")
        self.assertIn("Python", [r["name"] for r in result["project"]["languages_observed"]])
        rule = next(r for r in result["recommendations"] if r["id"] == "code:CS-CODE-03")
        self.assertEqual(rule["origin"], "code_pattern")
        self.assertEqual(rule["evidence"][0]["file"], "api/db.py")
        self.assertEqual(rule["evidence"][0]["line"], 35)
        self.assertEqual(rule["evidence_status"], "requires_human_verification")
        self.assertFalse(result["automatic_application"])

    def test_user_context_is_not_a_detected_vulnerability(self):
        result = project_advice({"files_scanned": 1, "findings": []}, ["app.php"], {
            "internet_exposed": True, "handles_sensitive_data": True,
        })
        self.assertTrue(result["recommendations"])
        self.assertTrue(all(r["origin"] == "user_declared" for r in result["recommendations"]))
        self.assertTrue(all(r["evidence"] == [] for r in result["recommendations"]))
        self.assertTrue(all(r["evidence_status"] == "not_verified_in_code" for r in result["recommendations"]))

    def test_no_context_no_findings_does_not_invent_recommendations(self):
        result = project_advice({"files_scanned": 1, "findings": []}, ["setup.sql"])
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(result["project"]["languages_observed"][0]["name"], "SQL")

    def test_unknown_rule_cannot_generate_fake_specific_advice(self):
        result = project_advice({"files_scanned": 1, "findings": [{
            "rule": "CS-AI-REVIEW", "file": "app.js", "line": 1,
        }]}, ["app.js"])
        self.assertEqual(result["recommendations"], [])

    def test_does_not_expose_source_code_or_secrets_in_recommendations(self):
        result = project_advice({"files_scanned": 1, "findings": [{
            "rule": "CS-CODE-06", "file": "backend/settings.py", "line": 7,
            "content": "secret_key='not-for-the-result'",
        }]}, ["backend/settings.py"])
        self.assertNotIn("not-for-the-result", str(result))
        self.assertFalse(result["protection_installed"])
        self.assertEqual(result["recommendations"][0]["reference_url"],
                         "https://cwe.mitre.org/data/definitions/798.html")


if __name__ == "__main__":
    unittest.main()
