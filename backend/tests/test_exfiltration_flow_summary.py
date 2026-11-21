"""Pruebas unitarias de agrupación c6, sin red ni DB."""
import unittest
from app.services.intelligence.exfiltration_flow_summary import (
    consolidate_exfiltration_flows,
)


def alert(flow_id, timestamp, sid=1000002):
    return {
        "flow_id": flow_id,
        "timestamp": timestamp,
        "event_type": "alert",
        "alert": {"signature_id": sid},
    }


def flow(flow_id, timestamp, bytes_up):
    return {
        "flow_id": flow_id,
        "timestamp": timestamp,
        "event_type": "flow",
        "dest_ip": "172.25.176.1",
        "dest_port": 8765,
        "flow": {"bytes_toserver": bytes_up},
    }


class ExfilFlowSummaryTests(unittest.TestCase):
    def test_three_alerts_same_window_and_flow_consolidated(self):
        timestamps = [
            f"2026-11-07T10:27:08.{i:06d}-0600"
            for i in (1, 2, 3)
        ]
        items = consolidate_exfiltration_flows(
            [alert(42, t) for t in timestamps]
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].alerts, 3)
        self.assertFalse(items[0].execution_allowed)
        self.assertFalse(items[0].executed)

    def test_identical_retransmission_not_counted_twice(self):
        item = alert(42, "2026-11-07T10:27:08-0600")
        items = consolidate_exfiltration_flows([item, item])
        self.assertEqual(items[0].alerts, 1)

    def test_different_flow_not_merged(self):
        ts = "2026-11-07T10:27:08-0600"
        self.assertEqual(
            len(consolidate_exfiltration_flows([alert(1, ts), alert(2, ts)])),
            2,
        )

    def test_different_window_not_merged(self):
        events = [
            alert(1, "2026-11-07T10:27:08-0600"),
            alert(1, "2026-11-07T10:32:08-0600"),
        ]
        self.assertEqual(len(consolidate_exfiltration_flows(events)), 2)

    def test_other_signature_excluded(self):
        self.assertEqual(
            consolidate_exfiltration_flows([
                alert(1, "2026-11-07T10:27:08-0600", 1000003)
            ]), [],
        )

    def test_bulk_flow_above_threshold(self):
        items = consolidate_exfiltration_flows([
            flow(1, "2026-11-07T10:27:08-0600", 20_000_000)
        ])
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0].bulk_transfer_observed)
        self.assertEqual(items[0].max_bytes_toserver, 20_000_000)

    def test_small_flow_not_qualified(self):
        self.assertEqual(consolidate_exfiltration_flows([
            flow(1, "2026-11-07T10:27:08-0600", 10_000)
        ]), [])

    def test_missing_identity_not_grouped(self):
        item = alert(None, "2026-11-07T10:27:08-0600")
        self.assertEqual(consolidate_exfiltration_flows([item]), [])

    def test_missing_timezone_not_grouped(self):
        item = alert(1, "2026-11-07T10:27:08")
        self.assertEqual(consolidate_exfiltration_flows([item]), [])

    def test_no_action_and_simulation_only(self):
        items = consolidate_exfiltration_flows([
            alert(1, "2026-11-07T10:27:08-0600")
        ])
        self.assertEqual(items[0].status, "simulation_only")
        self.assertFalse(items[0].execution_allowed)
        self.assertFalse(items[0].executed)

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            consolidate_exfiltration_flows([], window_seconds=0)


if __name__ == "__main__":
    unittest.main()
