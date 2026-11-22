"""Pruebas de catálogo unificado sin red y sin PostgreSQL real."""
import unittest
from unittest.mock import MagicMock

from app.services.intelligence.threat_catalog import (
    list_documented_threats, official_record_url, search_pattern,
)


class ThreatCatalogTests(unittest.TestCase):
    def test_search_escapes_sql_wildcards(self):
        self.assertEqual(search_pattern("A!_%"), "%a!!!_!%%")
        self.assertEqual(search_pattern("T1110"), "%t1110%")

    def test_urls_only_for_valid_official_ids(self):
        self.assertEqual(
            official_record_url("mitre", "T1565.001"),
            "https://attack.mitre.org/techniques/T1565/001/",
        )
        self.assertEqual(
            official_record_url("cisa", "CVE-2025-12345"),
            "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        )
        self.assertIsNone(official_record_url("mitre", "T1110/../../"))
        self.assertIsNone(official_record_url("cisa", "non-CVE"))

    def test_does_not_write_or_execute_controls(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = 1
        db.execute.return_value.mappings.return_value.all.return_value = [
            {
                "kind": "mitre",
                "external_id": "T1110",
                "name": "Brute Force",
                "description": "Documentación de ataque",
                "source_name": "MITRE ATT&CK Enterprise",
                "source_url": "https://attack.mitre.org/",
                "source_version": "test",
                "documented_at": None,
                "is_subtechnique": False,
            }
        ]
        result = list_documented_threats(db, kind="mitre", page=2, size=5,
                                         search="T1110")
        self.assertEqual(result["total"], 1)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["automatic_application"])
        self.assertFalse(result["items"][0]["protection_installed"])
        self.assertEqual(result["items"][0]["evidence_status"],
                         "official_catalog_imported")
        self.assertEqual(db.execute.call_args_list[0].args[1]["offset"], 5)
        self.assertEqual(db.execute.call_count, 2)
        sql = " ".join(str(call.args[0]) for call in db.execute.call_args_list)
        self.assertNotIn("INSERT INTO", sql)
        self.assertNotIn("UPDATE ", sql)
        self.assertNotIn("DELETE FROM", sql)
        db.commit.assert_not_called()

    def test_invalid_filters_rejected(self):
        for kind in ("other", "mitre'; DROP TABLE", ""):
            with self.assertRaises(ValueError):
                list_documented_threats(MagicMock(), kind=kind)
        with self.assertRaises(ValueError):
            list_documented_threats(MagicMock(), size=101)


if __name__ == "__main__":
    unittest.main()
