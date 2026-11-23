"""Pruebas aisladas de comparación entre proyecto y controles del catálogo."""
import unittest

from app.services.intelligence.project_protection_comparison import (
    compare_recommendations_to_catalog,
)


CONTROLS = [
    {"id": "c1", "name": "Fuerza bruta", "sensor": "Wazuh",
     "mode": "integrated", "execution_enabled": True, "execution_verified": True},
    {"id": "c5", "name": "Conexión externa sospechosa", "sensor": "Suricata",
     "mode": "integrated"},
    {"id": "c6", "name": "Posible exfiltración", "sensor": "Suricata + App",
     "mode": "simulated", "execution_enabled": False, "execution_verified": False},
    {"id": "proposal-123", "name": "Propuesta no aprobada", "mode": "pending"},
]


class ProjectProtectionComparisonTests(unittest.TestCase):
    def test_sql_never_claims_existing_direct_defense(self):
        report = compare_recommendations_to_catalog(["code:CS-CODE-03"], CONTROLS)
        entry = report["items"][0]
        self.assertEqual(entry["related_controls"], [])
        self.assertFalse(entry["direct_solution_in_catalog"])
        self.assertFalse(report["project_controls_verified"])
        self.assertFalse(report["automatic_application"])
        self.assertEqual(report["project_plan"]["mode"], "local_review_draft")
        self.assertFalse(report["project_plan"]["stored_in_database"])
        self.assertFalse(report["project_plan"]["automatic_application"])

    def test_login_monitoring_is_complementary_not_authorization(self):
        entry = compare_recommendations_to_catalog(
            ["profile:uses_authentication"], CONTROLS
        )["items"][0]
        self.assertEqual(len(entry["related_controls"]), 1)
        related = entry["related_controls"][0]
        self.assertEqual(related["id"], "c1")
        self.assertEqual(related["relationship"], "complementary")
        self.assertFalse(related["verified_for_project"])
        self.assertFalse(entry["direct_solution_in_catalog"])

    def test_sensitive_data_marks_simulation(self):
        entry = compare_recommendations_to_catalog(
            ["profile:handles_sensitive_data"], CONTROLS
        )["items"][0]
        c6 = next(c for c in entry["related_controls"] if c["id"] == "c6")
        self.assertEqual(c6["catalog_mode"], "simulated")
        self.assertFalse(c6["execution_verified_in_catalog"])
        self.assertFalse(c6["verified_for_project"])

    def test_missing_control_does_not_create_placeholder(self):
        report = compare_recommendations_to_catalog(
            ["profile:uses_authentication"], []
        )
        self.assertEqual(report["catalog_controls_total"], 0)
        self.assertEqual(report["items"][0]["related_controls"], [])

    def test_rejects_untrusted_recommendation_ids(self):
        for values in ([], ["profile:fake"], ["code:CS-CODE-03"] * 2,
                       ["code:CS-CODE-03"] * 13):
            with self.assertRaises(ValueError):
                compare_recommendations_to_catalog(values, CONTROLS)

    def test_catalog_status_does_not_mean_project_deployment(self):
        item = compare_recommendations_to_catalog(
            ["profile:uses_authentication"], CONTROLS
        )["items"][0]["related_controls"][0]
        self.assertTrue(item["execution_verified_in_catalog"])
        self.assertFalse(item["verified_for_project"])


if __name__ == "__main__":
    unittest.main()
