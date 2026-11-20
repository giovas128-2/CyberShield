"""Verificación aislada integración c5 Suricata. No escribe PostgreSQL."""
import unittest
from unittest.mock import MagicMock, patch
from app.api.integrations import receive_suricata_event


class SuricataShadowTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.normalized = {
            "event_type": "suspicious_network_traffic",
            "source": "suricata",
            "source_ip": "192.0.2.15",
            "server_id": 2,
            "details": {
                "integration": "suricata_real",
                "suricata_event_type": "alert",
                "signature_id": 1000003,
                "destination_allowed": False,
            },
        }

    @patch("app.api.integrations.save_shadow_decision", return_value=99)
    @patch("app.api.integrations.assess_connection_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_suricata_event")
    @patch("app.api.integrations.validate_server")
    def test_sc5_persists_shadow_without_action(
        self, check, normalize, process, assess, store
    ):
        normalize.return_value = self.normalized
        process.return_value = {"event": {
            **self.normalized, "id": 40001, "severity": "high",
        }}
        decision = MagicMock()
        decision.to_dict.return_value = {
            "status": "needs_investigation",
            "recommended_action": None,
            "execution_allowed": False,
            "executed": False,
        }
        assess.return_value = decision
        result = receive_suricata_event({}, server_id=2, db=self.db)
        self.assertEqual(result["autonomous_decision"]["decision_id"], 99)
        self.assertFalse(result["autonomous_decision"]["executed"])
        store.assert_called_once_with(self.db, 40001, decision)

    @patch("app.api.integrations.save_shadow_decision")
    @patch("app.api.integrations.assess_connection_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_suricata_event")
    @patch("app.api.integrations.validate_server")
    def test_c6_does_not_run_c5_evaluator(
        self, check, normalize, process, assess, store
    ):
        normalize.return_value = {
            **self.normalized, "event_type": "possible_data_exfiltration",
            "details": {
                "integration": "suricata_real",
                "signature_id": 1000002,
            },
        }
        process.return_value = {"event": {"id": 40002}}
        receive_suricata_event({}, server_id=2, db=self.db)
        assess.assert_not_called()
        store.assert_not_called()

    @patch("app.api.integrations.save_shadow_decision")
    @patch("app.api.integrations.assess_connection_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_suricata_event")
    @patch("app.api.integrations.validate_server")
    def test_general_network_alert_does_not_run_c5(
        self, check, normalize, process, assess, store
    ):
        normalize.return_value = {
            **self.normalized, "details": {
                **self.normalized["details"], "signature_id": 2016150,
            },
        }
        process.return_value = {"event": {"id": 40003}}
        receive_suricata_event({}, server_id=2, db=self.db)
        assess.assert_not_called()
        store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
