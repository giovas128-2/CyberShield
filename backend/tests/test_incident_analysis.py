"""Pruebas de interpretación y acceso a análisis de incidentes."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.services.intelligence.incident_analysis import analyze_incident
from app.api.incidents import get_incident_analysis

class IncidentAnalysisTests(unittest.TestCase):
    def test_lab_incident_not_real_attack(self):
        result = analyze_incident(
            {"id":555,"severity":"high","status":"open"},
            {"event_type":"multiple_login_attempts","source":"lab","scope":"REACHED","details":{"simulation":"true"}},
            {"technique_id":"T1110","technique_name":"Brute Force","tactic":"Credential Access"},
            None,
        )
        self.assertTrue(result["classification"]["simulated"])
        self.assertFalse(result["ai_generated"])
        self.assertEqual(result["classification"]["mitre_technique_id"],"T1110")
        self.assertIn("Sin acción",result["response_assessment"] if "Sin acción" in result["response_assessment"] else "Sin acción")
        self.assertIn("no hay acción",result["summary"].lower())

    def test_no_mitre_or_impact_inferred(self):
        result = analyze_incident(
            {"id":1,"severity":"medium","status":"open"},
            {"event_type":"unknown","source":"suricata","scope":None,"details":{}},
            None,None,
        )
        self.assertIsNone(result["classification"]["mitre_technique_id"])
        self.assertIsNone(result["classification"]["scope"])
        self.assertIn("No hay alcance confirmado",result["summary"])

    def test_response_execution_is_recorded_not_verified(self):
        result = analyze_incident(
            {"id":1,"severity":"critical"},
            {"event_type":"suspicious_file_change","source":"wazuh","scope":"IMPACT","details":{}},
            None,{"status":"executed"},
        )
        self.assertIn("comprobar evidencia",result["response_assessment"])
        self.assertEqual(result["classification"]["priority"],"urgente")

    def test_invalid_id_fails_before_db(self):
        db=MagicMock()
        with self.assertRaises(HTTPException) as ctx:
            get_incident_analysis(0,db,SimpleNamespace(id=1))
        self.assertEqual(ctx.exception.status_code,422)
        db.query.assert_not_called()

    def test_missing_incident(self):
        db=MagicMock()
        db.query.return_value.filter.return_value.first.return_value=None
        with self.assertRaises(HTTPException) as ctx:
            get_incident_analysis(123,db,SimpleNamespace(id=1))
        self.assertEqual(ctx.exception.status_code,404)

if __name__=="__main__":
    unittest.main()
