"""Pruebas aisladas del evaluador c6; sin red, BD real ni acciones."""
import unittest

from app.services.intelligence.exfiltration_decision_engine import assess_exfiltration

CONTROL = {"mode": "simulated", "execution_enabled": False}
DETAILS = {
    "integration": "suricata_real",
    "sensor_confirmed_exfiltration": True,
    "lab_exfiltration_signal": True,
    "dest_ip": "172.25.176.1",
    "dest_port": 8765,
    "suricata_event_type": "alert",
    "signature_id": 1000002,
    "bulk_data_access": True,
}
EVENT = {
    "event_type": "possible_data_exfiltration",
    "source": "suricata",
    "severity": "warning",
    "details": DETAILS,
}


class ExfiltrationDecisionTests(unittest.TestCase):
    def assess(self, event=None, exists=True, control=CONTROL):
        return assess_exfiltration(
            event if event is not None else EVENT,
            technique_exists=exists,
            control=control,
        )

    def test_historical_alert_is_simulation_only(self):
        result = self.assess()
        self.assertEqual(result.status, "simulation_only")
        self.assertEqual(result.control_id, "c6")
        self.assertEqual(result.technique_id, "T1041")
        self.assertIsNone(result.recommended_action)
        self.assertFalse(result.execution_allowed)
        self.assertFalse(result.executed)

    def test_historical_flow_above_threshold(self):
        details = {
            **DETAILS, "suricata_event_type": "flow",
            "signature_id": None, "bytes_toserver_total": 10_000_000,
        }
        self.assertEqual(
            self.assess({**EVENT, "details": details}).status, "simulation_only"
        )

    def test_flow_below_threshold(self):
        details = {
            **DETAILS, "suricata_event_type": "flow",
            "signature_id": None, "bytes_toserver_total": 9_999_999,
        }
        self.assertEqual(
            self.assess({**EVENT, "details": details}).status, "needs_investigation"
        )

    def test_no_sensor_proof(self):
        details = {**DETAILS, "sensor_confirmed_exfiltration": False}
        self.assertEqual(
            self.assess({**EVENT, "details": details}).status, "needs_investigation"
        )

    def test_wrong_destination(self):
        details = {**DETAILS, "dest_ip": "198.51.100.1"}
        self.assertEqual(
            self.assess({**EVENT, "details": details}).status, "needs_investigation"
        )

    def test_untrusted_source(self):
        self.assertEqual(
            self.assess({**EVENT, "source": "lab"}).status, "needs_investigation"
        )

    def test_not_applicable_for_sc5(self):
        self.assertEqual(
            self.assess({**EVENT, "event_type": "suspicious_network_traffic"}).status,
            "not_applicable",
        )

    def test_missing_mitre(self):
        self.assertEqual(self.assess(exists=False).status, "knowledge_missing")

    def test_no_control(self):
        self.assertEqual(self.assess(control=None).status, "control_unavailable")

    def test_integrated_needs_review(self):
        result = self.assess(control={"mode": "integrated"})
        self.assertEqual(result.status, "needs_investigation")
        self.assertFalse(result.execution_allowed)

    def test_unsigned_or_other_alert(self):
        details = {**DETAILS, "signature_id": 2016150}
        self.assertEqual(
            self.assess({**EVENT, "details": details}).status, "needs_investigation"
        )


if __name__ == "__main__":
    unittest.main()
