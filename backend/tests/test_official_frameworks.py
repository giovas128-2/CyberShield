"""Pruebas sin red/BD: investigación de fuentes fijas y mapeo documental."""
import json
import unittest
from unittest.mock import MagicMock
import httpx

from app.services.intelligence.official_frameworks import (
    SOURCE_BY_KEY, CONTROL_REFERENCES, read_official_source,
    references_for_controls, version_from_page, table_exists, read_snapshots,
)


class OfficialFrameworkTests(unittest.TestCase):
    def transport(self, body, *, status=200, content_type="text/html"):
        return httpx.MockTransport(lambda request: httpx.Response(
            status, content=body, headers={"content-type": content_type}
        ))

    def test_current_mitre_release_extracted_from_official_page(self):
        text = "<h3>ATT&amp;CK v19.2</h3><h3>ATT&amp;CK v20.1</h3>"
        self.assertEqual(version_from_page("mitre", text), "20.1")
        found = read_official_source("mitre", transport=self.transport(text))
        self.assertEqual(found["version"], "20.1")
        self.assertEqual(len(found["fingerprint"]), 64)

    def test_nist_framework_version(self):
        body = "<h1>NIST Cybersecurity Framework</h1><h2>CSF 2.0</h2>"
        found = read_official_source("nist", transport=self.transport(body))
        self.assertEqual(found["version"], "2.0")

    def test_cis_controls_version(self):
        body = "<p>CIS Controls v8</p><p>CIS Controls v8.1</p>"
        found = read_official_source("cis", transport=self.transport(body))
        self.assertEqual(found["version"], "8.1")

    def test_version_not_found_is_not_claimed(self):
        with self.assertRaises(ValueError):
            version_from_page("nist", "<title>Unavailable</title>")

    def test_cisa_keeps_count_and_fingerprint(self):
        payload = {"catalogVersion": "2026.11.20",
                   "vulnerabilities": [
                       {"cveID": "CVE-2025-12345", "dateAdded": "2026-11-19"},
                       {"cveID": "CVE-2026-4567", "dateAdded": "2026-11-20"},
                   ]}
        found = read_official_source(
            "cisa", transport=self.transport(
                json.dumps(payload), content_type="application/json"
            )
        )
        self.assertEqual(found["version"], "2026.11.20")
        self.assertEqual(found["record_count"], 2)
        self.assertEqual(len(found["fingerprint"]), 64)

    def test_redirect_rejected_without_following_untrusted_host(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(
            302, headers={"location": "https://unknown.invalid/payload"}
        ))
        with self.assertRaises(ValueError):
            read_official_source("mitre", transport=transport)

    def test_all_four_sources_are_fixed_https(self):
        self.assertEqual(set(SOURCE_BY_KEY), {"mitre", "nist", "cis", "cisa"})
        self.assertTrue(all(s["url"].startswith("https://") for s in SOURCE_BY_KEY.values()))

    def test_eight_existing_controls_have_references_and_no_defense_commands(self):
        controls = [{"id": f"c{i}", "name": f"Control {i}", "mode": "integrated",
                     "mitre_techniques": [{"technique_id": "T1110"}]}
                    for i in range(1, 9)]
        mapped = references_for_controls(controls)
        self.assertEqual(len(mapped), 8)
        self.assertEqual(set(CONTROL_REFERENCES), {f"c{i}" for i in range(1, 9)})
        self.assertTrue(all(row["nist"] and row["cis"] for row in mapped))
        self.assertTrue(all(row["mitre"][0]["url"].startswith(
            "https://attack.mitre.org/techniques/T1110/") for row in mapped))
        self.assertNotIn("command", mapped[0])

    def test_without_migration_is_explicitly_unchecked(self):
        db = MagicMock()
        db.execute.return_value.scalar_one.return_value = None
        self.assertFalse(table_exists(db))
        statuses = read_snapshots(db)
        self.assertTrue(all(s["status"] == "not_checked" for s in statuses))


if __name__ == "__main__":
    unittest.main()
