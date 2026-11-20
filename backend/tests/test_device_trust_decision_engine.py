"""Pruebas aisladas de decisión c2; no interactúan con usuarios reales."""
import unittest
from unittest.mock import MagicMock

from app.services.intelligence.device_trust_decision_engine import assess_device_from_database

from app.services.intelligence.device_trust_decision_engine import assess_device_access

CONTROL = {"mode": "integrated"}
BASE = {
    "event_type": "unauthorized_device_access",
    "source": "device_trust",
    "access_event_type": "unauthorized_device_access",
    "user_confirmed": True,
    "uuid_matches": True,
    "allowed": False,
    "access_allowed": False,
    "reason": "device_not_registered",
    "access_decision": "restricted",
    "device_id": None,
    "registered_device_status": None,
    "assigned_to_user": False,
}


class DeviceDecisionTests(unittest.TestCase):
    def assess(self, evidence=None, *, exists=True, control=CONTROL):
        return assess_device_access(
            evidence if evidence is not None else BASE,
            technique_exists=exists,
            control=control,
        )

    def test_unregistered_restricted_with_no_extra_action(self):
        decision = self.assess()
        self.assertEqual(decision.status, "access_restricted")
        self.assertEqual(decision.technique_id, "T1078")
        self.assertEqual(decision.control_id, "c2")
        self.assertIsNone(decision.recommended_action)
        self.assertFalse(decision.execution_allowed)
        self.assertFalse(decision.executed)

    def test_untrusted_device_restricted(self):
        evidence = {
            **BASE, "reason": "device_untrusted", "device_id": 2,
            "registered_device_status": "untrusted",
        }
        self.assertEqual(self.assess(evidence).status, "access_restricted")

    def test_revoked_device_blocked(self):
        evidence = {
            **BASE, "reason": "device_revoked", "device_id": 2,
            "registered_device_status": "revoked",
            "access_decision": "blocked",
        }
        self.assertEqual(self.assess(evidence).status, "access_restricted")

    def test_unassigned_trusted_device_restricted(self):
        evidence = {
            **BASE, "reason": "device_not_assigned_to_user",
            "device_id": 3, "registered_device_status": "trusted",
            "assigned_to_user": False,
        }
        self.assertEqual(self.assess(evidence).status, "access_restricted")

    def test_uuid_mismatch_requires_investigation(self):
        evidence = {**BASE, "uuid_matches": False}
        self.assertEqual(self.assess(evidence).status, "needs_investigation")

    def test_no_access_event_requires_investigation(self):
        evidence = {**BASE, "access_event_type": None}
        self.assertEqual(self.assess(evidence).status, "needs_investigation")

    def test_mismatched_registry_requires_investigation(self):
        evidence = {**BASE, "registered_device_status": "trusted"}
        self.assertEqual(self.assess(evidence).status, "needs_investigation")

    def test_missing_knowledge_and_control(self):
        self.assertEqual(self.assess(exists=False).status, "knowledge_missing")
        self.assertEqual(
            self.assess(control={"mode": "pending"}).status,
            "control_unavailable",
        )

    def test_database_denied_access_is_boolean_false(self):
        """Regression: JSONB 'false' must become False, not True."""
        db = MagicMock()
        access_row = {
            "access_event_type": "unauthorized_device_access",
            "access_decision": "restricted",
            "reason": "device_not_registered",
            "access_allowed": "false",
            "device_id": None,
            "user_confirmed": True,
            "uuid_matches": True,
            "registered_device_status": None,
            "assigned_to_user": False,
        }

        def query_response(statement, params):
            result = MagicMock()
            sql = str(statement)
            if "FROM access_events ae" in sql:
                result.mappings.return_value.first.return_value = access_row
            elif "intelligence_mitre_techniques" in sql:
                result.scalar_one.return_value = True
            elif "cybershield_protection_catalog" in sql:
                result.mappings.return_value.first.return_value = CONTROL
            else:
                raise AssertionError(f"Unexpected query: {sql}")
            return result

        db.execute.side_effect = query_response
        decision = assess_device_from_database(
            db,
            {
                "event_type": "unauthorized_device_access",
                "source": "device_trust",
                "details": {
                    "device_uuid": "lab-test-uuid",
                    "allowed": False,
                },
            },
            access_event_id=77,
        )
        self.assertEqual(decision.status, "access_restricted")
        self.assertFalse(decision.executed)
        self.assertFalse(decision.execution_allowed)

    def test_lab_event_not_accepted(self):
        evidence = {**BASE, "source": "lab"}
        self.assertEqual(self.assess(evidence).status, "not_applicable")


if __name__ == "__main__":
    unittest.main()
