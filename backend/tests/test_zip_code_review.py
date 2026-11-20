"""Pruebas desconectadas de archivos ZIP de código: seguridad + revisión real."""
import base64
import json
import os
import stat
import sys
import types
import unittest
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

from app.services.intelligence.archive_review import (
    analyze_zip, decode_archive, load_zip_sources, review_zip_with_ai,
)

def make_zip(entries: dict[str, str]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, code in entries.items():
            archive.writestr(name, code)
    return buffer.getvalue()

class ZipCodeReviewTests(unittest.TestCase):
    def test_scans_real_source_and_reports_file_and_line(self):
        raw = make_zip({"proyecto/src/main.py": "DEBUG = True\nx=eval(user_input)\n"})
        scan, files = analyze_zip(decode_archive(base64.b64encode(raw).decode()))
        self.assertEqual(scan["source"], "zip_static_rules")
        self.assertEqual(scan["files_scanned"], 1)
        self.assertEqual(len(files), 1)
        self.assertEqual(scan["execution"], "none")
        self.assertEqual(scan["incidents_created"], 0)
        self.assertEqual({f["cwe"] for f in scan["findings"]}, {"CWE-95","CWE-489"})
        self.assertEqual({f["line"] for f in scan["findings"]},{1,2})

    def test_ignores_dependencies_and_sensitive_environment_files(self):
        raw=make_zip({
            "project/src/app.py": "DEBUG = False\n",
            "project/node_modules/lib.py": "eval('skip')",
            "project/.env": "PASSWORD=should_not_be_read",
            "project/dist/generated.js": "eval('skip')",
        })
        scan, files=analyze_zip(raw)
        self.assertEqual(scan["files_scanned"],1)
        self.assertEqual(scan["findings_total"],0)
        self.assertEqual(scan["archive"]["skipped_noncode"],3)
        self.assertEqual(files[0]["path"],"project/src/app.py")

    def test_rejects_path_traversal(self):
        raw=make_zip({"../../outside.py":"print('unsafe')","src/a.py":"print('ok')"})
        with self.assertRaisesRegex(ValueError,"insegura"):
            analyze_zip(raw)

    def test_rejects_absolute_paths(self):
        raw=make_zip({"/etc/a.py":"print('unsafe')"})
        with self.assertRaisesRegex(ValueError,"insegura"):
            analyze_zip(raw)

    def test_rejects_symlinks(self):
        buffer=BytesIO()
        with ZipFile(buffer,"w") as archive:
            item=ZipInfo("src/link.py")
            item.create_system=3
            item.external_attr=(stat.S_IFLNK | 0o777)<<16
            archive.writestr(item,"../outside.py")
        with self.assertRaisesRegex(ValueError,"simbólicos"):
            load_zip_sources(buffer.getvalue())

    def test_invalid_archive_or_base64(self):
        with self.assertRaises(ValueError):
            analyze_zip(b"not a ZIP")
        with self.assertRaises(ValueError):
            decode_archive("##invalid##")

    def test_rejects_large_zip_before_base64_decode(self):
        with self.assertRaisesRegex(ValueError,"8 MB"):
            decode_archive("A"*10_666_680)

    def test_skips_oversized_source(self):
        raw=make_zip({"src/big.py":"x"*60_001,"src/ok.py":"print('ok')"})
        scan,_=analyze_zip(raw)
        self.assertEqual(scan["archive"]["skipped_oversized"],1)
        self.assertEqual(scan["files_scanned"],1)

    def test_handles_more_than_twenty_files_in_batches(self):
        raw=make_zip({f"src/file_{i}.py":"DEBUG = True\n" for i in range(25)})
        scan,_=analyze_zip(raw)
        self.assertEqual(scan["files_scanned"],25)
        self.assertEqual(scan["findings_total"],25)

    def test_limits_project_source_count(self):
        raw=make_zip({f"src/file_{i}.py":"pass\n" for i in range(161)})
        with self.assertRaisesRegex(ValueError,"160 archivos"):
            analyze_zip(raw)

    def test_without_ai_key_keeps_genuine_rule_findings(self):
        scan,files=analyze_zip(make_zip({"app.py":"DEBUG = True\n"}))
        with patch.dict(os.environ,{"OPENAI_API_KEY":""}):
            response=review_zip_with_ai(scan,files,True)
        self.assertEqual(response["mode"],"rules_only")
        self.assertEqual(scan["findings_total"],1)

    def test_ai_optin_reads_real_code_and_validates_extra_findings(self):
        observed=[]
        class Responses:
            def create(self,**kwargs):
                observed.append(kwargs["input"])
                return types.SimpleNamespace(output_text=json.dumps({
                    "summary":"Inspección tentativa de los fragmentos.",
                    "findings":[
                        {"file":"src/main.py","line":2,"title":"Comprobación ausente",
                         "severity":"medium","cwe":"CWE-20","recommendation":"Validar entrada."},
                        {"file":"missing.py","line":1,"title":"Ficticio",
                         "severity":"critical","cwe":"CWE-95","recommendation":"No guardar."}
                    ]
                }))
        class FakeOpenAI:
            def __init__(self,**kwargs):
                self.responses=Responses()
        scan,files=analyze_zip(make_zip({
            "src/main.py":"password = 'dummysecret_test'\nprint(user_input)\n"
        }))
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-only"}),patch.dict(sys.modules,{"openai":types.SimpleNamespace(OpenAI=FakeOpenAI)}):
            response=review_zip_with_ai(scan,files,True)
        self.assertEqual(response["mode"],"llm_code_review")
        self.assertEqual(scan["ai_files_sampled"],1)
        self.assertEqual(scan["findings_total"],2)  # regla local + una propuesta IA
        self.assertNotIn("dummysecret_test",observed[0])
        self.assertIn("print(user_input)",observed[0])
        self.assertEqual(scan["findings"][-1]["verification"],"unverified")

    def test_ai_failure_does_not_break_scan(self):
        class FakeOpenAI:
            def __init__(self,**kwargs):
                raise RuntimeError("Provider unavailable")
        scan,files=analyze_zip(make_zip({"src/main.py":"DEBUG = True\n"}))
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-only"}),patch.dict(sys.modules,{"openai":types.SimpleNamespace(OpenAI=FakeOpenAI)}):
            response=review_zip_with_ai(scan,files,True)
        self.assertEqual(response["mode"],"rules_only")
        self.assertEqual(scan["findings_total"],1)

if __name__ == "__main__":
    unittest.main()
