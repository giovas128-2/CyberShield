"""Regresión c8 en receptor Wazuh con mocks, sin HTTP ni PostgreSQL.

Se reemplaza process_security_event para NO crear eventos ni acciones.
"""
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api import integrations
from app.services.intelligence.defensive_decision_engine import Decision


def normalized(event_type="possible_lateral_movement"):
    return {
        "event_type": event_type,
        "source": "wazuh",
        "severity": "high",
        "source_ip": "192.0.2.10",
        "details": {
            "integration": "wazuh_real",
            "wazuh_rule_id": "100210",
            "protocol": "ssh",
            "login_successful": True,
            "sensor_confirmed_lateral": True,
            "srcip": "192.0.2.10",
            "destination_user": "lateral_demo",
        },
    }


class WazuhC8HandlerTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.raw = {"id": "TEST-WAZUH-C8"}
        self.normalized = normalized()
        self.stored = {"id": 818181, **self.normalized}
        self.decision = Decision(
            status="simulation_only",
            technique_id="T1021.004",
            control_id="c8",
            reason="Solo escenario SSH de laboratorio",
            recommended_action=None,
            target=None,
            execution_allowed=False,
            executed=False,
        )
        items = [
            patch.object(integrations, "validate_server"),
            patch.object(integrations, "normalize_wazuh_event",
                         return_value=self.normalized.copy()),
            patch.object(integrations, "SecurityEventRequest",
                         side_effect=lambda **kw: kw),
            patch.object(integrations, "process_security_event",
                         side_effect=lambda db, event: {
                             "success": True,
                             "event": {"id": 818181, **event},
                         }),
            patch.object(integrations, "assess_lateral_from_database",
                         return_value=self.decision),
            patch.object(integrations, "save_shadow_decision", return_value=101),
            patch.object(integrations, "assess_ransomware_from_database"),
            patch.object(integrations, "assess_from_database"),
        ]
        self.mocks = [p.start() for p in items]
        self.addCleanup(lambda: [p.stop() for p in reversed(items)])

    def test_c8_shadow_after_existing_processing(self):
        result = integrations.receive_wazuh_event(
            self.raw, server_id=2, db=self.db
        )
        self.mocks[3].assert_called_once()
        self.mocks[4].assert_called_once()
        self.mocks[5].assert_called_once_with(self.db, 818181, self.decision)
        self.assertEqual(result["autonomous_decision"]["mode"], "shadow")
        self.assertEqual(result["autonomous_decision"]["control_id"], "c8")
        self.assertFalse(result["autonomous_decision"]["execution_allowed"])
        self.assertFalse(result["autonomous_decision"]["executed"])
        self.mocks[6].assert_not_called()
        self.mocks[7].assert_not_called()

    def test_id_required_before_processing(self):
        with self.assertRaises(HTTPException) as cm:
            integrations.receive_wazuh_event({}, server_id=2, db=self.db)
        self.assertEqual(cm.exception.status_code, 422)
        self.mocks[3].assert_not_called()
        self.mocks[4].assert_not_called()

    def test_other_event_uses_existing_evaluator(self):
        other = normalized("authentication_failure")
        self.mocks[1].return_value = other
        self.mocks[7].return_value = self.decision
        integrations.receive_wazuh_event(self.raw, server_id=2, db=self.db)
        self.mocks[7].assert_called_once()
        self.mocks[4].assert_not_called()

    def test_shadow_failure_cannot_reprocess(self):
        self.mocks[4].side_effect = RuntimeError("fallo de prueba c8")
        with patch.object(integrations.logger, "exception"):
            result = integrations.receive_wazuh_event(
                self.raw, server_id=2, db=self.db
            )
        self.assertEqual(
            result["autonomous_decision"]["status"],
            "evaluation_unavailable",
        )
        self.db.rollback.assert_called_once()
        self.mocks[3].assert_called_once()
        self.mocks[5].assert_not_called()


if __name__ == "__main__":
    unittest.main()
