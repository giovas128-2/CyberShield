"""Pruebas aisladas c7 sin tocar Wazuh, archivos ni respuestas."""
import unittest
from app.services.intelligence.ransomware_decision_engine import assess_ransomware_like

BASE = {
    "event_type": "possible_ransomware_behavior",
    "source": "wazuh", "severity": "high",
    "details": {
        "integration": "wazuh_real", "wazuh_alert_id": "1001",
        "path": "/opt/cybershield-lab/ransomware-demo/documento.txt",
        "wazuh_event": "modified", "change_applied": True,
        "sensor_confirmed_ransomware_like": True,
        "lab_ransomware_signal": True, "detection_basis": "behavior",
        "maintenance_mode": False,
    },
}
CONTROL = {"mode": "simulated", "execution_enabled": False}


class RansomwareDecisionTests(unittest.TestCase):
    def assess(self, event=None, exists=True, control=CONTROL):
        return assess_ransomware_like(
            event if event is not None else BASE,
            technique_exists=exists, control=control,
        )

    def test_confirmed_lab_change_is_simulation_only(self):
        result = self.assess()
        self.assertEqual(result.status, "simulation_only")
        self.assertEqual(result.technique_id, "T1486")
        self.assertEqual(result.control_id, "c7")
        self.assertIsNone(result.recommended_action)
        self.assertIsNone(result.target)
        self.assertFalse(result.execution_allowed)
        self.assertFalse(result.executed)

    def test_filename_only_needs_review(self):
        details = {**BASE["details"], "sensor_confirmed_ransomware_like": False,
                   "detection_basis": "filename"}
        self.assertEqual(self.assess({**BASE, "details": details}).status,
                         "needs_investigation")

    def test_missing_wazuh_id_needs_review(self):
        details = {**BASE["details"], "wazuh_alert_id": None}
        self.assertEqual(self.assess({**BASE, "details": details}).status,
                         "needs_investigation")

    def test_lab_event_not_accepted_as_sensor(self):
        self.assertEqual(self.assess({**BASE, "source": "lab"}).status,
                         "needs_investigation")

    def test_maintenance_excluded(self):
        details = {**BASE["details"], "maintenance_mode": True}
        self.assertEqual(self.assess({**BASE, "details": details}).status,
                         "excluded")

    def test_missing_mitre(self):
        self.assertEqual(self.assess(exists=False).status, "knowledge_missing")

    def test_missing_control(self):
        self.assertEqual(self.assess(control=None).status, "control_unavailable")

    def test_integrated_mode_still_no_execution(self):
        result = self.assess(control={"mode": "integrated"})
        self.assertEqual(result.status, "needs_investigation")
        self.assertFalse(result.execution_allowed)
        self.assertIsNone(result.recommended_action)

    def test_other_event_not_applicable(self):
        self.assertEqual(self.assess({
            **BASE, "event_type": "suspicious_file_change"
        }).status, "not_applicable")

    def test_missing_content_change(self):
        details = {**BASE["details"], "change_applied": False}
        self.assertEqual(self.assess({**BASE, "details": details}).status,
                         "needs_investigation")


if __name__ == "__main__":
    unittest.main()
