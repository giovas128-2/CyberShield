"""Pruebas de IA opcional; no realizan solicitudes externas."""
import os
import sys
import types
import unittest
from unittest.mock import patch

from app.services.intelligence.incident_ai import generate_incident_explanation

ANALYSIS = {
    "classification": {
        "severity": "high", "priority": "alta",
        "mitre_technique_id": "T1110",
        "mitre_tactic": "Credential Access",
        "scope": "BLOCKED", "simulated": True,
    },
    "response_assessment": "Acción registrada, no confirmada.",
}

class IncidentAITests(unittest.TestCase):
    def test_not_requested_never_calls_provider(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "dummy"}):
            result = generate_incident_explanation(ANALYSIS, False)
        self.assertEqual(result["ai_status"], "not_requested")

    def test_no_key_preserves_rules(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            result = generate_incident_explanation(ANALYSIS, True)
        self.assertEqual(result["ai_status"], "not_configured")
        self.assertIsNone(result["ai_explanation"])

    def test_provider_receives_no_raw_evidence(self):
        inputs = []
        class Responses:
            def create(self, **kwargs):
                inputs.append(kwargs["input"])
                return types.SimpleNamespace(output_text="Simulación de laboratorio; revisar evidencias.")
        class FakeOpenAI:
            def __init__(self, **kwargs):
                self.responses = Responses()
        fake_module = types.SimpleNamespace(OpenAI=FakeOpenAI)
        analysis = dict(ANALYSIS, details={"secret":"SUPERSECRET"}, source_ip="192.0.2.8")
        with patch.dict(os.environ, {"OPENAI_API_KEY":"dummy"}), patch.dict(sys.modules, {"openai":fake_module}):
            result = generate_incident_explanation(analysis, True)
        self.assertEqual(result["ai_status"], "generated")
        self.assertNotIn("SUPERSECRET",inputs[0])
        self.assertNotIn("192.0.2.8",inputs[0])
        self.assertIn("simulated",inputs[0])

    def test_provider_failure_falls_back(self):
        class FakeOpenAI:
            def __init__(self, **kwargs):
                raise RuntimeError("network unavailable")
        with patch.dict(os.environ, {"OPENAI_API_KEY":"dummy"}), patch.dict(sys.modules, {"openai":types.SimpleNamespace(OpenAI=FakeOpenAI)}):
            result = generate_incident_explanation(ANALYSIS, True)
        self.assertEqual(result["ai_status"], "unavailable")
        self.assertIsNone(result["ai_explanation"])

if __name__ == "__main__":
    unittest.main()
