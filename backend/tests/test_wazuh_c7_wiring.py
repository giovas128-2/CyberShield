"""Regresión de cableado c7: prueba estática sin API, red ni BD."""
import ast
from pathlib import Path
import unittest


class WazuhC7WiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / "app/api/integrations.py"
        cls.module = ast.parse(source.read_text(encoding="utf-8"))
        cls.handler = next(node for node in cls.module.body
                           if isinstance(node, ast.FunctionDef)
                           and node.name == "receive_wazuh_event")
        cls.source = ast.unparse(cls.handler)

    def test_c7_in_handler(self):
        self.assertIn("possible_ransomware_behavior", self.source)
        self.assertIn("assess_ransomware_from_database", self.source)

    def test_dedup_guard_precedes_shadow(self):
        self.assertLess(
            self.source.index("ux_events_wazuh_alert_id"),
            self.source.index("assess_ransomware_from_database"),
        )

    def test_existing_evaluators_preserved(self):
        for evaluator in (
            "assess_from_database",
            "assess_privilege_from_database",
            "assess_fim_from_database",
        ):
            self.assertIn(evaluator, self.source)

    def test_store_remains_shadow(self):
        self.assertIn("save_shadow_decision", self.source)
        self.assertIn("'mode': 'shadow'", self.source)


if __name__ == "__main__":
    unittest.main()
