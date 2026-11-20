"""Evaluador c8 / T1021.004 para sesiones SSH observadas por Wazuh.

Una autenticación SSH exitosa, incluso del usuario de laboratorio lateral_demo,
NO demuestra movimiento lateral malicioso ni compromiso. 'pair_authorized=False'
en el adaptador actual es un valor fijo y NO prueba falta de autorización.
No crea incidentes, recomendaciones ejecutables ni respuestas.
"""
from typing import Any, Mapping
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1021.004"
CONTROL_ID = "c8"


def assess_lateral_ssh(
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
    if event.get("event_type") != "possible_lateral_movement":
        return Decision(
            status="not_applicable",
            reason="No corresponde a una alerta de posible movimiento lateral.",
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
        or str(details.get("wazuh_rule_id")) != "100210"
        or details.get("protocol") != "ssh"
        or details.get("login_successful") is not True
        or details.get("sensor_confirmed_lateral") is not True
        or not details.get("srcip")
        or details.get("destination_user") != "lateral_demo"
    ):
        return Decision(
            status="needs_investigation",
            reason=(
                "Falta trazabilidad completa Wazuh SSH 100210 o la confirmación "
                "del escenario de laboratorio. Una sesión SSH no prueba ataque."
            ),
            **base,
        )
    if details.get("maintenance_mode") is True:
        return Decision(
            status="excluded",
            reason="Señal durante mantenimiento declarado; requiere contexto.",
            **base,
        )
    if details.get("allowlisted") is True or details.get("admin_protected") is True:
        return Decision(
            status="excluded",
            reason="Origen excluido por configuración de protección existente.",
            **base,
        )
    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="La técnica T1021.004 no está en el catálogo MITRE local.",
            **base,
        )
    if control is None:
        return Decision(
            status="control_unavailable",
            reason="El control c8 no está registrado para T1021.004.",
            **base,
        )
    if control.get("mode") != "integrated":
        return Decision(
            status="simulation_only",
            reason=(
                "Wazuh registró autenticación SSH del usuario de laboratorio "
                "lateral_demo mediante regla 100210. Control c8 simulated; "
                "no demuestra intrusión, desplazamiento real ni autorización "
                "independientemente verificada."
            ),
            **base,
        )
    return Decision(
        status="needs_investigation",
        reason=(
            "SSH de laboratorio observado por Wazuh; falta correlación entre "
            "equipos y política de autorizaciones comprobada. No se propone contención."
        ),
        **base,
    )


def assess_lateral_from_database(
    db: Session, event: Mapping[str, Any],
) -> Decision:
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
        "technique": '[{"technique_id":"T1021.004"}]',
    }).mappings().first()
    return assess_lateral_ssh(
        event,
        technique_exists=technique_exists,
        control=dict(row) if row else None,
    )
