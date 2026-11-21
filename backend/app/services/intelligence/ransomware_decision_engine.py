"""Evaluador c7 / MITRE T1486 de observación ransomware-like en Wazuh FIM.

La detección de alteración de un documento de demostración NO demuestra
cifrado real, ransomware activo ni identidad del atacante. Nunca ejecuta
CONTAIN_HOST, comandos de sistema ni respuestas automáticas.
"""
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1486"
CONTROL_ID = "c7"


def assess_ransomware_like(
    event: Mapping[str, Any], *,
    technique_exists: bool,
    control: Mapping[str, Any] | None,
) -> Decision:
    base = dict(
        technique_id=TECHNIQUE,
        control_id=CONTROL_ID,
        recommended_action=None,
        target=None,
        execution_allowed=False,
        executed=False,
    )
    if event.get("event_type") != "possible_ransomware_behavior":
        return Decision(
            status="not_applicable",
            reason="No es un evento ransomware-like.",
            **base,
        )

    details = event.get("details")
    if not isinstance(details, dict):
        details = {}

    if (
        event.get("source") != "wazuh"
        or details.get("integration") != "wazuh_real"
        or not isinstance(details.get("wazuh_alert_id"), str)
        or not details.get("wazuh_alert_id")
        or not isinstance(details.get("path"), str)
        or not details.get("path")
        or details.get("wazuh_event") not in ("added", "modified", "deleted")
    ):
        return Decision(
            status="needs_investigation",
            reason="No hay trazabilidad Wazuh FIM suficiente para esta señal.",
            **base,
        )
    if details.get("maintenance_mode") is True:
        return Decision(
            status="excluded",
            reason="El evento se declaró mantenimiento; no confirma amenaza.",
            **base,
        )
    if (
        details.get("lab_ransomware_signal") is not True
        or details.get("sensor_confirmed_ransomware_like") is not True
        or details.get("change_applied") is not True
        or details.get("detection_basis") not in ("behavior", "filename_and_behavior")
    ):
        return Decision(
            status="needs_investigation",
            reason="Wazuh observó una indicación, sin conducta de laboratorio corroborada.",
            **base,
        )
    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="La técnica T1486 no está en la base MITRE local.",
            **base,
        )
    if control is None:
        return Decision(
            status="control_unavailable",
            reason="No se encontró el control c7 para T1486.",
            **base,
        )
    if control.get("mode") != "integrated":
        return Decision(
            status="simulation_only",
            reason=(
                "Wazuh FIM confirmó cambio de archivo ficticio dentro del "
                "laboratorio ransomware-demo; c7 permanece en modo simulated. "
                "Esto no demuestra cifrado ni infección real."
            ),
            **base,
        )
    return Decision(
        status="needs_investigation",
        reason=(
            "Wazuh observó un cambio compatible con ransomware-like en "
            "laboratorio; falta evidencia independiente de cifrado o "
            "actividad maliciosa antes de recomendar contención."
        ),
        **base,
    )


def assess_ransomware_from_database(
    db: Session, event: Mapping[str, Any],
) -> Decision:
    technique_exists = bool(db.execute(text("""
        SELECT EXISTS(
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
        "technique": '[{"technique_id":"T1486"}]',
    }).mappings().first()
    return assess_ransomware_like(
        event,
        technique_exists=technique_exists,
        control=dict(control) if control else None,
    )
