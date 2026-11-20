"""Pruebas del handler Wazuh c7 con dependencias simuladas.

No abre conexiones, no envía HTTP, no escribe en PostgreSQL y no invoca
ningún ejecutor defensivo real. El comportamiento de event_service
es intencionadamente simulado para verificar sólo el cableado c7.
"""
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api import integrations
from app.services.intelligence.defensive_decision_engine import Decision


def normalized(event_type="possible_ransomware_behavior"):
    return {
        "event_type": event_type,
        "source": "wazuh",
        "severity": "high",
        "source_ip": None,
        "details": {
            "integration": "wazuh_real",
            "sensor_confirmed_ransomware_like": True,
            "lab_ransomware_signal": True,
        },
    }


class WazuhC7HandlerTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.original = normalized()
        self.raw = {"id": "TEST-WAZUH-C7"}
        self.stored = {"id": 909090, **self.original}
        self.result = {"success": True, "event": self.stored.copy()}
        self.decision = Decision(
            status="simulation_only", reason="Solo laboratorio",
            technique_id="T1486", control_id="c7",
            recommended_action=None, target=None,
            execution_allowed=False, executed=False,
        )
        self.patchers = [
            patch.object(integrations, "validate_server"),
            patch.object(integrations, "normalize_wazuh_event", return_value=self.original.copy()),
            patch.object(integrations, "SecurityEventRequest", side_effect=lambda **data: data),
            patch.object(integrations, "process_security_event", return_value=self.result.copy()),
            patch.object(integrations, "assess_ransomware_from_database", return_value=self.decision),
            patch.object(integrations, "save_shadow_decision", return_value=9876),
            patch.object(integrations, "assess_from_database"),
            patch.object(integrations, "assess_fim_from_database"),
            patch.object(integrations, "assess_privilege_from_database"),
        ]
        self.mocks = [p.start() for p in self.patchers]
        self.addCleanup(lambda: [p.stop() for p in reversed(self.patchers)])

    def test_c7_shadow_decision_after_existing_event_processing(self):
        response = integrations.receive_wazuh_event(self.raw, server_id=2, db=self.db)
        self.mocks[3].assert_called_once()
        self.mocks[4].assert_called_once()
        self.mocks[5].assert_called_once_with(self.db, 909090, self.decision)
        self.assertEqual(response["autonomous_decision"]["mode"], "shadow")
        self.assertEqual(response["autonomous_decision"]["status"], "simulation_only")
        self.assertFalse(response["autonomous_decision"]["execution_allowed"])
        self.assertFalse(response["autonomous_decision"]["executed"])
        self.assertEqual(response["autonomous_decision"]["decision_id"], 9876)
        for m in self.mocks[6:]:
            m.assert_not_called()

    def test_missing_id_rejected_before_processing(self):
        with self.assertRaises(HTTPException) as cm:
            integrations.receive_wazuh_event({}, server_id=2, db=self.db)
        self.assertEqual(cm.exception.status_code, 422)
        self.mocks[3].assert_not_called()
        self.mocks[5].assert_not_called()

    def test_shadow_failure_not_reprocess_event(self):
        self.mocks[4].side_effect = RuntimeError("Error controlado")
        response = integrations.receive_wazuh_event(self.raw, server_id=2, db=self.db)
        self.assertEqual(response["autonomous_decision"]["status"], "evaluation_unavailable")
        self.mocks[3].assert_called_once()
        self.mocks[5].assert_not_called()
        self.db.rollback.assert_called_once()

    def test_other_wazuh_event_keeps_existing_evaluator(self):
        other = normalized("authentication_failure")
        self.mocks[1].return_value = other
        self.mocks[3].return_value = {
            "success": True, "event": {"id": 909091, **other}
        }
        self.mocks[6].return_value = self.decision
        integrations.receive_wazuh_event(self.raw, server_id=2, db=self.db)
        self.mocks[6].assert_called_once()
        self.mocks[4].assert_not_called()
        self.mocks[5].assert_called_once()


if __name__ == "__main__":
    unittest.main()
