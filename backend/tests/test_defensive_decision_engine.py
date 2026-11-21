"""Tests sin red ni base de datos para el primer evaluador autónomo."""
import unittest

from app.services.intelligence.defensive_decision_engine import assess_ssh_bruteforce

BASE = {
    "event_type": "authentication_burst",
    "severity": "high",
    "source": "wazuh",
    "source_ip": "192.0.2.44",
    "details": {
        "sensor_confirmed_bruteforce": True,
        "wazuh_rule_id": "5763",
    },
}
CONTROL = {"mode": "integrated", "execution_enabled": False, "execution_verified": False}


class DecisionEngineTests(unittest.TestCase):
    def decision(self, event=None, control=CONTROL, exists=True):
        return assess_ssh_bruteforce(
            event if event is not None else BASE,
            technique_exists=exists,
            control=control,
        )

    def test_confirmed_recommends_but_never_executes(self):
        result = self.decision()
        self.assertEqual(result.status, "recommendation_only")
        self.assertEqual(result.recommended_action, "BLOCK_SOURCE_IP")
        self.assertFalse(result.executed)
        self.assertFalse(result.execution_allowed)

    def test_forged_or_missing_evidence_not_trusted(self):
        for details in ({}, {"wazuh_rule_id": "5763"}, {"sensor_confirmed_bruteforce": True}):
            event = {**BASE, "details": details}
            self.assertEqual(self.decision(event).status, "needs_investigation")

    def test_allowlist_always_wins(self):
        event = {**BASE, "details": {**BASE["details"], "allowlisted": True}}
        self.assertEqual(self.decision(event).status, "excluded")

    def test_missing_knowledge(self):
        self.assertEqual(self.decision(exists=False).status, "knowledge_missing")

    def test_pending_control_cannot_run(self):
        self.assertEqual(self.decision(control={"mode": "pending"}).status, "control_unavailable")

    def test_even_enabled_flags_do_not_authorize_execution(self):
        result = self.decision(control={
            "mode": "integrated", "execution_enabled": True,
            "execution_verified": True,
        })
        self.assertFalse(result.execution_allowed)
        self.assertFalse(result.executed)

    def test_loopback_never_blocked(self):
        event = {**BASE, "source_ip": "127.0.0.1"}
        self.assertEqual(self.decision(event).status, "needs_investigation")

    def test_unrelated_event_not_applicable(self):
        event = {**BASE, "event_type": "suspicious_file_change"}
        self.assertEqual(self.decision(event).status, "not_applicable")


if __name__ == "__main__":
    unittest.main()
