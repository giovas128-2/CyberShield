"""Pruebas de identidad y reenvío de alertas SC5, sin red ni BD real."""
import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from app.cybersecurity.suricata_adapter import (
    sc5_alert_fingerprint, normalize_suricata_event,
)
from app.api.integrations import receive_suricata_event


def alert(timestamp="2026-11-07T10:46:39.206251-0600", flow_id=42):
    return {
        "event_type": "alert", "timestamp": timestamp,
        "flow_id": flow_id, "src_ip": "192.0.2.1", "src_port": 50001,
        "dest_ip": "198.51.100.10", "dest_port": 443, "proto": "TCP",
        "alert": {"signature_id": 1000003, "signature": "SC5"},
    }


class SuricataDedupTests(unittest.TestCase):
    def test_retransmission_same_fingerprint(self):
        self.assertEqual(sc5_alert_fingerprint(alert()),
                         sc5_alert_fingerprint(alert()))

    def test_same_flow_different_alerts(self):
        self.assertNotEqual(
            sc5_alert_fingerprint(alert()),
            sc5_alert_fingerprint(alert("2026-11-07T10:46:39.206287-0600"))
        )

    def test_different_flow(self):
        self.assertNotEqual(sc5_alert_fingerprint(alert()),
                            sc5_alert_fingerprint(alert(flow_id=43)))

    def test_missing_metadata_has_no_fingerprint(self):
        raw = alert()
        del raw["flow_id"]
        self.assertIsNone(sc5_alert_fingerprint(raw))

    def test_other_signature_has_no_fingerprint(self):
        raw = alert()
        raw["alert"]["signature_id"] = 1000002
        self.assertIsNone(sc5_alert_fingerprint(raw))

    def test_adapter_embeds_fingerprint(self):
        raw = alert()
        normalized = normalize_suricata_event(raw, server_id=2)
        self.assertEqual(
            normalized["details"]["suricata_sc5_fingerprint"],
            sc5_alert_fingerprint(raw),
        )

    @patch("app.api.integrations.validate_server")
    @patch("app.api.integrations.process_security_event")
    def test_duplicate_is_acknowledged_without_new_shadow(self, process, validate):
        orig = Exception("duplicate")
        orig.diag = MagicMock()
        orig.diag.constraint_name = "ux_events_suricata_sc5_fingerprint"
        process.side_effect = IntegrityError("INSERT INTO events", {}, orig)
        db = MagicMock()
        db.execute.return_value.scalar_one_or_none.return_value = 39073
        result = receive_suricata_event(alert(), server_id=2, db=db)
        self.assertTrue(result["duplicate"])
        self.assertEqual(result["event"]["id"], 39073)
        self.assertFalse(result["autonomous_decision"]["executed"])
        db.rollback.assert_called_once()

if __name__ == "__main__":
    unittest.main()
