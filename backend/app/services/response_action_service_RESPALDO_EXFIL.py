from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.response_action import ResponseAction
from app.services.telegram_service import (
    send_telegram_message,
)

def create_response_action(
    db: Session,
    incident_id: int,
    action_type: str,
    target: str | None,
    reversible: bool,
    duration_seconds: int | None,
    reason: str,
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        raise ValueError(
            f"No existe el incidente {incident_id}"
        )

    action = ResponseAction(
        incident_id=incident_id,
        action_type=action_type,
        target=target,
        status="pending",
        reversible=reversible,
        duration_seconds=duration_seconds,
        reason=reason,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


def get_response_actions(
    db: Session,
    incident_id: int | None = None,
    status: str | None = None,
    action_type: str | None = None,
):
    query = db.query(ResponseAction)

    if incident_id is not None:
        query = query.filter(
            ResponseAction.incident_id
            == incident_id
        )

    if status is not None:
        query = query.filter(
            ResponseAction.status == status
        )

    if action_type is not None:
        query = query.filter(
            ResponseAction.action_type
            == action_type
        )

    return (
        query
        .order_by(ResponseAction.id.desc())
        .all()
    )


def get_response_action_by_id(
    db: Session,
    action_id: int,
):
    return (
        db.query(ResponseAction)
        .filter(ResponseAction.id == action_id)
        .first()
    )

def get_latest_response_action_for_target(
    db: Session,
    action_type: str,
    target: str,
    statuses: list[str],
):
    """
    Busca la acción de respuesta más reciente que coincida
    con tipo, objetivo y alguno de los estados indicados.

    Se utiliza para correlacionar el resultado real de
    Wazuh Active Response con la acción creada previamente
    por CyberShield.
    """

    return (
        db.query(ResponseAction)
        .filter(
            ResponseAction.action_type
            == action_type,
            ResponseAction.target
            == target,
            ResponseAction.status.in_(
                statuses
            ),
        )
        .order_by(
            ResponseAction.id.desc()
        )
        .first()
    )

def register_execution_result(
    db: Session,
    action_id: int,
    success: bool,
    result: str,
):
    action = get_response_action_by_id(
        db,
        action_id,
    )

    if not action:
        raise ValueError(
            f"No existe la acción {action_id}"
        )

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == action.incident_id
        )
        .first()
    )

    if not incident:
        raise ValueError(
            f"No existe el incidente {action.incident_id}"
        )

    if success:
        action.status = "executed"
        action.executed_at = datetime.now(
            timezone.utc
        )

        # La acción defensiva fue ejecutada correctamente.
        # Consideramos el incidente contenido/resuelto.
        incident.status = "resolved"

    else:
        action.status = "failed"

        # La acción defensiva no pudo contener el incidente.
        # Se escala para intervención humana.
        incident.status = "escalated"

    action.result = result

    db.commit()

    db.refresh(action)
    db.refresh(incident)

    # =========================================================
    # NOTIFICACIÓN MÓVIL DEL RESULTADO
    # =========================================================

    if success:
        telegram_message = (
            "✅ CYBERSHIELD - ATAQUE CONTENIDO\n\n"
            f"Incidente: {incident.id}\n"
            f"Acción: {action.action_type}\n"
            f"Objetivo: {action.target or 'N/D'}\n"
            f"Estado: {action.status}\n\n"
            "La respuesta defensiva fue ejecutada "
            "correctamente."
        )

    else:
        telegram_message = (
            "⚠️ CYBERSHIELD - ATAQUE NO CONTENIDO\n\n"
            f"Incidente: {incident.id}\n"
            f"Acción: {action.action_type}\n"
            f"Objetivo: {action.target or 'N/D'}\n"
            f"Estado: {action.status}\n\n"
            "No fue posible completar la respuesta "
            "defensiva.\n"
            "Se requiere intervención del ingeniero "
            "de seguridad."
        )

    send_telegram_message(
        telegram_message
    )

    return action


def register_rollback_result(
    db: Session,
    action_id: int,
    success: bool,
    result: str,
):
    action = get_response_action_by_id(
        db,
        action_id,
    )

    if not action:
        raise ValueError(
            f"No existe la acción {action_id}"
        )

    if not action.reversible:
        raise ValueError(
            "La acción no está marcada como reversible"
        )

    if success:
        action.status = "rolled_back"
        action.rolled_back_at = datetime.now(
            timezone.utc
        )
    else:
        action.status = "failed"

    previous_result = action.result or ""

    if previous_result:
        action.result = (
            f"{previous_result}\n"
            f"ROLLBACK: {result}"
        )
    else:
        action.result = f"ROLLBACK: {result}"

    db.commit()
    db.refresh(action)

    return action


def create_automatic_response_action(
    db: Session,
    incident_id: int,
    event_type: str,
    severity: str,
    scope: str | None,
    source_ip: str | None,
    details: dict | None = None,
):
    """
    Evalúa una política de respuesta y, cuando corresponde,
    crea una acción PENDIENTE.

    IMPORTANTE:
    Esto NO ejecuta bloqueos reales.
    Solo registra la acción propuesta en response_actions.
    """

    details = details or {}

    sensor_confirmed_bruteforce = bool(
        details.get(
            "sensor_confirmed_bruteforce",
            False,
        )
    )

    is_confirmed_ssh_bruteforce = (
        event_type
        in (
            "authentication_burst",
            "authentication_failure",
            "multiple_login_attempts",
        )
        and severity.lower() == "high"
        and sensor_confirmed_bruteforce
    )

    sensor_confirmed_ransomware_like = bool(
        details.get(
            "sensor_confirmed_ransomware_like",
            False,
        )
    )

    is_confirmed_lab_ransomware = (
        event_type == "possible_ransomware_behavior"
        and severity.lower() in ("high", "critical")
        and sensor_confirmed_ransomware_like
    )

    is_confirmed_privilege_abuse = (
        event_type == "privilege_escalation"
        and severity.lower() in ("high", "critical")
        and bool(
            details.get(
                "sensor_confirmed_privilege",
                False,
            )
        )
        and bool(
            details.get(
                "sudo_used",
                False,
            )
        )
        and not bool(
            details.get(
                "authorized",
                True,
            )
        )
        and bool(
            details.get(
                "success",
                False,
            )
        )
    )

    if (
        severity.lower() != "critical"
        and event_type != "possible_lateral_movement"
        and not is_confirmed_ssh_bruteforce
        and not is_confirmed_lab_ransomware
        and not is_confirmed_privilege_abuse
    ):
        return None

    if (
        not is_confirmed_ssh_bruteforce
        and event_type not in (
            "possible_data_exfiltration",
            "possible_lateral_movement",
            "possible_ransomware_behavior",
        )
        and scope != "IMPACT"
    ):
        return None

    if details.get("admin_protected", False):
        return None

    if details.get("allowlisted", False):
        return None

    action_type = None
    target = None
    duration_seconds = None
    reason = None

    if event_type in (
        "authentication_burst",
        "authentication_failure",
        "multiple_login_attempts",
    ):
        if not source_ip:
            return None

        action_type = "BLOCK_SOURCE_IP"
        target = source_ip

        if sensor_confirmed_bruteforce:
            duration_seconds = 180

            reason = (
                "Wazuh confirmó fuerza bruta SSH mediante "
                "la regla correlacionada 5763. "
                "Se propone bloqueo temporal y reversible "
                "de la IP de origen mediante Active Response."
            )

        else:
            duration_seconds = 900

            reason = (
                "Incidente CRITICAL con IMPACT: "
                "acceso no autorizado o compromiso de "
                "autenticación confirmado."
            )
    elif event_type == "privilege_escalation":
        target_user = (
            details.get("user")
            or details.get("srcuser")
        )

        # Defensa exclusivamente sobre la
        # cuenta de laboratorio permitida.
        if target_user != "priv_demo":
            return None

        action_type = "TEMPORARY_ACCOUNT_LOCK"
        target = target_user
        duration_seconds = 180

        reason = (
            "Wazuh confirmó uso exitoso de sudo "
            "por una cuenta de laboratorio que "
            "no está autorizada como administradora. "
            "Se propone bloqueo temporal y reversible."
        )

    elif event_type == "possible_ransomware_behavior":
        target = (
            source_ip
            or details.get("agent_name")
        )

        if not target:
            return None

        action_type = "CONTAIN_HOST"
        duration_seconds = 180

        reason = (
            "Propuesta de contención reversible por "
            "comportamiento tipo ransomware en laboratorio. "
            "La acción queda PENDIENTE y no ejecuta "
            "aislamiento real automáticamente."
        )
    elif event_type == "possible_data_exfiltration":
        if not source_ip:
            return None

        action_type = "RESTRICT_DATA_FLOW"
        target = source_ip
        duration_seconds = 180

        reason = (
            "Propuesta de restricción reversible del flujo de datos "
            "por posible exfiltración en laboratorio. "
            "La acción queda PENDIENTE y no ejecuta "
            "bloqueo real automáticamente."
        )
    elif event_type == "possible_lateral_movement":
        if not source_ip:
            return None

        action_type = "RESTRICT_LATERAL_COMMUNICATION"
        target = source_ip
        duration_seconds = 180

        reason = (
            "Propuesta de restricción reversible de comunicación "
            "por posible movimiento lateral mediante SSH en laboratorio. "
            "La acción queda PENDIENTE y no ejecuta "
            "bloqueo real automáticamente."
        )
    if action_type is None:
        return None

    existing = (
        db.query(ResponseAction)
        .filter(
            ResponseAction.incident_id == incident_id,
            ResponseAction.action_type == action_type,
            ResponseAction.target == target,
            ResponseAction.status.in_(
                [
                    "pending",
                    "approved",
                    "executed",
                ]
            ),
        )
        .first()
    )

    if existing:
        return existing

    action = ResponseAction(
        incident_id=incident_id,
        action_type=action_type,
        target=target,
        status="pending",
        reversible=True,
        duration_seconds=duration_seconds,
        reason=reason,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action