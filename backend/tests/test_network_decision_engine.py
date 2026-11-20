"""Tests aislados de la evaluación c5. Sin conexiones ni bloqueos."""
import unittest
from app.services.intelligence.network_decision_engine import assess_suspicious_connection

CONTROL = {"mode": "integrated", "execution_enabled": False}
BASE = {
    "event_type": "suspicious_network_traffic",
    "source": "suricata",
    "severity": "high",
    "details": {
        "integration": "suricata_real",
        "suricata_event_type": "alert",
        "signature_id": 1000003,
        "destination_allowed": False,
    },
}


class NetworkDecisionTests(unittest.TestCase):
    def assess(self, event=None, exists=True, control=CONTROL):
        return assess_suspicious_connection(
            event if event is not None else BASE,
            technique_exists=exists,
            control=control,
        )

    def test_sc5_requires_review_never_executes(self):
        result = self.assess()
        self.assertEqual(result.status, "needs_investigation")
        self.assertEqual(result.control_id, "c5")
        self.assertEqual(result.technique_id, "T1041")
        self.assertIsNone(result.recommended_action)
        self.assertFalse(result.execution_allowed)
        self.assertFalse(result.executed)

    def test_other_signature_not_confirmed(self):
        event = {**BASE, "details": {**BASE["details"], "signature_id": 1000002}}
        self.assertEqual(self.assess(event).status, "needs_investigation")

    def test_flow_alone_not_confirmed(self):
        event = {**BASE, "details": {**BASE["details"], "suricata_event_type": "flow"}}
        self.assertEqual(self.assess(event).status, "needs_investigation")

    def test_untrusted_source(self):
        self.assertEqual(self.assess({**BASE, "source": "lab"}).status, "needs_investigation")

    def test_missing_mitre(self):
        self.assertEqual(self.assess(exists=False).status, "knowledge_missing")

    def test_missing_integrated_control(self):
        self.assertEqual(self.assess(control={"mode": "pending"}).status, "control_unavailable")

    def test_other_event_type(self):
        self.assertEqual(
            self.assess({**BASE, "event_type": "possible_data_exfiltration"}).status,
            "not_applicable",
        )


if __name__ == "__main__":
    unittest.main()
