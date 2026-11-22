"""Pruebas sin PostgreSQL real: reporte documental MITRE de solo lectura."""
import unittest
from unittest.mock import MagicMock

from app.services.intelligence.technique_research import build_documentary_report


class TechniqueResearchTests(unittest.TestCase):
    def test_report_is_read_only_and_not_ai(self):
        db = MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value = {
            "attack_id": "T1110", "name": "Brute Force",
            "description": "MITRE definition", "source_version": "bundle-test",
            "modified_at": None,
        }
        db.execute.return_value.mappings.return_value.all.return_value = [
            {"mitigation_id": "M1032", "name": "Multi-factor Authentication"}
        ]
        result = build_documentary_report(db, "t1110")
        self.assertEqual(result["attack_id"], "T1110")
        self.assertEqual(result["mitigation_count"], 1)
        self.assertFalse(result["automatic_application"])
        self.assertFalse(result["executable_controls_verified"])
        self.assertTrue(result["needs_human_review"])
        self.assertEqual(result["mode"], "documental_sin_ia_generativa")
        self.assertEqual(db.execute.call_count, 2)
        statements = " ".join(str(x.args[0]) for x in db.execute.call_args_list).upper()
        for forbidden in ("INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE"):
            self.assertNotIn(forbidden, statements)
        db.commit.assert_not_called()

    def test_missing_technique_is_not_invented(self):
        db = MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value = None
        with self.assertRaises(LookupError):
            build_documentary_report(db, "T9999")

    def test_rejects_invalid_attack_id_before_database(self):
        db = MagicMock()
        for invalid in ("T1110/../", "CVE-2025-1234", "T1110;SELECT 1"):
            with self.assertRaises(ValueError):
                build_documentary_report(db, invalid)
        db.execute.assert_not_called()

    def test_zero_mitigations_does_not_claim_protection(self):
        db = MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value = {
            "attack_id": "T1001.001", "name": "Junk Data",
            "description": "MITRE definition", "source_version": "test",
            "modified_at": None,
        }
        db.execute.return_value.mappings.return_value.all.return_value = []
        result = build_documentary_report(db, "T1001.001")
        self.assertEqual(result["mitigations"], [])
        self.assertEqual(result["reference_url"], "https://attack.mitre.org/techniques/T1001/001/")
        self.assertIn("0 mitigación(es)", result["summary_es"])


if __name__ == "__main__":
    unittest.main()
