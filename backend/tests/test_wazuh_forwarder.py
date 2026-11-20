"""Pruebas sin Wazuh, red, base de datos ni bloqueos."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import wazuh_forwarder as fw


class FakeResponse:
    status_code = 200
    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.sent = []
        self.closed = False

    def post(self, url, json, headers, timeout):
        self.sent.append(json)
        return FakeResponse()

    def close(self):
        self.closed = True


class ForwarderTests(unittest.TestCase):
    def test_select_relevant_rules(self):
        self.assertTrue(fw.is_relevant_event({"rule": {"id": "5763"}}))
        self.assertTrue(fw.is_relevant_event({"rule": {"id": "5402"}}))
        self.assertFalse(fw.is_relevant_event({"rule": {"id": "40704"}}))
        self.assertFalse(fw.is_relevant_event({"rule": {"id": "5502"}}))

    def test_cursor_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cursor.json"
            cursor = {"device": 1, "inode": 2, "offset": 36}
            fw.save_cursor(cursor, path)
            self.assertEqual(fw.load_cursor(path), cursor)

    @patch("wazuh_forwarder.get_service_headers",
           return_value={"X-CyberShield-Service-Key": "TEST-ONLY"})
    def test_initial_start_skips_old_alerts(self, _headers):
        with tempfile.TemporaryDirectory() as folder:
            alerts = Path(folder) / "alerts.json"
            cursor = Path(folder) / "cursor.json"
            alerts.write_text(json.dumps({"rule": {"id": "5763"}}) + "\n")
            session = FakeSession()
            checks = 0

            def stop():
                nonlocal checks
                checks += 1
                return checks > 1

            fw.follow_alerts(alerts, cursor, session=session, stop=stop,
                             sleep=lambda seconds: None)
            self.assertEqual(session.sent, [])
            self.assertEqual(fw.load_cursor(cursor)["offset"], alerts.stat().st_size)

    @patch("wazuh_forwarder.get_service_headers",
           return_value={"X-CyberShield-Service-Key": "TEST-ONLY"})
    def test_restart_reads_new_alert_only(self, _headers):
        with tempfile.TemporaryDirectory() as folder:
            alerts = Path(folder) / "alerts.json"
            cursor = Path(folder) / "cursor.json"
            alerts.write_text(json.dumps({"rule": {"id": "40704"}}) + "\n")
            session = FakeSession()

            def run(stop_after):
                calls = 0
                def stop():
                    nonlocal calls
                    calls += 1
                    return calls > stop_after
                fw.follow_alerts(alerts, cursor, session=session,
                                 stop=stop, sleep=lambda seconds: None)

            run(1)  # primera ejecución: EOF
            with alerts.open("a") as file:
                file.write(json.dumps({"rule": {"id": "5763"}}) + "\n")
            run(2)
            self.assertEqual(len(session.sent), 1)
            self.assertEqual(session.sent[0]["rule"]["id"], "5763")
            run(2)
            self.assertEqual(len(session.sent), 1)


if __name__ == "__main__":
    unittest.main()
