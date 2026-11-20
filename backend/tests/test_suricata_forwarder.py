"""Pruebas forwarder Suricata sin llamadas HTTP ni eventos reales."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from suricata_forwarder import (
    relevant, load_cursor, save_cursor, follow_eve,
)


def sc5(timestamp):
    return {
        "event_type": "alert", "timestamp": timestamp, "flow_id": 44,
        "alert": {"signature_id": 1000003},
    }


class SuricataForwarderTests(unittest.TestCase):
    def test_sc5_and_exfil_relevant(self):
        self.assertTrue(relevant(sc5("2026-11-07T10:00:00-0600")))
        self.assertTrue(relevant({
            "event_type": "alert", "alert": {"signature_id": 1000002},
            "dest_ip": "172.25.176.1", "dest_port": 8765,
        }))

    def test_other_alert_ignored(self):
        self.assertFalse(relevant({
            "event_type": "alert", "alert": {"signature_id": 2027397},
        }))

    def test_cursor_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cursor.json"
            expected = {"device": 1, "inode": 2, "offset": 3}
            save_cursor(expected, path)
            self.assertEqual(load_cursor(path), expected)

    def test_invalid_cursor_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cursor.json"
            path.write_text('{"offset": -1}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_cursor(path)

    def test_first_start_skips_history(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "eve.json"
            cursor = Path(directory) / "cursor.json"
            source.write_text(json.dumps(sc5("old")) + "\n", encoding="utf-8")
            client = MagicMock()
            ticks = iter([False, True])
            follow_eve(
                source, cursor, client,
                stop=lambda: next(ticks),
                sleep=lambda _: None,
            )
            client.post.assert_not_called()
            self.assertEqual(load_cursor(cursor)["offset"], source.stat().st_size)

    def test_failed_delivery_retries_same_alert(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "eve.json"
            cursor = Path(directory) / "cursor.json"
            source.write_text(json.dumps(sc5("new")) + "\n", encoding="utf-8")
            with source.open("rb") as file:
                cursor_data = {
                    "device": file.fileno() and source.stat().st_dev,
                    "inode": source.stat().st_ino,
                    "offset": 0,
                }
            save_cursor(cursor_data, cursor)
            client = MagicMock()
            import httpx
            client.post.side_effect = [
                httpx.ConnectError("offline"),
                MagicMock(status_code=200, json=lambda: {"duplicate": False}),
            ]
            ticks = iter([False, False, False, True])
            follow_eve(
                source, cursor, client,
                stop=lambda: next(ticks),
                sleep=lambda _: None,
            )
            self.assertEqual(client.post.call_count, 2)
            self.assertEqual(load_cursor(cursor)["offset"], source.stat().st_size)

    def test_same_flow_different_alerts_both_sent(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "eve.json"
            cursor = Path(directory) / "cursor.json"
            source.write_text(
                json.dumps(sc5("time1")) + "\n"
                + json.dumps(sc5("time2")) + "\n",
                encoding="utf-8",
            )
            save_cursor({
                "device": source.stat().st_dev,
                "inode": source.stat().st_ino,
                "offset": 0,
            }, cursor)
            client = MagicMock()
            client.post.return_value.status_code = 200
            client.post.return_value.json.return_value = {"duplicate": False}
            ticks = iter([False, False, False, True])
            follow_eve(
                source, cursor, client,
                stop=lambda: next(ticks),
                sleep=lambda _: None,
            )
            self.assertEqual(client.post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
