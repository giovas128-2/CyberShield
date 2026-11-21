"""Pruebas de cobertura sin PostgreSQL ni ejecución de protecciones."""
import unittest

from app.services.intelligence.coverage_gap_analyzer import build_coverage_report


class CoverageGapTests(unittest.TestCase):
    def setUp(self):
        self.techniques = [
            {"attack_id": "T1041", "name": "Exfiltration"},
            {"attack_id": "T1110", "name": "Brute Force"},
            {"attack_id": "T1486", "name": "Data Encrypted for Impact"},
            {"attack_id": "T1059", "name": "Command Interpreter"},
        ]
        self.controls = [
            {
                "control_id": "c1", "mode": "integrated",
                "execution_verified": False,
                "mitre_techniques": [{"technique_id": "T1110"}],
            },
            {
                "control_id": "c5", "mode": "integrated",
                "execution_verified": False,
                "mitre_techniques": [{"technique_id": "T1041"}],
            },
            {
                "control_id": "c6", "mode": "simulated",
                "execution_verified": False,
                "mitre_techniques": [{"technique_id": "T1041"}],
            },
        ]

    def test_duplicate_controls_not_double_counted(self):
        report = build_coverage_report(self.techniques, self.controls)
        self.assertEqual(report.catalog_controls, 3)
        self.assertEqual(report.referenced_techniques, 2)
        self.assertEqual(report.referenced_in_mitre, 2)
        self.assertEqual(report.uncovered_techniques, 2)

    def test_no_verified_control(self):
        report = build_coverage_report(self.techniques, self.controls)
        self.assertEqual(report.execution_verified_associations, 0)
        self.assertEqual(report.integrated_associations, 2)

    def test_uncovered_preview_deterministic(self):
        report = build_coverage_report(self.techniques, self.controls)
        self.assertEqual(
            report.uncovered_preview,
            (("T1059", "Command Interpreter"), ("T1486", "Data Encrypted for Impact")),
        )

    def test_unknown_mitre_id_reported(self):
        controls = self.controls + [{
            "control_id": "c99", "mode": "simulated",
            "execution_verified": False,
            "mitre_techniques": [{"technique_id": "T9999"}],
        }]
        result = build_coverage_report(self.techniques, controls)
        self.assertEqual(result.unknown_references, ("T9999",))
        self.assertEqual(result.uncovered_techniques, 2)

    def test_multiple_techniques_per_control(self):
        controls = [{
            "mode": "simulated", "execution_verified": False,
            "mitre_techniques": [
                {"technique_id": "T1110"}, {"technique_id": "T1486"},
            ],
        }]
        result = build_coverage_report(self.techniques, controls)
        self.assertEqual(result.referenced_in_mitre, 2)

    def test_invalid_json_catalog_entry_ignored(self):
        controls = [{
            "mode": "integrated", "execution_verified": False,
            "mitre_techniques": {"technique_id": "T1110"},
        }]
        result = build_coverage_report(self.techniques, controls)
        self.assertEqual(result.referenced_techniques, 0)

    def test_preview_limit(self):
        report = build_coverage_report(self.techniques, self.controls, preview_limit=1)
        self.assertEqual(len(report.uncovered_preview), 1)

    def test_rejects_invalid_preview(self):
        with self.assertRaises(ValueError):
            build_coverage_report(self.techniques, self.controls, preview_limit=-1)


if __name__ == "__main__":
    unittest.main()
