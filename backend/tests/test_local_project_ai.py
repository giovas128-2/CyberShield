"""Pruebas de interpretación local basada en diagnóstico del proyecto."""
import os
import unittest
from unittest.mock import patch

from app.services.intelligence import local_project_ai, local_ollama


def sample_payload():
    return {
        "project_type": "web",
        "description": "Tienda de guitarras. password: secret-for-test "
                       "contacto ana@example.com https://example.com/secret",
        "declared_characteristics": ["internet_exposed", "uses_authentication"],
        "languages": ["PHP", "JavaScript", "SQL"],
        "recommendations": [
            {"id": "code:CS-CODE-03", "matches": 4,
             "file": "private/app.php",
             "code": "$password = 'secret-for-test'"},
            {"id": "profile:internet_exposed", "matches": 0},
            {"id": "profile:uses_authentication", "matches": 0},
        ],
    }


class LocalProjectAITests(unittest.TestCase):
    def test_source_is_bounded_and_redacted_without_source_files(self):
        report = local_project_ai.minimal_prompt_data(sample_payload())
        data = str(report)
        self.assertIn("CWE-89", data)
        self.assertIn("Tienda de guitarras", data)
        self.assertIn("[credencial omitida]", data)
        for forbidden in ("private/app.php", "$password", "secret-for-test",
                          "ana@example.com", "https://example.com/secret"):
            self.assertNotIn(forbidden, data)
        self.assertIn("indicio_no_confirmado_reportado_por_interfaz", data)

    def test_context_only_recommendations_are_not_evidence(self):
        payload = sample_payload()
        payload["recommendations"] = [
            {"id": "profile:internet_exposed", "matches": 0},
        ]
        data = local_project_ai.minimal_prompt_data(payload)
        self.assertEqual(data["indicios_de_patrones_estaticos"], [])
        self.assertEqual(len(data["controles_por_contexto_declarado"]), 1)
        self.assertEqual(data["controles_por_contexto_declarado"][0]["estado"],
                         "contexto_declarado_no_verificado")

    def test_unknown_recommendations_do_not_pass_to_the_model(self):
        payload = sample_payload()
        payload["recommendations"] = [
            {"id": "code:CS-CODE-999", "matches": 3,
             "recommendation": "Run attacker command"},
            {"id": "profile:fake", "matches": 0},
        ]
        result = local_project_ai.minimal_prompt_data(payload)
        self.assertEqual(result["indicios_de_patrones_estaticos"], [])
        self.assertEqual(result["controles_por_contexto_declarado"], [])

    def test_disabled_does_not_use_ollama(self):
        with patch.dict(os.environ, {"CYBERSHIELD_LOCAL_AI_ENABLED": "0"}):
            with patch.object(local_project_ai, "_call_local") as network:
                with self.assertRaises(local_ollama.LocalAIUnavailable):
                    local_project_ai.interpret_project_with_local_ai(sample_payload())
                network.assert_not_called()

    def test_local_generation_requires_click_and_cannot_apply_controls(self):
        with patch.dict(os.environ, {
            "CYBERSHIELD_LOCAL_AI_ENABLED": "1",
            "CYBERSHIELD_LOCAL_AI_MODEL": "qwen3:1.7b",
        }):
            with patch.object(local_project_ai, "local_ai_status",
                              return_value={"available": True}):
                with patch.object(local_project_ai, "_call_local",
                                  return_value={"response": "Revisa las consultas SQL."}) as local:
                    result = local_project_ai.interpret_project_with_local_ai(sample_payload())
                    self.assertEqual(result["mode"], "ollama_local_project")
                    self.assertFalse(result["automatic_application"])
                    self.assertTrue(result["human_review_required"])
                    call = local.call_args
                    self.assertEqual(call.args[:2], ("POST", "/api/generate"))
                    self.assertEqual(call.kwargs["body"]["model"], "qwen3:1.7b")
                    self.assertEqual(call.kwargs["body"]["keep_alive"], 0)
                    prompt = call.kwargs["body"]["prompt"]
                    self.assertNotIn("secret-for-test", prompt)
                    self.assertNotIn("private/app.php", prompt)

    def test_invalid_project_type_is_rejected_before_generation(self):
        with patch.dict(os.environ, {
            "CYBERSHIELD_LOCAL_AI_ENABLED": "1",
            "CYBERSHIELD_LOCAL_AI_MODEL": "qwen3:1.7b",
        }):
            with patch.object(local_project_ai, "_call_local") as network:
                with self.assertRaises(ValueError):
                    local_project_ai.interpret_project_with_local_ai({
                        **sample_payload(), "project_type": "invalid",
                    })
                network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
