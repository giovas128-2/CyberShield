"""Pruebas del evaluador sudo: nunca ejecutar ni bloquear."""
import unittest

from app.services.intelligence.privilege_decision_engine import (
    assess_sudo_privilege,
)

CONTROL = {"mode": "integrated", "execution_enabled": False}
BASE = {
    "event_type": "privilege_escalation",
    "source": "wazuh",
    "severity": "normal",
    "source_ip": None,
    "details": {
        "wazuh_rule_id": "5402",
        "sensor_confirmed_privilege": True,
        "sudo_used": True,
        "success": True,
        "authorized": True,
    },
}


class PrivilegeDecisionTests(unittest.TestCase):
    def assess(self, event=None, *, exists=True, control=CONTROL):
        return assess_sudo_privilege(
            event if event is not None else BASE,
            technique_exists=exists,
            control=control,
        )

    def test_legitimate_sudo_requires_no_block(self):
        decision = self.assess()
        self.assertEqual(decision.status, "observed_authorized")
        self.assertEqual(decision.technique_id, "T1548.003")
        self.assertEqual(decision.control_id, "c4")
        self.assertIsNone(decision.recommended_action)
        self.assertIsNone(decision.target)
        self.assertFalse(decision.executed)
        self.assertFalse(decision.execution_allowed)

    def test_unrecognized_user_needs_investigation_not_block(self):
        event = {**BASE, "details": {**BASE["details"], "authorized": False}}
        decision = self.assess(event)
        self.assertEqual(decision.status, "needs_investigation")
        self.assertIsNone(decision.recommended_action)
        self.assertFalse(decision.execution_allowed)

    def test_missing_sensor_evidence(self):
        event = {**BASE, "details": {"wazuh_rule_id": "5402", "authorized": True}}
        self.assertEqual(self.assess(event).status, "needs_investigation")

    def test_wrong_rule(self):
        event = {**BASE, "details": {**BASE["details"], "wazuh_rule_id": "5502"}}
        self.assertEqual(self.assess(event).status, "needs_investigation")

    def test_missing_knowledge_or_control(self):
        self.assertEqual(self.assess(exists=False).status, "knowledge_missing")
        self.assertEqual(
            self.assess(control={"mode": "pending"}).status,
            "control_unavailable",
        )

    def test_other_event(self):
        event = {**BASE, "event_type": "multiple_login_attempts"}
        self.assertEqual(self.assess(event).status, "not_applicable")


if __name__ == "__main__":
    unittest.main()
