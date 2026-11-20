"""Unit tests para guardado c6; DB falsa, ninguna escritura real."""
import unittest
from unittest.mock import MagicMock

from app.services.intelligence.exfiltration_flow_summary import (
    ExfilFlowSummary, consolidate_exfiltration_flows,
)
from app.services.intelligence.exfiltration_flow_store import (
    store_complete_exfil_snapshots,
)


def event(timestamp):
    return {
        "flow_id": 99,
        "timestamp": timestamp,
        "event_type": "alert",
        "alert": {"signature_id": 1000002},
    }


class ExfilFlowStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.alerts = consolidate_exfiltration_flows([
            event("2026-11-07T10:27:08.123456-0600"),
            event("2026-11-07T10:27:08.123456-0600"),
            event("2026-11-07T10:27:08.123457-0600"),
        ])

    def test_raw_and_distinct_separate(self):
        self.assertEqual(self.alerts[0].raw_alert_records, 3)
        self.assertEqual(self.alerts[0].distinct_timestamps, 2)
        self.assertEqual(self.alerts[0].alerts, 2)

    def test_requires_complete_snapshot(self):
        with self.assertRaises(ValueError):
            store_complete_exfil_snapshots(
                self.db, self.alerts, sensor_id="suricata-local"
            )
        self.db.execute.assert_not_called()

    def test_stores_snapshot_without_committing(self):
        count = store_complete_exfil_snapshots(
            self.db, self.alerts,
            sensor_id="suricata-local", snapshot_complete=True
        )
        self.assertEqual(count, 1)
        self.db.execute.assert_called_once()
        params = self.db.execute.call_args.args[1]
        self.assertEqual(params["raw_alert_records"], 3)
        self.assertEqual(params["distinct_observations"], 2)
        self.assertEqual(params["sensor_id"], "suricata-local")
        self.db.commit.assert_not_called()

    def test_missing_sensor_rejected(self):
        with self.assertRaises(ValueError):
            store_complete_exfil_snapshots(
                self.db, self.alerts, sensor_id="",
                snapshot_complete=True,
            )
        self.db.execute.assert_not_called()

    def test_rejects_duplicate_window_before_writing(self):
        with self.assertRaises(ValueError):
            store_complete_exfil_snapshots(
                self.db, self.alerts + self.alerts,
                sensor_id="suricata-local", snapshot_complete=True
            )
        self.db.execute.assert_not_called()

    def test_no_action_methods_called(self):
        store_complete_exfil_snapshots(
            self.db, self.alerts,
            sensor_id="suricata-local", snapshot_complete=True
        )
        self.db.commit.assert_not_called()
        self.db.add.assert_not_called()
        self.db.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
