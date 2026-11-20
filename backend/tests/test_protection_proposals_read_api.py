"""API de consulta de propuestas; no utiliza PostgreSQL ni HTTP real."""
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.api.intelligence import (
    list_protection_proposals, protection_proposal_detail, router,
)


class ProposalReadApiTests(unittest.TestCase):
    def test_listing_is_read_only_and_paginated(self):
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(scalar_one=lambda: 4),
            MagicMock(mappings=lambda: MagicMock(all=lambda: [
                {"id": 1, "technique_id": "T1059", "status": "review_required"}
            ])),
        ]
        result = list_protection_proposals(
            status="review_required", page=1, size=20, db=db,
            _reviewer=object(),
        )
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["items"][0]["technique_id"], "T1059")
        self.assertTrue(result["read_only"])
        self.assertEqual(db.execute.call_count, 2)
        self.assertEqual(db.execute.call_args_list[1].args[1]["status"],
                         "review_required")
        db.commit.assert_not_called()

    def test_invalid_status_no_query(self):
        db = MagicMock()
        with self.assertRaises(HTTPException) as exc:
            list_protection_proposals(
                status="approved", page=1, size=20, db=db, _reviewer=object()
            )
        self.assertEqual(exc.exception.status_code, 422)
        db.execute.assert_not_called()

    def test_detail_found(self):
        db = MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value = {
            "id": 2, "technique_id": "T1001.003"
        }
        result = protection_proposal_detail(
            proposal_id=2, db=db, _reviewer=object()
        )
        self.assertEqual(result["technique_id"], "T1001.003")
        db.commit.assert_not_called()

    def test_detail_not_found(self):
        db = MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value = None
        with self.assertRaises(HTTPException) as exc:
            protection_proposal_detail(
                proposal_id=999, db=db, _reviewer=object()
            )
        self.assertEqual(exc.exception.status_code, 404)

    def test_invalid_id_no_query(self):
        db = MagicMock()
        with self.assertRaises(HTTPException) as exc:
            protection_proposal_detail(
                proposal_id=0, db=db, _reviewer=object()
            )
        self.assertEqual(exc.exception.status_code, 422)
        db.execute.assert_not_called()

    def test_routes_are_get_only_and_have_auth_dependencies(self):
        routes = [
            r for r in router.routes if "/protection-proposals" in r.path
        ]
        self.assertEqual(len(routes), 2)
        self.assertTrue(all(r.methods == {"GET"} for r in routes))
        for route in routes:
            dependency_names = [
                getattr(item.call, "__name__", "")
                for item in route.dependant.dependencies
            ]
            self.assertIn("get_current_user", dependency_names)
            self.assertIn("check_role", dependency_names)


if __name__ == "__main__":
    unittest.main()
