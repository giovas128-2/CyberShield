"""Pruebas de IA local: aislamiento, desactivación y controles de datos."""
import os
import unittest
from unittest.mock import MagicMock, patch
from app.services.intelligence import local_ollama


class LocalAITests(unittest.TestCase):
    def test_disabled_by_default_never_connects(self):
        with patch.dict(os.environ, {"CYBERSHIELD_LOCAL_AI_ENABLED": "0"}, clear=False):
            with patch.object(local_ollama, "_call_local") as mock_net:
                status = local_ollama.local_ai_status()
                self.assertEqual(status["status"], "disabled")
                with self.assertRaises(local_ollama.LocalAIUnavailable):
                    local_ollama.interpret_mitre_with_local_ai(MagicMock(), "T1110")
                mock_net.assert_not_called()

    def test_model_must_be_approved_and_not_cloud(self):
        with patch.dict(os.environ, {
            "CYBERSHIELD_LOCAL_AI_ENABLED": "1",
            "CYBERSHIELD_LOCAL_AI_MODEL": "qwen3:cloud"
        }):
            status = local_ollama.local_ai_status()
            self.assertEqual(status["status"], "invalid_model")
            with self.assertRaises(local_ollama.LocalAIUnavailable):
                local_ollama.interpret_mitre_with_local_ai(MagicMock(), "T1110")

    def test_missing_model_never_generates(self):
        with patch.dict(os.environ, {
            "CYBERSHIELD_LOCAL_AI_ENABLED": "1",
            "CYBERSHIELD_LOCAL_AI_MODEL": "qwen3:0.6b",
        }):
            with patch.object(local_ollama, "_call_local", return_value={"models": []}) as mock_net:
                with self.assertRaises(local_ollama.LocalAIUnavailable):
                    local_ollama.interpret_mitre_with_local_ai(MagicMock(), "T1110")
                self.assertEqual(mock_net.call_count, 1)

    def test_response_uses_public_mitre_only(self):
        db = MagicMock()
        db.execute.return_value.mappings.return_value.first.return_value = {
            "attack_id": "T1110",
            "name": "Brute Force",
            "description": "Public MITRE description.",
            "source_version": "bundle-test",
        }
        db.execute.return_value.mappings.return_value.all.return_value = [{
            "mitigation_id": "M1032", "name": "Multi-factor Authentication",
        }]
        with patch.dict(os.environ, {
            "CYBERSHIELD_LOCAL_AI_ENABLED": "1",
            "CYBERSHIELD_LOCAL_AI_MODEL": "qwen3:0.6b",
        }):
            with patch.object(local_ollama, "_call_local") as fake:
                fake.side_effect = [
                    {"models": [{"name": "qwen3:0.6b"}]},
                    {"response": "Revisa la autenticación multifactor."},
                ]
                report = local_ollama.interpret_mitre_with_local_ai(db, "T1110")
                self.assertEqual(report["mode"], "ollama_local")
                self.assertFalse(report["automated_changes"])
                self.assertTrue(report["human_review_required"])
                payload = fake.call_args_list[-1].kwargs["body"]
                self.assertEqual(payload["model"], "qwen3:0.6b")
                self.assertEqual(payload["keep_alive"], 0)
                self.assertFalse(payload["stream"])
                self.assertNotIn("ip", payload["prompt"].lower().replace("description",""))
                self.assertEqual(db.execute.call_count, 2)
                db.commit.assert_not_called()

    def test_invalid_id_does_not_query_database(self):
        with patch.dict(os.environ, {
            "CYBERSHIELD_LOCAL_AI_ENABLED": "1",
            "CYBERSHIELD_LOCAL_AI_MODEL": "qwen3:0.6b",
        }):
            with patch.object(local_ollama, "local_ai_status", return_value={"available": True}):
                db = MagicMock()
                with self.assertRaises(ValueError):
                    local_ollama.interpret_mitre_with_local_ai(db, "CVE-2025-1234")
                db.execute.assert_not_called()

    def test_transport_cannot_target_external_endpoints(self):
        with self.assertRaises(ValueError):
            local_ollama._call_local("POST", "https://example.com")
        with self.assertRaises(ValueError):
            local_ollama._call_local("GET", "/api/generate")


if __name__ == "__main__":
    unittest.main()
