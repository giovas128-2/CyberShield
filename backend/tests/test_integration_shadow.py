"""Pruebas aisladas: la integración de Wazuh incorpora decisiones shadow.

Las pruebas NO escriben en PostgreSQL y NO invocan ejecutores.
"""
import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError

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
            "event": {**self.normalized, "id": 847, "severity": "high"},
            "success": True,
        }

    @patch("app.api.integrations.save_shadow_decision", return_value=23)
    @patch("app.api.integrations.assess_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.validate_server")
    def test_shadow_adds_non_executable_decision(
        self, check, normalize, process, evaluate, store
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
        result = receive_wazuh_event({"id": "test-alert-001"}, server_id=2, db=self.db)
        self.assertEqual(result["autonomous_decision"]["mode"], "shadow")
        self.assertFalse(result["autonomous_decision"]["executed"])
        evaluate.assert_called_once()
        store.assert_called_once()
        self.assertEqual(result["autonomous_decision"]["decision_id"], 23)

    @patch("app.api.integrations.assess_from_database", side_effect=RuntimeError("offline"))
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.validate_server")
    def test_shadow_failure_does_not_claim_defense(
        self, check, normalize, process, evaluate
    ):
        normalize.return_value = self.normalized
        process.return_value = self.stored_result.copy()
        result = receive_wazuh_event({"id": "test-alert-001"}, server_id=2, db=self.db)
        self.assertTrue(result["success"])
        self.assertEqual(result["autonomous_decision"]["status"], "evaluation_unavailable")
        self.assertFalse(result["autonomous_decision"]["execution_allowed"])
        self.assertFalse(result["autonomous_decision"]["executed"])

    @patch("app.api.integrations.save_shadow_decision", return_value=31)
    @patch("app.api.integrations.assess_privilege_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.validate_server")
    def test_sudo_shadow_persists_without_action(
        self, check, normalize, process, assess, store
    ):
        normalized = {
            **self.normalized,
            "event_type": "privilege_escalation",
            "source_ip": None,
            "details": {
                "wazuh_rule_id": "5402",
                "sensor_confirmed_privilege": True,
                "sudo_used": True,
                "success": True,
                "authorized": True,
            },
        }
        normalize.return_value = normalized
        process.return_value = {
            "event": {**normalized, "id": 39327, "severity": "normal"},
            "success": True,
        }
        decision = MagicMock()
        decision.to_dict.return_value = {
            "status": "observed_authorized",
            "technique_id": "T1548.003",
            "recommended_action": None,
            "execution_allowed": False,
            "executed": False,
        }
        assess.return_value = decision
        result = receive_wazuh_event(
            {"id": "test-sudo-5402"}, server_id=2, db=self.db
        )
        self.assertEqual(result["autonomous_decision"]["status"], "observed_authorized")
        self.assertEqual(result["autonomous_decision"]["decision_id"], 31)
        self.assertIsNone(result["autonomous_decision"]["recommended_action"])
        assess.assert_called_once()
        store.assert_called_once_with(self.db, 39327, decision)

    @patch("app.api.integrations.save_shadow_decision", return_value=44)
    @patch("app.api.integrations.assess_fim_from_database")
    @patch("app.api.integrations.process_security_event")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.validate_server")
    def test_fim_shadow_persists_without_action(
        self, check, normalize, process, assess, store
    ):
        normalized = {
            **self.normalized,
            "event_type": "suspicious_file_change",
            "source_ip": None,
            "details": {
                "integration": "wazuh_real",
                "wazuh_rule_id": "550",
                "path": "/opt/cybershield-lab/archivo-prueba.txt",
                "wazuh_event": "modified",
                "change_applied": True,
                "authorized": True,
                "file_criticality": "common",
            },
        }
        normalize.return_value = normalized
        process.return_value = {
            "event": {**normalized, "id": 39340, "severity": "normal"},
            "success": True,
        }
        decision = MagicMock()
        decision.to_dict.return_value = {
            "status": "observed_authorized",
            "technique_id": "T1565.001",
            "recommended_action": None,
            "execution_allowed": False,
            "executed": False,
        }
        assess.return_value = decision
        result = receive_wazuh_event(
            {"id": "test-fim-540"}, server_id=2, db=self.db
        )
        self.assertEqual(result["autonomous_decision"]["decision_id"], 44)
        self.assertEqual(result["autonomous_decision"]["status"], "observed_authorized")
        self.assertFalse(result["autonomous_decision"]["execution_allowed"])
        assess.assert_called_once()
        store.assert_called_once_with(self.db, 39340, decision)

    @patch("app.api.integrations.validate_server")
    def test_missing_wazuh_alert_id_is_rejected(self, check):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            receive_wazuh_event({}, server_id=2, db=self.db)
        self.assertEqual(context.exception.status_code, 422)

    @patch("app.api.integrations.validate_server")
    @patch("app.api.integrations.normalize_wazuh_event")
    @patch("app.api.integrations.process_security_event")
    def test_duplicate_is_acknowledged_without_new_processing(
        self, process, normalize, check
    ):
        class FakeDiag:
            constraint_name = "ux_events_wazuh_alert_id"

        class FakeDatabaseError(Exception):
            diag = FakeDiag()

        normalize.return_value = self.normalized
        process.side_effect = IntegrityError("INSERT", {}, FakeDatabaseError())
        self.db.execute.return_value.scalar_one_or_none.return_value = 39318

        result = receive_wazuh_event(
            {"id": "1795141364.258252"}, server_id=1, db=self.db,
        )
        self.assertTrue(result["duplicate"])
        self.assertEqual(result["event"]["id"], 39318)
        self.assertEqual(result["autonomous_decision"]["status"], "already_processed")
        self.db.rollback.assert_called_once()



if __name__ == "__main__":
    unittest.main()
