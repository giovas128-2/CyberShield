"""Alta manual real de servidores; pruebas offline sin modificar PostgreSQL."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi import HTTPException, Response
from pydantic import ValidationError

from app.api.servers import ServerOnboardRequest, get_servers, onboard_server


class ServerOnboardingTests(unittest.TestCase):
    def payload(self, **overrides):
        return ServerOnboardRequest(**({
            "name":"Servidor Windows de pruebas",
            "ip_address":"192.0.2.25", "platform":"windows",
        } | overrides))

    def test_validates_real_ip(self):
        with self.assertRaises(ValidationError):
            self.payload(ip_address="servidor.invalid")
        with self.assertRaises(ValidationError):
            self.payload(ip_address="0.0.0.0")
        with self.assertRaises(ValidationError):
            self.payload(ip_address="239.0.0.1")

    def test_supports_ipv6(self):
        self.assertEqual(self.payload(ip_address="2001:db8::1").ip_address,"2001:db8::1")

    def test_no_credentials_migration_503(self):
        db=MagicMock()
        db.execute.return_value.scalar_one.return_value=None
        with self.assertRaises(HTTPException) as ctx:
            onboard_server(self.payload(),response=Response(),db=db,_current_user=SimpleNamespace(role="engineer"))
        self.assertEqual(ctx.exception.status_code,503)
        db.add.assert_not_called()

    def test_existing_ip_409(self):
        db=MagicMock()
        db.execute.return_value.scalar_one.return_value="server_agent_credentials"
        db.query.return_value.filter.return_value.first.return_value=(1,)
        with self.assertRaises(HTTPException) as ctx:
            onboard_server(self.payload(),response=Response(),db=db,_current_user=SimpleNamespace(role="engineer"))
        self.assertEqual(ctx.exception.status_code,409)
        db.add.assert_not_called()

    def test_atomic_registration_does_not_claim_online(self):
        db=MagicMock()
        db.execute.return_value.scalar_one.return_value="server_agent_credentials"
        db.query.return_value.filter.return_value.first.return_value=None
        def flush():
            db.add.call_args[0][0].id=105
        db.flush.side_effect=flush
        result=onboard_server(self.payload(),response=Response(),db=db,_current_user=SimpleNamespace(role="engineer"))
        self.assertEqual(result["server"]["status"],"registered")
        self.assertIsNone(result["server"]["last_seen"])
        self.assertEqual(result["server"]["id"],105)
        self.assertTrue(result["agent"]["token_shown_once"])
        self.assertGreaterEqual(len(result["agent"]["token"]),40)
        self.assertEqual(result["agent"]["platform"],"windows")
        self.assertEqual(db.commit.call_count,1)
        db.add.assert_called_once()

    def test_get_connected_only_with_recent_individual_heartbeat(self):
        now=datetime.now(timezone.utc)
        db=MagicMock()
        server=SimpleNamespace(id=1,name="win01",ip_address="192.0.2.25",
            status="online",agent="CyberShield",created_at=now,last_seen=None)
        db.query.return_value.order_by.return_value.all.return_value=[server]
        def execute(query,*args,**kwargs):
            sql=str(query)
            r=MagicMock()
            if "to_regclass" in sql:
                r.scalar_one.return_value="server_agent_credentials"
            else:
                r.mappings.return_value.all.return_value=[{
                    "server_id":1,"agent_id":"00000000-0000-4000-8000-000000000001",
                    "platform":"windows","agent_version":"1.0",
                    "last_seen":None,"revoked_at":None,
                }]
            return r
        db.execute.side_effect=execute
        result=get_servers(db=db,_current_user=SimpleNamespace(id=1))
        self.assertEqual(result[0]["status"],"registered")
        self.assertEqual(result[0]["agent_connection"]["state"],"awaiting_heartbeat")

    def test_stale_agent_marked_offline(self):
        now=datetime.now(timezone.utc)
        db=MagicMock()
        server=SimpleNamespace(id=3,name="linux02",ip_address="192.0.2.30",
            status="online",agent="CyberShield",created_at=now,last_seen=now)
        db.query.return_value.order_by.return_value.all.return_value=[server]
        def execute(query,*args,**kwargs):
            r=MagicMock()
            if "to_regclass" in str(query):
                r.scalar_one.return_value="server_agent_credentials"
            else:
                r.mappings.return_value.all.return_value=[{
                    "server_id":3,"agent_id":"00000000-0000-4000-8000-000000000003",
                    "platform":"linux","agent_version":"1.0",
                    "last_seen":now-timedelta(minutes=3),"revoked_at":None,
                }]
            return r
        db.execute.side_effect=execute
        result=get_servers(db=db,_current_user=SimpleNamespace(id=1))
        self.assertEqual(result[0]["status"],"offline")
        self.assertEqual(result[0]["agent_connection"]["state"],"disconnected")

    def test_recent_agent_marked_connected(self):
        now=datetime.now(timezone.utc)
        db=MagicMock()
        server=SimpleNamespace(id=4,name="ubuntu04",ip_address="192.0.2.40",
            status="registered",agent="CyberShield",created_at=now,last_seen=now)
        db.query.return_value.order_by.return_value.all.return_value=[server]
        def execute(query,*args,**kwargs):
            r=MagicMock()
            if "to_regclass" in str(query):
                r.scalar_one.return_value="server_agent_credentials"
            else:
                r.mappings.return_value.all.return_value=[{
                    "server_id":4,"agent_id":"00000000-0000-4000-8000-000000000004",
                    "platform":"linux","agent_version":"1.0",
                    "last_seen":now-timedelta(seconds=20),"revoked_at":None,
                }]
            return r
        db.execute.side_effect=execute
        result=get_servers(db=db,_current_user=SimpleNamespace(id=1))
        self.assertEqual(result[0]["status"],"online")
        self.assertEqual(result[0]["agent_connection"]["state"],"connected")

if __name__=="__main__":
    unittest.main()
