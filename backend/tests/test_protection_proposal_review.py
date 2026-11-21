"""Regresión del endpoint de revisión; mocks sin escrituras reales."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException
from pydantic import ValidationError

from app.api.intelligence import (
    ProposalReviewRequest,
    review_protection_proposal,
    router,
)


def payload(status="under_review", notes="Se requiere evidencia adicional"):
    return ProposalReviewRequest(status=status, notes=notes)


class ProposalReviewTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.reviewer = SimpleNamespace(id=3, role="engineer")
        self.db.execute.return_value.mappings.return_value.first.return_value = {
            "id": 1, "technique_id": "T1059", "status": "under_review",
            "review_notes": "Se requiere evidencia adicional",
            "reviewed_by": "3", "reviewed_at": None,
            "execution_allowed": False, "executed": False,
        }

    def run_review(self, proposal_id=1, request=None, reviewer=None):
        return review_protection_proposal(
            proposal_id=proposal_id,
            payload=request or payload(),
            db=self.db,
            reviewer=reviewer or self.reviewer,
        )

    def test_review_status_and_notes_commit(self):
        result = self.run_review()
        self.assertTrue(result["success"])
        self.assertEqual(result["proposal"]["status"], "under_review")
        self.assertFalse(result["execution_allowed"])
        self.db.commit.assert_called_once()
        sql = str(self.db.execute.call_args.args[0])
        self.assertIn("status IN ('review_required', 'under_review')", sql)
        self.assertNotIn("cybershield_protection_catalog", sql)
        self.assertNotIn("response_actions", sql)

    def test_reject_allowed_no_activation(self):
        response = self.run_review(request=payload("rejected", "No hay telemetría suficiente"))
        self.assertFalse(response["executed"])

    def test_unsupported_status_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            payload("approved", "Intento de aprobación automática")
        self.db.execute.assert_not_called()

    def test_short_notes(self):
        with self.assertRaises(HTTPException) as err:
            self.run_review(request=payload(notes="          "))
        self.assertEqual(err.exception.status_code, 422)
        self.db.execute.assert_not_called()

    def test_invalid_id(self):
        with self.assertRaises(HTTPException) as err:
            self.run_review(proposal_id=0)
        self.assertEqual(err.exception.status_code, 422)
        self.db.execute.assert_not_called()

    def test_invalid_actor(self):
        with self.assertRaises(HTTPException) as err:
            self.run_review(reviewer=SimpleNamespace(id=None))
        self.assertEqual(err.exception.status_code, 403)
        self.db.execute.assert_not_called()

    def test_missing_proposal(self):
        self.db.execute.side_effect = [
            MagicMock(mappings=lambda: MagicMock(first=lambda: None)),
            MagicMock(scalar_one_or_none=lambda: None),
        ]
        with self.assertRaises(HTTPException) as err:
            self.run_review()
        self.assertEqual(err.exception.status_code, 404)
        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_terminal_proposal_conflict(self):
        self.db.execute.side_effect = [
            MagicMock(mappings=lambda: MagicMock(first=lambda: None)),
            MagicMock(scalar_one_or_none=lambda: "rejected"),
        ]
        with self.assertRaises(HTTPException) as err:
            self.run_review()
        self.assertEqual(err.exception.status_code, 409)
        self.db.commit.assert_not_called()

    def test_commit_failure_rolls_back(self):
        self.db.commit.side_effect = RuntimeError("db unavailable")
        with self.assertRaises(RuntimeError):
            self.run_review()
        self.db.rollback.assert_called_once()

    def test_review_route_secured(self):
        routes = [r for r in router.routes if r.path.endswith("/review")]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].methods, {"PATCH"})
        dependencies = [
            getattr(d.call, "__name__", "") for d in routes[0].dependant.dependencies
        ]
        self.assertIn("get_current_user", dependencies)
        self.assertIn("check_role", dependencies)


if __name__ == "__main__":
    unittest.main()
