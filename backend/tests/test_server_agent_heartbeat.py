"""Pruebas offline del intercambio de heartbeat individual entre host remoto y CyberShield."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.agents import agent_heartbeat, token_digest
from uuid import UUID

AGENT_ID = UUID("10000000-0000-4000-8000-000000000011")

class RemoteAgentHeartbeatTests(unittest.TestCase):
    def test_valid_individual_token_updates_server_heartbeat(self):
        db=MagicMock()
        token="secreto-de-prueba-no-real"
        record={
            "server_id": 13,
            "token_hash": token_digest(token),
            "revoked_at": None,
        }
        db.execute.return_value.mappings.return_value.first.return_value=record
        creds=HTTPAuthorizationCredentials(scheme="Bearer",credentials=token)
        result=agent_heartbeat(AGENT_ID,credentials=creds,db=db)
        self.assertEqual(result["heartbeat"],"accepted")
        self.assertEqual(result["server_id"],13)
        self.assertEqual(db.execute.call_count,3)
        db.commit.assert_called_once()

    def test_invalid_token_is_rejected_without_writes(self):
        db=MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value={
            "server_id": 13,
            "token_hash": token_digest("token-correcto"),
            "revoked_at": None,
        }
        creds=HTTPAuthorizationCredentials(scheme="Bearer",credentials="token-invalido")
        with self.assertRaises(HTTPException) as ctx:
            agent_heartbeat(AGENT_ID,credentials=creds,db=db)
        self.assertEqual(ctx.exception.status_code,401)
        self.assertEqual(db.execute.call_count,1)
        db.commit.assert_not_called()

    def test_revoked_token_is_rejected(self):
        from datetime import datetime, timezone
        db=MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value={
            "server_id": 13,
            "token_hash": token_digest("token-de-prueba"),
            "revoked_at": datetime.now(timezone.utc),
        }
        creds=HTTPAuthorizationCredentials(scheme="Bearer",credentials="token-de-prueba")
        with self.assertRaises(HTTPException) as ctx:
            agent_heartbeat(AGENT_ID,credentials=creds,db=db)
        self.assertEqual(ctx.exception.status_code,401)
        db.commit.assert_not_called()

if __name__ == "__main__":
    unittest.main()
