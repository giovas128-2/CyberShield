"""Pruebas puras del motor FIM c3, sin red ni PostgreSQL."""
import unittest

from app.services.intelligence.fim_decision_engine import assess_fim_change

CONTROL = {"mode": "integrated", "execution_enabled": False}
DETAILS = {
    "integration": "wazuh_real",
    "wazuh_alert_id": "test-fim-1",
    "wazuh_rule_id": "550",
    "path": "/opt/cybershield-lab/archivo-prueba.txt",
    "wazuh_event": "modified",
    "change_applied": True,
    "authorized": True,
    "file_criticality": "common",
}
BASE = {
    "event_type": "suspicious_file_change",
    "source": "wazuh",
    "severity": "normal",
    "details": DETAILS,
}


class FimDecisionTests(unittest.TestCase):
    def assess(self, event=None, exists=True, control=CONTROL):
        return assess_fim_change(
            event if event is not None else BASE,
            technique_exists=exists,
            control=control,
        )

    def test_authorized_change_is_observed_without_block(self):
        decision = self.assess()
        self.assertEqual(decision.status, "observed_authorized")
        self.assertEqual(decision.technique_id, "T1565.001")
        self.assertEqual(decision.control_id, "c3")
        self.assertIsNone(decision.recommended_action)
        self.assertFalse(decision.execution_allowed)
        self.assertFalse(decision.executed)

    def test_critical_change_without_authorization_requires_review(self):
        details = {**DETAILS, "authorized": False, "file_criticality": "critical"}
        decision = self.assess({**BASE, "details": details})
        self.assertEqual(decision.status, "needs_investigation")
        self.assertIsNone(decision.recommended_action)
        self.assertFalse(decision.execution_allowed)

    def test_missing_fim_evidence(self):
        for key in ("path", "wazuh_alert_id", "wazuh_event"):
            details = {k: v for k, v in DETAILS.items() if k != key}
            self.assertEqual(
                self.assess({**BASE, "details": details}).status,
                "needs_investigation",
            )

    def test_spoofed_source_not_accepted(self):
        self.assertEqual(
            self.assess({**BASE, "source": "lab"}).status,
            "needs_investigation",
        )

    def test_no_mitre_knowledge(self):
        self.assertEqual(self.assess(exists=False).status, "knowledge_missing")

    def test_no_integrated_control(self):
        self.assertEqual(
            self.assess(control={"mode": "pending"}).status,
            "control_unavailable",
        )

    def test_unrelated_event(self):
        self.assertEqual(
            self.assess({**BASE, "event_type": "privilege_escalation"}).status,
            "not_applicable",
        )


if __name__ == "__main__":
    unittest.main()
