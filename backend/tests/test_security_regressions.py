import unittest
from unittest.mock import patch

from fastapi import Request
from sqlalchemy import event, inspect, text
from sqlalchemy.exc import IntegrityError

from app.api.events import (
    _remote_lab_source_ip,
    receive_remote_lab_event,
)
from app.api.incidents import list_incidents
from app.database.connection import engine, SessionLocal
from app.schemas.event import RemoteLabEventRequest


class TestDatabaseIntegrity(unittest.TestCase):

    def test_incident_event_foreign_key_exists(self):
        inspector = inspect(engine)

        foreign_keys = inspector.get_foreign_keys(
            "incidents"
        )

        matching = [
            fk
            for fk in foreign_keys
            if fk.get("constrained_columns")
            == ["event_id"]
            and fk.get("referred_table")
            == "events"
            and fk.get("referred_columns")
            == ["id"]
        ]

        self.assertTrue(
            matching,
            "Falta FK incidents.event_id -> events.id",
        )

        self.assertEqual(
            matching[0].get("options", {}).get(
                "ondelete"
            ),
            "RESTRICT",
        )

    def test_orphan_incident_is_rejected(self):
        with engine.connect() as conn:
            transaction = conn.begin()

            try:
                max_event_id = conn.execute(
                    text(
                        "SELECT COALESCE(MAX(id), 0) "
                        "FROM events"
                    )
                ).scalar_one()

                fake_event_id = (
                    max_event_id + 1000000
                )

                with self.assertRaises(
                    IntegrityError
                ):
                    conn.execute(
                        text("""
                            INSERT INTO incidents (
                                event_id,
                                status,
                                severity,
                                created_at
                            )
                            VALUES (
                                :event_id,
                                'open',
                                'HIGH',
                                NOW()
                            )
                        """),
                        {
                            "event_id":
                                fake_event_id,
                        },
                    )

            finally:
                transaction.rollback()


class TestRemoteLabSecurity(unittest.TestCase):

    def _request(
        self,
        client_ip="192.168.1.69",
        port=12345,
        forwarded_ip="203.0.113.250",
    ):
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/events/remote-lab",
            "headers": [
                (
                    b"x-forwarded-for",
                    forwarded_ip.encode(),
                ),
            ],
            "client": (
                client_ip,
                port,
            ),
            "server": (
                "127.0.0.1",
                8000,
            ),
            "scheme": "http",
            "query_string": b"",
            "http_version": "1.1",
        }

        return Request(scope)

    def test_remote_ip_comes_from_socket_not_header(self):
        request = self._request()

        source_ip, port = (
            _remote_lab_source_ip(
                request
            )
        )

        self.assertEqual(
            source_ip,
            "192.168.1.69",
        )

        self.assertEqual(
            port,
            12345,
        )

    @patch(
        "app.api.events.process_security_event"
    )
    def test_remote_client_cannot_self_classify_attack(
        self,
        process_mock,
    ):
        process_mock.return_value = {
            "ok": True,
        }

        # Campos adicionales simulan un cliente
        # intentando declarar información sensible.
        data = RemoteLabEventRequest(
            server_id=2,
            user="dannael_lab",
            description="Prueba remota",
            details={
                "client_name":
                    "equipo-dannael",
                "test_id":
                    "P6-REMOTE",
                "script_name":
                    "remote_test.py",

                # Deben ser descartados.
                "modified_files": 9999,
                "sensor_confirmed_ransomware_like":
                    True,
                "wazuh_rule_id": "999999",
            },

            source_ip="203.0.113.250",
            event_type=(
                "possible_ransomware_behavior"
            ),
            severity="CRITICAL",
            scope="IMPACT",
        )

        request = self._request()

        receive_remote_lab_event(
            request=request,
            data=data,
            db=object(),
        )

        process_mock.assert_called_once()

        event_payload = (
            process_mock.call_args.args[1]
        )

        self.assertEqual(
            event_payload.event_type,
            "remote_lab_connectivity_test",
        )

        self.assertEqual(
            event_payload.source,
            "remote_lab_http",
        )

        self.assertEqual(
            str(event_payload.source_ip),
            "192.168.1.69",
        )

        self.assertIsNone(
            event_payload.scope
        )

        details = (
            event_payload.details or {}
        )

        self.assertEqual(
            details.get("client_name"),
            "equipo-dannael",
        )

        self.assertEqual(
            details.get(
                "observed_source_ip"
            ),
            "192.168.1.69",
        )

        self.assertNotIn(
            "modified_files",
            details,
        )

        self.assertNotIn(
            "sensor_confirmed_ransomware_like",
            details,
        )

        self.assertNotIn(
            "wazuh_rule_id",
            details,
        )


class TestIncidentPerformance(unittest.TestCase):

    def test_incident_list_does_not_reintroduce_n_plus_one(
        self,
    ):
        statements = []

        def before_cursor_execute(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            statements.append(statement)

        event.listen(
            engine,
            "before_cursor_execute",
            before_cursor_execute,
        )

        db = SessionLocal()

        try:
            list_incidents(db=db)

        finally:
            db.close()

            event.remove(
                engine,
                "before_cursor_execute",
                before_cursor_execute,
            )

        self.assertLessEqual(
            len(statements),
            4,
            (
                "Regresión N+1: /incidents "
                f"ejecutó {len(statements)} "
                "consultas SQL"
            ),
        )



class TestWazuhClassification(unittest.TestCase):

    def _analyze(self, normalized):
        from types import SimpleNamespace

        from app.cybersecurity.rules import (
            analyze_security_event,
        )

        event = SimpleNamespace(
            event_type=normalized["event_type"],
            details=normalized.get("details") or {},
            scope=normalized.get("scope"),
        )

        return analyze_security_event(event)

    def test_fim_behavior_detects_real_lab_change(self):
        from app.cybersecurity.wazuh_adapter import (
            normalize_wazuh_event,
        )

        raw = {
            "rule": {
                "id": "550",
                "level": 7,
                "description": (
                    "Integrity checksum changed"
                ),
                "groups": ["syscheck"],
            },
            "agent": {
                "id": "001",
                "name": "srv-cyber-01",
                "ip": "100.77.51.7",
            },
            "decoder": {
                "name":
                    "syscheck_integrity_changed",
            },
            "syscheck": {
                "path": (
                    "/opt/cybershield-lab/"
                    "ransomware-demo/d3_lab/"
                    "archivo_1.txt"
                ),
                "event": "modified",
                "sha256_before": "aaa",
                "sha256_after": "bbb",
                "size_before": "10",
                "size_after": "10",
            },
        }

        normalized = normalize_wazuh_event(
            raw,
            server_id=2,
        )

        self.assertEqual(
            normalized["event_type"],
            "possible_ransomware_behavior",
        )

        # FIM sabe qué host fue afectado,
        # pero no demuestra la IP atacante.
        self.assertIsNone(
            normalized["source_ip"]
        )

        details = normalized["details"]

        self.assertEqual(
            details["affected_host_ip"],
            "100.77.51.7",
        )

        self.assertEqual(
            details["source_ip_role"],
            "unknown_attacker",
        )

        self.assertEqual(
            details["detection_basis"],
            "behavior",
        )

        self.assertTrue(
            details[
                "sensor_confirmed_ransomware_like"
            ]
        )

        self.assertIn(
            "sha256_changed",
            details["behavior_indicators"],
        )

        result = self._analyze(normalized)

        self.assertEqual(
            result["risk_level"],
            "high",
        )
        self.assertTrue(
            result["create_incident"]
        )
        self.assertEqual(
            result["scope"],
            "IMPACT",
        )

    def test_locked_file_plus_behavior_becomes_critical(self):
        from app.cybersecurity.wazuh_adapter import (
            normalize_wazuh_event,
        )

        raw = {
            "rule": {
                "id": "554",
                "level": 7,
                "description": "File added",
                "groups": ["syscheck"],
            },
            "agent": {
                "id": "001",
                "name": "srv-cyber-01",
                "ip": "100.77.51.7",
            },
            "decoder": {
                "name": "syscheck_new_entry",
            },
            "syscheck": {
                "path": (
                    "/opt/cybershield-lab/"
                    "ransomware-demo/d3_lab/"
                    "archivo_2.txt.locked"
                ),
                "event": "added",
            },
        }

        normalized = normalize_wazuh_event(
            raw,
            server_id=2,
        )

        details = normalized["details"]

        self.assertEqual(
            normalized["event_type"],
            "possible_ransomware_behavior",
        )

        self.assertEqual(
            details["normalized_demo_filename"],
            "archivo_2.txt",
        )

        self.assertTrue(
            details["suspicious_extension"]
        )

        self.assertEqual(
            details["detection_basis"],
            "filename_and_behavior",
        )

        result = self._analyze(normalized)

        self.assertEqual(
            result["risk_level"],
            "critical",
        )
        self.assertTrue(
            result["create_incident"]
        )
        self.assertEqual(
            result["scope"],
            "IMPACT",
        )

    def test_filename_alone_does_not_claim_ransomware_impact(
        self,
    ):
        from app.cybersecurity.wazuh_adapter import (
            normalize_wazuh_event,
        )

        raw = {
            "rule": {
                "id": "550",
                "level": 5,
                "description": "FIM observation",
                "groups": ["syscheck"],
            },
            "agent": {
                "id": "001",
                "name": "srv-cyber-01",
                "ip": "100.77.51.7",
            },
            "decoder": {
                "name":
                    "syscheck_integrity_changed",
            },
            "syscheck": {
                "path": (
                    "/opt/cybershield-lab/"
                    "ransomware-demo/d3_lab/"
                    "archivo_3.txt.locked"
                ),

                # No hay cambio aplicado.
                "event": "observed",
            },
        }

        normalized = normalize_wazuh_event(
            raw,
            server_id=2,
        )

        details = normalized["details"]

        self.assertEqual(
            details["detection_basis"],
            "filename",
        )

        self.assertFalse(
            details[
                "sensor_confirmed_ransomware_like"
            ]
        )

        result = self._analyze(normalized)

        self.assertEqual(
            result["risk_level"],
            "warning",
        )

        self.assertFalse(
            result["create_incident"]
        )

        self.assertEqual(
            result["scope"],
            "REACHED",
        )

    def test_ssh_bruteforce_preserves_remote_peer_ip(self):
        from app.cybersecurity.wazuh_adapter import (
            normalize_wazuh_event,
        )

        raw = {
            "rule": {
                "id": "5763",
                "level": 10,
                "description": (
                    "SSH brute force detected"
                ),
                "frequency": 12,
                "groups": [
                    "authentication_failures"
                ],
                "mitre": {
                    "id": ["T1110"],
                    "tactic": [
                        "Credential Access"
                    ],
                    "technique": [
                        "Brute Force"
                    ],
                },
            },
            "agent": {
                "id": "001",
                "name": "srv-cyber-01",
                "ip": "100.77.51.7",
            },
            "decoder": {
                "name": "sshd",
            },
            "data": {
                "srcip": "100.125.115.24",
                "srcport": "51422",
                "dstuser": "demo_user",
            },
        }

        normalized = normalize_wazuh_event(
            raw,
            server_id=2,
        )

        self.assertEqual(
            normalized["source_ip"],
            "100.125.115.24",
        )

        details = normalized["details"]

        self.assertEqual(
            details["source_ip_observation"],
            "wazuh_srcip",
        )

        self.assertEqual(
            details["source_ip_role"],
            "remote_peer",
        )

        self.assertTrue(
            details[
                "sensor_confirmed_bruteforce"
            ]
        )

        result = self._analyze(normalized)

        self.assertEqual(
            result["risk_level"],
            "high",
        )

        self.assertTrue(
            result["create_incident"]
        )

        self.assertEqual(
            result["scope"],
            "REACHED",
        )


if __name__ == "__main__":
    unittest.main()
