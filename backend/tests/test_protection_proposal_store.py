"""Almacenamiento de propuestas: pruebas sin BD real ni servicios."""
import unittest
from dataclasses import replace
from unittest.mock import MagicMock

from app.services.intelligence.protection_draft_generator import ProtectionDraft
from app.services.intelligence.protection_proposal_store import store_protection_drafts


def draft(code="T1059"):
    return ProtectionDraft(
        technique_id=code,
        technique_name="Command and Scripting Interpreter",
        title="Investigar ejecución anómala de intérpretes",
        candidate_sensor="Wazuh",
        required_evidence="Eventos de proceso",
        validation_plan="Datos sintéticos",
        priority=1,
    )


class ProposalStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    def test_creates_proposal_without_commit(self):
        self.db.execute.return_value.scalar_one_or_none.return_value = 77
        self.assertEqual(store_protection_drafts(self.db, [draft()]), 1)
        self.db.execute.assert_called_once()
        self.db.commit.assert_not_called()

    def test_existing_proposal_skipped(self):
        self.db.execute.return_value.scalar_one_or_none.return_value = None
        self.assertEqual(store_protection_drafts(self.db, [draft()]), 0)
        sql = str(self.db.execute.call_args.args[0])
        self.assertIn("ON CONFLICT (technique_id) DO NOTHING", sql)

    def test_rejects_executable_draft(self):
        for kwargs in ({"execution_allowed": True}, {"executed": True},
                       {"telemetry_verified": True}, {"detection_verified": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                store_protection_drafts(self.db, [replace(draft(), **kwargs)])
        self.db.execute.assert_not_called()

    def test_rejects_changed_status(self):
        with self.assertRaises(ValueError):
            store_protection_drafts(self.db, [replace(draft(), status="approved")])
        self.db.execute.assert_not_called()

    def test_duplicate_batch_rejected_before_insert(self):
        with self.assertRaises(ValueError):
            store_protection_drafts(self.db, [draft(), draft()])
        self.db.execute.assert_not_called()

    def test_invalid_priority_rejected(self):
        with self.assertRaises(ValueError):
            store_protection_drafts(self.db, [replace(draft(), priority=0)])
        self.db.execute.assert_not_called()

    def test_no_defensive_actions(self):
        self.db.execute.return_value.scalar_one_or_none.return_value = 7
        store_protection_drafts(self.db, [draft()])
        self.db.add.assert_not_called()
        self.db.delete.assert_not_called()
        self.db.commit.assert_not_called()

    def test_empty_batch(self):
        self.assertEqual(store_protection_drafts(self.db, []), 0)
        self.db.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
