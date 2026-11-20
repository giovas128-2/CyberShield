"""Pruebas aisladas: la integración de Wazuh incorpora decisiones shadow.

Las pruebas NO escriben en PostgreSQL y NO invocan ejecutores.
"""
import unittest
from unittest.mock import MagicMock, patch

from app.api.integrations import receive_wazuh_event


class IntegrationShadowTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.normalized = {
            "event_type": "multiple_login_attempts",
            "source": "wazuh",
            "source_ip": "192.0.2.44",
            "server_id": 2,
            "details": {
                "wazuh_rule_id": "5763",
                "sensor_confirmed_bruteforce": True,
            },
        }
        self.stored_result = {
            "event": {**self.normalized, "severity": "high"},
            "success": True,
        }

    @patch("app.api.integrations.assess_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.validate_server")
    def test_shadow_adds_non_executable_decision(
        self, check, normalize, process, evaluate
    ):
        normalize.return_value = self.normalized
        process.return_value = self.stored_result.copy()
        decision = MagicMock()
        decision.to_dict.return_value = {
            "status": "recommendation_only",
            "execution_allowed": False,
            "executed": False,
        }
        evaluate.return_value = decision
        result = receive_wazuh_event({}, server_id=2, db=self.db)
        self.assertEqual(result["autonomous_decision"]["mode"], "shadow")
        self.assertFalse(result["autonomous_decision"]["executed"])
        evaluate.assert_called_once()

    @patch("app.api.integrations.assess_from_database", side_effect=RuntimeError("offline"))
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.validate_server")
    def test_shadow_failure_does_not_claim_defense(
        self, check, normalize, process, evaluate
    ):
        normalize.return_value = self.normalized
        process.return_value = self.stored_result.copy()
        result = receive_wazuh_event({}, server_id=2, db=self.db)
        self.assertTrue(result["success"])
        self.assertEqual(result["autonomous_decision"]["status"], "evaluation_unavailable")
        self.assertFalse(result["autonomous_decision"]["execution_allowed"])
        self.assertFalse(result["autonomous_decision"]["executed"])


if __name__ == "__main__":
    unittest.main()
