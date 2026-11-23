"""Pruebas de bandeja: no migración automática ni despliegue de controles."""
import unittest
from unittest.mock import MagicMock, patch

from app.services.intelligence import project_plan_store as store


class ProjectPlanStoreTests(unittest.TestCase):
    def test_no_db_schema_gives_explicit_unavailable(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = False
        with self.assertRaises(store.PlanStoreMissing):
            store.require_plan_tables(db)
        db.commit.assert_not_called()

    def test_invalid_user_cannot_create_plan(self):
        db = MagicMock()
        with self.assertRaises(ValueError):
            store.create_plan(db, 0, "Tienda", ["code:CS-CODE-03"])
        db.execute.assert_not_called()

    def test_empty_project_name_cannot_create_plan(self):
        db = MagicMock()
        with self.assertRaises(ValueError):
            store.create_plan(db, 1, "   ", ["code:CS-CODE-03"])
        db.execute.assert_not_called()

    def test_save_uses_server_generated_tasks_only(self):
        db = MagicMock()
        # to_regclass result, INSERT plan result and INSERT task.
        inserted = {"id": 12, "project_name": "Inventario", "created_by": 1,
                    "created_at": "2026-11-23"}
        db.execute.return_value.scalar_one.return_value = True
        db.execute.return_value.mappings.return_value.one.return_value = inserted
        with patch.object(store, "list_protections", return_value=[]):
            result = store.create_plan(
                db, 1, "Inventario", ["code:CS-CODE-03"]
            )
        self.assertTrue(result["stored_in_database"])
        self.assertFalse(result["implementation_approved"])
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(result["tasks_total"], 1)
        self.assertEqual(db.commit.call_count, 1)
        sql = " ".join(str(call.args[0]) for call in db.execute.call_args_list)
        self.assertNotIn("UPDATE cybershield_protection_catalog", sql)
        self.assertNotIn("response_actions", sql)
        self.assertIn("cybershield_project_review_tasks", sql)

    def test_no_approval_from_pending_to_planned(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = True
        db.execute.return_value.mappings.return_value.first.return_value = {
            "id": 23, "plan_id": 12, "recommendation_id": "code:CS-CODE-03",
            "status": "review_required"
        }
        with self.assertRaises(store.PlanConflict):
            store.review_task(db, 12, 23, 1, "planned", "Revisión técnica pendiente")
        db.commit.assert_not_called()
        db.rollback.assert_called_once()

    def test_rejection_is_terminal(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = True
        db.execute.return_value.mappings.return_value.first.return_value = {
            "id": 23, "plan_id": 12, "recommendation_id": "code:CS-CODE-03",
            "status": "rejected"
        }
        with self.assertRaises(store.PlanConflict):
            store.review_task(db, 12, 23, 1, "under_review", "Intento de reversión")
        db.commit.assert_not_called()

    def test_review_writes_audit_in_same_transaction(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = True
        db.execute.return_value.mappings.return_value.first.side_effect = [
            {"id": 23, "plan_id": 12, "recommendation_id": "code:CS-CODE-03",
             "status": "under_review"},
            {"id": 23, "plan_id": 12, "recommendation_id": "code:CS-CODE-03",
             "status": "planned", "reviewed_by": 1, "review_notes": "Validado",
             "reviewed_at": "2026-11-23"},
        ]
        result = store.review_task(
            db, 12, 23, 1, "planned", "Evaluación técnica completa"
        )
        self.assertTrue(result["history_recorded"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["implementation_approved"])
        db.commit.assert_called_once()
        sql = " ".join(str(call.args[0]) for call in db.execute.call_args_list)
        self.assertIn("cybershield_project_review_history", sql)
        self.assertNotIn("cybershield_protection_catalog", sql)

    def test_notes_must_have_substantive_review(self):
        with self.assertRaises(ValueError):
            store.review_task(MagicMock(), 12, 23, 1, "rejected", "ok")


if __name__ == "__main__":
    unittest.main()
