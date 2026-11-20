"""Pruebas del generador de borradores: sin red, sensores ni PostgreSQL."""
import unittest
from app.services.intelligence.protection_draft_generator import (
    generate_protection_drafts,
)

TECHNIQUES = [
    {"attack_id": "T1059", "name": "Command and Scripting Interpreter"},
    {"attack_id": "T1005", "name": "Data from Local System"},
    {"attack_id": "T1001.003", "name": "Protocol or Service Impersonation"},
    {"attack_id": "T1003.008", "name": "/etc/passwd and /etc/shadow"},
    {"attack_id": "T1110", "name": "Brute Force"},
]


class ProtectionDraftTests(unittest.TestCase):
    def test_only_known_recipe_ids(self):
        drafts = generate_protection_drafts(TECHNIQUES, [])
        self.assertEqual(len(drafts), 4)
        self.assertNotIn("T1110", [d.technique_id for d in drafts])

    def test_already_covered_excluded(self):
        controls = [{"mitre_techniques": [{"technique_id": "T1059"}]}]
        drafts = generate_protection_drafts(TECHNIQUES, controls)
        self.assertNotIn("T1059", [d.technique_id for d in drafts])
        self.assertEqual(len(drafts), 3)

    def test_empty_catalog_no_proposals(self):
        self.assertEqual(generate_protection_drafts([], []), ())

    def test_all_stay_nonexecuting_and_unverified(self):
        for draft in generate_protection_drafts(TECHNIQUES, []):
            self.assertEqual(draft.status, "review_required")
            self.assertEqual(draft.generation_mode, "deterministic_template")
            self.assertFalse(draft.telemetry_verified)
            self.assertFalse(draft.detection_verified)
            self.assertFalse(draft.execution_allowed)
            self.assertFalse(draft.executed)

    def test_process_telemetry_not_assumed(self):
        drafts = generate_protection_drafts(TECHNIQUES, [])
        t1059 = next(d for d in drafts if d.technique_id == "T1059")
        self.assertIn("si está habilitada", t1059.candidate_sensor)

    def test_credential_file_not_read_as_fim(self):
        drafts = generate_protection_drafts(TECHNIQUES, [])
        t1003 = next(d for d in drafts if d.technique_id == "T1003.008")
        self.assertIn("no lecturas", t1003.required_evidence)

    def test_deterministic_priority_and_limit(self):
        drafts = generate_protection_drafts(TECHNIQUES, [], limit=2)
        self.assertEqual(
            [d.technique_id for d in drafts], ["T1059", "T1001.003"]
        )

    def test_invalid_limits_rejected(self):
        for limit in (0, 51, True, -2):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    generate_protection_drafts(TECHNIQUES, [], limit=limit)

    def test_draft_data_serializable(self):
        draft = generate_protection_drafts(TECHNIQUES, [], limit=1)[0]
        self.assertEqual(draft.to_dict()["technique_id"], "T1059")


if __name__ == "__main__":
    unittest.main()
