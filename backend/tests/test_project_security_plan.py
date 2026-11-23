"""Pruebas del plan documental sin ejecución ni persistencia."""
import unittest

from app.services.intelligence.project_security_plan import build_security_plan


class ProjectSecurityPlanTests(unittest.TestCase):
    def test_sql_is_code_correction_without_automatic_protection(self):
        plan = build_security_plan([{
            "recommendation_id": "code:CS-CODE-03", "related_controls": [],
        }])
        item = plan["tasks"][0]
        self.assertEqual(item["action_type"], "code_correction")
        self.assertEqual(item["owner_role"], "developer")
        self.assertEqual(item["related_catalog_controls"], [])
        self.assertEqual(item["reference_url"],
                         "https://cwe.mitre.org/data/definitions/89.html")
        self.assertFalse(item["execution_allowed"])
        self.assertFalse(item["implementation_approved"])
        self.assertFalse(plan["stored_in_database"])

    def test_control_evaluation_is_not_approval_or_deployment(self):
        plan = build_security_plan([{
            "recommendation_id": "profile:uses_authentication",
            "related_controls": [{"id": "c1", "catalog_mode": "integrated"}],
        }])
        item = plan["tasks"][0]
        self.assertEqual(item["action_type"], "control_evaluation")
        self.assertEqual(item["related_catalog_controls"], ["c1"])
        self.assertFalse(item["project_deployment_verified"])
        self.assertEqual(item["status"], "draft_for_human_review")
        self.assertEqual(plan["project_protections_verified"], 0)

    def test_environment_review_does_not_invent_protection(self):
        plan = build_security_plan([{
            "recommendation_id": "profile:internet_exposed", "related_controls": [],
        }])
        self.assertEqual(plan["tasks"][0]["action_type"], "environment_review")
        self.assertEqual(plan["tasks"][0]["related_catalog_controls"], [])

    def test_untrusted_recommendations_cannot_become_tasks(self):
        for bad in ([{"recommendation_id": "profile:unknown"}],
                    [{"recommendation_id": "code:CS-CODE-999"}],
                    [{"recommendation_id": "profile:api"}] * 13,
                    []):
            with self.assertRaises(ValueError):
                build_security_plan(bad)

    def test_duplicate_ids_and_non_c1_c8_controls_rejected(self):
        with self.assertRaises(ValueError):
            build_security_plan([
                {"recommendation_id": "profile:api", "related_controls": []},
                {"recommendation_id": "profile:api", "related_controls": []},
            ])
        plan = build_security_plan([{
            "recommendation_id": "profile:handles_sensitive_data",
            "related_controls": [{"id": "proposal-malicious"}, {"id": "c5"}, {"id": "c6"}],
        }])
        self.assertEqual(
            plan["tasks"][0]["related_catalog_controls"], ["c5", "c6"]
        )

    def test_sorting_prioritizes_code_evidence_for_equal_severity(self):
        plan = build_security_plan([
            {"recommendation_id": "profile:internet_exposed", "related_controls": []},
            {"recommendation_id": "code:CS-CODE-03", "related_controls": []},
        ])
        self.assertEqual(plan["tasks"][0]["task_id"], "code:CS-CODE-03")
        self.assertEqual(plan["code_corrections"], 1)
        self.assertEqual(plan["environment_reviews"], 1)


if __name__ == "__main__":
    unittest.main()
