"""Motor shadow c6 (T1041): análisis de evidencia de laboratorio Suricata.

Los indicadores llamados sensor_confirmed_exfiltration describen una señal
del laboratorio; no certifican una fuga no autorizada de información.
Este módulo solo lee catálogo y nunca ejecuta defensas.
"""
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1041"
CONTROL_ID = "c6"
LAB_DEST_IP = "172.25.176.1"
LAB_DEST_PORT = 8765
MIN_BYTES = 10_000_000


def assess_exfiltration(
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

    if event.get("event_type") != "possible_data_exfiltration":
        return Decision(
            status="not_applicable",
            reason="No pertenece a la familia de posible exfiltración.",
            **base,
        )

    details = event.get("details")
    if not isinstance(details, dict):
        details = {}

    # Las señales se evalúan solo para eventos normalizados del sensor,
    # nunca para simulaciones manuales ni JSON incompleto.
    if (
        event.get("source") != "suricata"
        or details.get("integration") != "suricata_real"
        or details.get("sensor_confirmed_exfiltration") is not True
        or details.get("lab_exfiltration_signal") is not True
        or details.get("dest_ip") != LAB_DEST_IP
        or type(details.get("dest_port")) is not int
        or details["dest_port"] != LAB_DEST_PORT
    ):
        return Decision(
            status="needs_investigation",
            reason="Evidencia de sensor/laboratorio insuficiente o incongruente.",
            **base,
        )

    sensor_event = details.get("suricata_event_type")
    is_lab_alert = (
        sensor_event == "alert"
        and str(details.get("signature_id")) == "1000002"
    )
    bytes_up = details.get("bytes_toserver_total")
    if bytes_up is None:
        bytes_up = details.get("bytes_toserver")
    is_bulk_flow = (
        sensor_event == "flow"
        and type(bytes_up) is int
        and bytes_up >= MIN_BYTES
    )
    if not (is_lab_alert or is_bulk_flow):
        return Decision(
            status="needs_investigation",
            reason="No coincide con la firma 1000002 ni el umbral de flujo del laboratorio.",
            **base,
        )

    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="T1041 no existe en la base MITRE local.",
            **base,
        )

    if control is None:
        return Decision(
            status="control_unavailable",
            reason="No existe catálogo c6 para la técnica T1041.",
            **base,
        )

    if control.get("mode") != "integrated":
        return Decision(
            status="simulation_only",
            reason=(
                "Suricata observó una señal de exfiltración controlada, "
                "pero el catálogo c6 sigue en modo simulated. "
                "No se acredita una exfiltración no autorizada; "
                "se requiere revisión humana y validación del control."
            ),
            **base,
        )

    return Decision(
        status="needs_investigation",
        reason=(
            "Suricata observó firma 1000002 o transferencia controlada de "
            "al menos 10 MB. La telemetría no demuestra por sí sola "
            "filtración no autorizada. No se recomienda bloqueo."
        ),
        **base,
    )


def assess_exfiltration_from_database(
    db: Session, event: Mapping[str, Any]
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
        "technique": '[{"technique_id":"T1041"}]',
    }).mappings().first()

    return assess_exfiltration(
        event,
        technique_exists=technique_exists,
        control=dict(row) if row else None,
    )
