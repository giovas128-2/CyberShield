"""Pruebas unitarias c8; sin red, SSH ni escritura en BD."""
import unittest
from app.services.intelligence.lateral_decision_engine import assess_lateral_ssh

BASE = {
    "event_type": "possible_lateral_movement",
    "source": "wazuh", "severity": "high",
    "details": {
        "integration": "wazuh_real",
        "wazuh_alert_id": "wazuh-test-100210",
        "wazuh_rule_id": "100210",
        "protocol": "ssh", "login_successful": True,
        "sensor_confirmed_lateral": True,
        "srcip": "192.0.2.10",
        "destination_user": "lateral_demo",
        "pair_authorized": False,
        "maintenance_mode": False,
    },
}
CONTROL = {"mode": "simulated", "execution_enabled": False}


class LateralSshDecisionTests(unittest.TestCase):
    def assess(self, event=None, technique_exists=True, control=CONTROL):
        return assess_lateral_ssh(
            BASE if event is None else event,
            technique_exists=technique_exists,
            control=control,
        )

    def changed(self, **details):
        return {**BASE, "details": {**BASE["details"], **details}}

    def test_lab_evidence_is_simulation_only(self):
        d = self.assess()
        self.assertEqual(d.status, "simulation_only")
        self.assertEqual((d.technique_id, d.control_id), ("T1021.004", "c8"))
        self.assertIsNone(d.recommended_action)
        self.assertIsNone(d.target)
        self.assertFalse(d.execution_allowed)
        self.assertFalse(d.executed)

    def test_historical_no_wazuh_id(self):
        self.assertEqual(
            self.assess(self.changed(wazuh_alert_id=None)).status,
            "needs_investigation",
        )

    def test_normal_ssh_not_lateral(self):
        self.assertEqual(
            self.assess(self.changed(destination_user="yahir")).status,
            "needs_investigation",
        )

    def test_failed_login_not_lateral(self):
        self.assertEqual(
            self.assess(self.changed(login_successful=False)).status,
            "needs_investigation",
        )

    def test_other_rule_requires_review(self):
        self.assertEqual(
            self.assess(self.changed(wazuh_rule_id="5715")).status,
            "needs_investigation",
        )

    def test_maintenance_excluded(self):
        self.assertEqual(
            self.assess(self.changed(maintenance_mode=True)).status,
            "excluded",
        )

    def test_no_mitre(self):
        self.assertEqual(self.assess(technique_exists=False).status, "knowledge_missing")

    def test_no_control(self):
        self.assertEqual(self.assess(control=None).status, "control_unavailable")

    def test_integrated_still_nonexecuting(self):
        d = self.assess(control={"mode": "integrated"})
        self.assertEqual(d.status, "needs_investigation")
        self.assertFalse(d.execution_allowed)
        self.assertIsNone(d.recommended_action)

    def test_lab_source_not_accepted_as_wazuh(self):
        self.assertEqual(
            self.assess({**BASE, "source": "lab"}).status,
            "needs_investigation",
        )

    def test_wrong_event_ignored(self):
        self.assertEqual(
            self.assess({**BASE, "event_type": "authentication_failure"}).status,
            "not_applicable",
        )


if __name__ == "__main__":
    unittest.main()
