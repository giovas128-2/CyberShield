"""Evaluación shadow c5, Suricata SC5. No ejecuta respuestas.

Una alerta IDS no prueba automáticamente destino no autorizado ni exfiltración.
"""
from typing import Any, Mapping
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1041"
CONTROL_ID = "c5"


def assess_suspicious_connection(
    event: Mapping[str, Any],
    *,
    technique_exists: bool,
    control: Mapping[str, Any] | None,
) -> Decision:
    base = dict(
        technique_id=TECHNIQUE, control_id=CONTROL_ID,
        recommended_action=None, target=None,
        execution_allowed=False, executed=False,
    )
    if event.get("event_type") != "suspicious_network_traffic":
        return Decision(
            status="not_applicable",
            reason="No corresponde a tráfico de red sospechoso.",
            **base,
        )
    details = event.get("details")
    if not isinstance(details, dict):
        details = {}
    if (
        event.get("source") != "suricata"
        or details.get("integration") != "suricata_real"
        or details.get("suricata_event_type") != "alert"
        or str(details.get("signature_id")) != "1000003"
        or details.get("destination_allowed") is not False
    ):
        return Decision(
            status="needs_investigation",
            reason="Falta evidencia de alerta SC5 1000003; sin contención.",
            **base,
        )
    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="T1041 no está disponible en MITRE local.",
            **base,
        )
    if control is None or control.get("mode") != "integrated":
        return Decision(
            status="control_unavailable",
            reason="La protección c5 no está integrada.",
            **base,
        )
    return Decision(
        status="needs_investigation",
        reason=(
            "Suricata detectó firma de laboratorio SC5 1000003. "
            "Se solicita revisión humana; destination_allowed=False "
            "indica presencia de alerta, no una política verificada. "
            "No se ha confirmado exfiltración ni se propone bloqueo."
        ),
        **base,
    )


def assess_connection_from_database(db: Session, event: Mapping[str, Any]) -> Decision:
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
        "technique": '[{"technique_id":"T1041"}]',
    }).mappings().first()

    return assess_suspicious_connection(
        event,
        technique_exists=technique_exists,
        control=dict(control) if control else None,
    )
