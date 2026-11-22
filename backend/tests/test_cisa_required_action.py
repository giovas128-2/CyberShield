"""Validación de acciones CISA KEV ya importadas, sin red ni BD real."""
import unittest
from unittest.mock import MagicMock

from app.services.intelligence.threat_catalog import (
    list_documented_threats,
    split_cisa_imported_action,
)


class CisaRequiredActionTests(unittest.TestCase):
    def test_extracts_only_the_official_importer_separator(self):
        description = (
            "Product vulnerability from official feed.\n\n"
            "Acción recomendada por CISA: Apply updates per vendor instructions."
        )
        visible, action = split_cisa_imported_action(description)
        self.assertEqual(visible, "Product vulnerability from official feed.")
        self.assertEqual(action, "Apply updates per vendor instructions.")

    def test_empty_description_or_unknown_format_does_not_invent_action(self):
        self.assertEqual(split_cisa_imported_action(None), (None, None))
        self.assertEqual(split_cisa_imported_action("Legacy copy without action"), (
            "Legacy copy without action", None,
        ))
        empty = "Info\n\nAcción recomendada por CISA: "
        self.assertEqual(split_cisa_imported_action(empty), (empty, None))

    def test_handles_imported_action_with_empty_short_description(self):
        text = "\n\nAcción recomendada por CISA: Apply mitigation guidance."
        description, action = split_cisa_imported_action(text)
        self.assertIsNone(description)
        self.assertEqual(action, "Apply mitigation guidance.")

    def test_cisa_card_uses_database_only_no_controls(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = 1
        db.execute.return_value.mappings.return_value.all.return_value = [{
            "kind": "cisa",
            "external_id": "CVE-2025-12345",
            "name": "Example vulnerability",
            "description": (
                "Short official description.\n\n"
                "Acción recomendada por CISA: Follow vendor mitigations."
            ),
            "source_name": "CISA KEV",
            "source_url": "https://www.cisa.gov/",
            "source_version": "test-version",
            "documented_at": None,
            "is_subtechnique": False,
        }]
        response = list_documented_threats(db, kind="cisa", size=10)
        item = response["items"][0]
        self.assertEqual(item["description"], "Short official description.")
        self.assertEqual(item["cisa_required_action"], "Follow vendor mitigations.")
        self.assertEqual(item["cisa_action_origin"], "requiredAction del catálogo CISA KEV importado")
        self.assertFalse(item["protection_installed"])
        self.assertFalse(response["automatic_application"])
        self.assertEqual(db.execute.call_count, 2)
        db.commit.assert_not_called()

    def test_mitre_does_not_receive_cisa_action(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = 1
        db.execute.return_value.mappings.return_value.all.return_value = [{
            "kind": "mitre", "external_id": "T1110", "name": "Brute Force",
            "description": "MITRE description",
            "source_name": "MITRE ATT&CK Enterprise",
            "source_url": "https://attack.mitre.org/",
            "source_version": "test",
            "documented_at": None,
            "is_subtechnique": False,
        }]
        item = list_documented_threats(db, kind="mitre")["items"][0]
        self.assertIsNone(item["cisa_required_action"])
        self.assertIsNone(item["cisa_action_origin"])


if __name__ == "__main__":
    unittest.main()
