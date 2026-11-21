"""Motor de observación c3 / MITRE T1565.001 para alertas FIM de Wazuh.

Un cambio de archivo no prueba manipulación maliciosa. Nunca bloquea, cambia
permisos ni ejecuta playbooks. La etiqueta 'authorized' proviene de reglas
del laboratorio, no de una verificación independiente de identidad.
"""
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1565.001"
CONTROL_ID = "c3"


def assess_fim_change(
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
    if event.get("event_type") != "suspicious_file_change":
        return Decision(
            status="not_applicable",
            reason="El evento no corresponde a cambios de integridad FIM.",
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
        or details.get("change_applied") is not True
    ):
        return Decision(
            status="needs_investigation",
            reason="No existe evidencia FIM completa para evaluar el cambio.",
            **base,
        )
    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="T1565.001 no está disponible en MITRE local.",
            **base,
        )
    if control is None or control.get("mode") != "integrated":
        return Decision(
            status="control_unavailable",
            reason="La protección c3 no está registrada como integrada.",
            **base,
        )

    if details.get("authorized") is True:
        return Decision(
            status="observed_authorized",
            reason=(
                "Wazuh FIM observó un cambio; la política actual del "
                "laboratorio lo clasifica como autorizado. FIM no prueba "
                "por sí solo la autorización del usuario."
            ),
            **base,
        )

    if (
        details.get("authorized") is False
        and details.get("file_criticality") in ("critical", "important")
    ):
        return Decision(
            status="needs_investigation",
            reason=(
                "Wazuh FIM observó un cambio en un archivo señalado como "
                "crítico o importante sin autorización comprobada. "
                "Se necesita revisión humana antes de cualquier contención."
            ),
            **base,
        )

    return Decision(
        status="needs_investigation",
        reason=(
            "Wazuh FIM registró un cambio, pero no hay evidencia suficiente "
            "para concluir si fue autorizado o malicioso."
        ),
        **base,
    )


def assess_fim_from_database(db: Session, event: Mapping[str, Any]) -> Decision:
    technique_exists = bool(db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM intelligence_mitre_techniques
            WHERE attack_id = :attack_id
        )
    """), {"attack_id": TECHNIQUE}).scalar_one())
    row = db.execute(text("""
        SELECT mode, execution_enabled, execution_verified
        FROM cybershield_protection_catalog
        WHERE control_id = :control_id
          AND origin = 'builtin'
          AND mitre_techniques @> CAST(:technique AS jsonb)
        LIMIT 1
    """), {
        "control_id": CONTROL_ID,
        "technique": '[{"technique_id":"T1565.001"}]',
    }).mappings().first()
    return assess_fim_change(
        event,
        technique_exists=technique_exists,
        control=dict(row) if row else None,
    )
