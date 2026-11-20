"""Evaluación no ejecutable de uso de sudo (MITRE T1548.003).

La regla 5402 confirma uso exitoso de sudo, NO confirma abuso.
La autorización del usuario proviene hoy de una allowlist de laboratorio;
no debe utilizarse como evidencia definitiva de compromiso ni para bloqueo.
"""
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1548.003"
CONTROL_ID = "c4"


def assess_sudo_privilege(
    event: Mapping[str, Any],
    *,
    technique_exists: bool,
    control: Mapping[str, Any] | None,
) -> Decision:
    base = {
        "technique_id": TECHNIQUE,
        "control_id": CONTROL_ID,
        "recommended_action": None,
        "target": None,
        "execution_allowed": False,
        "executed": False,
    }
    if event.get("event_type") != "privilege_escalation":
        return Decision(
            status="not_applicable",
            reason="El evento no corresponde a uso de privilegios.",
            **base,
        )
    details = event.get("details")
    if not isinstance(details, dict):
        details = {}
    if (
        event.get("source") != "wazuh"
        or str(details.get("wazuh_rule_id")) != "5402"
        or details.get("sensor_confirmed_privilege") is not True
        or details.get("sudo_used") is not True
        or details.get("success") is not True
    ):
        return Decision(
            status="needs_investigation",
            reason="No hay evidencia completa de uso exitoso de sudo mediante regla 5402.",
            **base,
        )
    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="La técnica T1548.003 no está en MITRE local.",
            **base,
        )
    if control is None or control.get("mode") != "integrated":
        return Decision(
            status="control_unavailable",
            reason="La protección c4 no está registrada como integrada.",
            **base,
        )
    if details.get("authorized") is True:
        return Decision(
            status="observed_authorized",
            reason=(
                "Wazuh registró sudo exitoso de un usuario permitido por la "
                "configuración actual del laboratorio; no existe evidencia "
                "suficiente de abuso. No se propone bloqueo."
            ),
            **base,
        )
    return Decision(
        status="needs_investigation",
        reason=(
            "Wazuh registró sudo exitoso de un usuario no permitido o "
            "sin autorización comprobada. Se requiere revisión humana; "
            "la regla 5402 no prueba por sí sola una intrusión."
        ),
        **base,
    )


def assess_privilege_from_database(db: Session, event: Mapping[str, Any]) -> Decision:
    technique_exists = bool(db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM intelligence_mitre_techniques
            WHERE attack_id = :attack_id
        )
    """), {"attack_id": TECHNIQUE}).scalar_one())

    control = db.execute(text("""
        SELECT mode, execution_enabled, execution_verified
        FROM cybershield_protection_catalog
        WHERE control_id = :control_id
          AND origin = 'builtin'
          AND mitre_techniques @> CAST(:technique AS jsonb)
        LIMIT 1
    """), {
        "control_id": CONTROL_ID,
        "technique": '[{"technique_id":"T1548.003"}]',
    }).mappings().first()
    return assess_sudo_privilege(
        event,
        technique_exists=technique_exists,
        control=dict(control) if control else None,
    )
