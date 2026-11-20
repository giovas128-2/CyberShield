"""Evaluación en sombra del control c2 (Device Trust, T1078).

La evidencia se obtiene del AccessEvent creado por el backend y se corrobora
contra tablas de dispositivos. No ejecuta acciones ni cambia permisos.
La ausencia de registro NO demuestra compromiso ni inicio de sesión exitoso.
"""
from typing import Any, Mapping
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.intelligence.defensive_decision_engine import Decision

TECHNIQUE = "T1078"
CONTROL_ID = "c2"


def assess_device_access(
    evidence: Mapping[str, Any],
    *,
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
    if (
        evidence.get("event_type") != "unauthorized_device_access"
        or evidence.get("source") != "device_trust"
    ):
        return Decision(
            status="not_applicable",
            reason="No es una evaluación Device Trust del backend.",
            **base,
        )
    if (
        evidence.get("access_event_type") != "unauthorized_device_access"
        or evidence.get("user_confirmed") is not True
        or evidence.get("uuid_matches") is not True
        or evidence.get("allowed") is not False
        or evidence.get("access_allowed") is not False
    ):
        return Decision(
            status="needs_investigation",
            reason="No se pudo correlacionar el evento con una denegación de Device Trust.",
            **base,
        )
    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="T1078 no existe en el catálogo MITRE local.",
            **base,
        )
    if control is None or control.get("mode") != "integrated":
        return Decision(
            status="control_unavailable",
            reason="No existe una protección c2 integrada.",
            **base,
        )

    reason = evidence.get("reason")
    decision = evidence.get("access_decision")
    status = evidence.get("registered_device_status")
    linked = evidence.get("assigned_to_user")

    if reason == "device_not_registered":
        if (
            decision == "restricted"
            and evidence.get("device_id") is None
            and status is None
        ):
            return Decision(
                status="access_restricted",
                reason=(
                    "Device Trust restringió el acceso: no existe dispositivo "
                    "registrado para el identificador presentado. "
                    "No se ha verificado un inicio de sesión exitoso ni un ataque."
                ),
                **base,
            )
    elif reason == "device_revoked":
        if decision == "blocked" and status == "revoked":
            return Decision(
                status="access_restricted",
                reason=(
                    "Device Trust registró una denegación de dispositivo revocado. "
                    "No se autorizan nuevas acciones."
                ),
                **base,
            )
    elif reason == "device_untrusted":
        if decision == "restricted" and status == "untrusted":
            return Decision(
                status="access_restricted",
                reason="Device Trust restringió un dispositivo no confiable.",
                **base,
            )
    elif reason == "device_not_assigned_to_user":
        if (
            decision == "restricted"
            and status == "trusted"
            and linked is False
        ):
            return Decision(
                status="access_restricted",
                reason="Device Trust restringió un dispositivo que no está asignado al usuario.",
                **base,
            )

    return Decision(
        status="needs_investigation",
        reason="La denegación no coincide con el estado actual del registro de dispositivos.",
        **base,
    )


def assess_device_from_database(
    db: Session,
    event: Mapping[str, Any],
    *,
    access_event_id: int,
) -> Decision:
    """Consultas SELECT únicamente. Compara registro de acceso y evento."""
    details = event.get("details") or {}
    if not isinstance(details, dict):
        details = {}

    row = db.execute(text("""
        SELECT
            ae.event_type AS access_event_type,
            ae.decision AS access_decision,
            ae.details->>'reason' AS reason,
            ae.details->>'allowed' AS access_allowed,
            ae.device_id,
            (ae.user_id IS NOT NULL) AS user_confirmed,
            (ae.details->>'device_uuid' = :device_uuid) AS uuid_matches,
            d.status AS registered_device_status,
            EXISTS (
                SELECT 1 FROM user_devices ud
                WHERE ud.user_id = ae.user_id
                  AND ud.device_id = d.id
            ) AS assigned_to_user
        FROM access_events ae
        LEFT JOIN devices d ON d.device_uuid = ae.details->>'device_uuid'
        WHERE ae.id = :access_event_id
        LIMIT 1
    """), {
        "access_event_id": access_event_id,
        "device_uuid": details.get("device_uuid", ""),
    }).mappings().first()

    exists = bool(db.execute(text("""
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
        "technique": '[{"technique_id":"T1078"}]',
    }).mappings().first()

    evidence = dict(row) if row else {}
    evidence.update({
        "event_type": event.get("event_type"),
        "source": event.get("source"),
        "allowed": details.get("allowed"),
        "access_allowed": (
            row["access_allowed"] == "false" if row
            else None
        ),
        "uuid_matches": (
            row["uuid_matches"] is True if row
            else False
        ),
    })
    return assess_device_access(
        evidence,
        technique_exists=exists,
        control=dict(control) if control else None,
    )
