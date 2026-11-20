"""Pruebas aisladas de la ruta Device Trust con auditoría shadow."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.api.device_trust import post_access_evaluate


class DeviceTrustShadowIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user = SimpleNamespace(id=5)
        self.access_event = SimpleNamespace(id=77)

    @patch("app.api.device_trust.save_shadow_decision", return_value=8)
    @patch("app.api.device_trust.assess_device_from_database")
    @patch("app.api.device_trust.process_security_event")
    @patch("app.api.device_trust.create_access_event")
    @patch("app.api.device_trust.evaluate_device_trust")
    def test_restricted_access_records_nonexecuting_shadow(
        self, evaluate, access, process, assess, save
    ):
        evaluate.return_value = {
            "event_type": "unauthorized_device_access",
            "decision": "restricted",
            "severity": "HIGH",
            "reason": "device_not_registered",
            "allowed": False,
            "device_id": None,
        }
        access.return_value = self.access_event
        process.return_value = {"event": {
            "id": 444, "source": "device_trust",
            "event_type": "unauthorized_device_access",
            "details": {},
        }}
        decision = SimpleNamespace(execution_allowed=False, executed=False)
        assess.return_value = decision
        result = post_access_evaluate(
            user_id=5, device_uuid="test-device-uuid",
            source_ip=None, db=self.db, current_user=self.user,
        )
        self.assertFalse(result["allowed"])
        security_event = process.call_args.args[1]
        self.assertEqual(security_event.details["access_event_id"], 77)
        self.assertEqual(security_event.details["auth_result"], "success")
        assess.assert_called_once()
        save.assert_called_once_with(self.db, 444, decision)

    @patch("app.api.device_trust.save_shadow_decision")
    @patch("app.api.device_trust.process_security_event")
    @patch("app.api.device_trust.create_access_event")
    @patch("app.api.device_trust.evaluate_device_trust")
    def test_trusted_access_does_not_create_security_event(
        self, evaluate, access, process, save
    ):
        evaluate.return_value = {
            "event_type": "device_access", "decision": "allowed",
            "severity": "NORMAL", "reason": "trusted_device",
            "allowed": True, "device_id": 2,
        }
        access.return_value = self.access_event
        result = post_access_evaluate(
            user_id=5, device_uuid="test-trusted",
            source_ip=None, db=self.db, current_user=self.user,
        )
        self.assertTrue(result["allowed"])
        process.assert_not_called()
        save.assert_not_called()

    @patch("app.api.device_trust.save_shadow_decision", side_effect=RuntimeError("offline"))
    @patch("app.api.device_trust.assess_device_from_database")
    @patch("app.api.device_trust.process_security_event")
    @patch("app.api.device_trust.create_access_event")
    @patch("app.api.device_trust.evaluate_device_trust")
    def test_shadow_failure_preserves_access_denial(
        self, evaluate, access, process, assess, save
    ):
        evaluate.return_value = {
            "event_type": "unauthorized_device_access",
            "decision": "restricted", "severity": "HIGH",
            "reason": "device_not_registered",
            "allowed": False, "device_id": None,
        }
        access.return_value = self.access_event
        process.return_value = {"event": {"id": 444}}
        assess.return_value = SimpleNamespace(
            execution_allowed=False, executed=False
        )
        result = post_access_evaluate(
            user_id=5, device_uuid="test-device",
            source_ip=None, db=self.db, current_user=self.user,
        )
        self.assertFalse(result["allowed"])
        self.db.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
