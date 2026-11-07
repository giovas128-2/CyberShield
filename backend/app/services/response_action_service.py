from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.response_action import ResponseAction
from app.services.notification_service import (
    create_response_notification,
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
    # NOTIFICACIÓN DEL RESULTADO
    # Dashboard + Telegram persistente
    # =========================================================

    create_response_notification(
        db=db,
        incident_id=incident.id,
        success=success,
        action_type=action.action_type,
        target=action.target,
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
    commit: bool = True,
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

    sensor_confirmed_exfiltration = bool(
        details.get(
            "sensor_confirmed_exfiltration",
            False,
        )
    )

    is_confirmed_suricata_exfiltration = (
        event_type == "possible_data_exfiltration"
        and sensor_confirmed_exfiltration
        and bool(
            details.get(
                "lab_exfiltration_signal",
                False,
            )
        )
        and details.get(
            "destination_ip"
        ) == "172.25.176.1"
        and int(
            details.get(
                "destination_port"
            ) or 0
        ) == 8765
    )

    is_confirmed_device_trust = (
        event_type == "unauthorized_device_access"
        and severity.lower() in ("high", "critical")
        and bool(details.get("device_trust_real", False))
        and not bool(details.get("allowed", True))
    )

    is_confirmed_critical_file_change = (
        event_type == "suspicious_file_change"
        and severity.lower() in ("high", "critical")
        and details.get("integration") == "wazuh_real"
        and not bool(details.get("authorized", True))
        and bool(details.get("change_applied", False))
        and details.get("file_criticality") in (
            "critical",
            "important",
        )
    )

    is_confirmed_sc5_suricata = (
        event_type == "suspicious_network_traffic"
        and severity.lower() in ("high", "critical")
        and details.get("integration") == "suricata_real"
        and int(details.get("signature_id") or 0) == 1000003
        and not bool(details.get("destination_allowed", True))
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

    # Simulación explícita y limitada del laboratorio.
    # NO se etiqueta como confirmación real de Wazuh.
    is_lab_privilege_simulation = (
        event_type == "privilege_escalation"
        and severity.lower() in ("high", "critical")
        and bool(
            details.get(
                "simulation",
                False,
            )
        )
        and details.get(
            "lab_scenario"
        ) == "sc4"
        and (
            details.get("user")
            or details.get("srcuser")
        ) == "priv_demo"
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
        and not is_confirmed_suricata_exfiltration
        and not is_confirmed_privilege_abuse
        and not is_lab_privilege_simulation
        and not is_confirmed_device_trust
        and not is_confirmed_critical_file_change
        and not is_confirmed_sc5_suricata
    ):
        return None

    if (
        not is_confirmed_ssh_bruteforce
        and event_type not in (
            "possible_data_exfiltration",
            "possible_lateral_movement",
            "possible_ransomware_behavior",
            "unauthorized_device_access",
            "suspicious_file_change",
            "suspicious_network_traffic",
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

        if is_lab_privilege_simulation:
            reason = (
                "Simulación controlada de abuso de "
                "privilegios sobre la cuenta priv_demo. "
                "CyberShield aplicará un bloqueo temporal "
                "y reversible exclusivamente en el laboratorio."
            )
        else:
            reason = (
                "Wazuh confirmó uso exitoso de sudo "
                "por una cuenta de laboratorio que "
                "no está autorizada como administradora. "
                "Se propone bloqueo temporal y reversible."
            )

    elif event_type == "unauthorized_device_access":
        if not is_confirmed_device_trust:
            return None

        target = details.get("device_uuid")

        if not target:
            return None

        action_type = "RESTRICT_DEVICE_ACCESS"
        duration_seconds = 180

        reason = (
            "CyberShield confirmó un intento de acceso desde "
            "un dispositivo no registrado o no confiable. "
            "Se mantiene la restricción de acceso y se registra "
            "la respuesta defensiva para verificación."
        )

    elif event_type == "suspicious_file_change":
        if not is_confirmed_critical_file_change:
            return None

        target = details.get("path")

        if not target:
            return None

        action_type = "PROTECT_CRITICAL_FILE"
        duration_seconds = 180

        reason = (
            "Wazuh FIM confirmó una modificación no autorizada "
            "sobre un archivo crítico del laboratorio. "
            "CyberShield aplicará protección temporal y reversible."
        )

    elif event_type == "suspicious_network_traffic":
        if not is_confirmed_sc5_suricata:
            return None

        destination_ip = details.get("dest_ip")
        destination_port = details.get("dest_port")

        if not destination_ip or not destination_port:
            return None

        action_type = "RESTRICT_OUTBOUND_CONNECTION"
        target = f"{destination_ip}:{destination_port}"
        duration_seconds = 180

        reason = (
            "Suricata confirmó la conexión saliente sospechosa "
            "del escenario SC5. CyberShield aplicará una "
            "restricción temporal y reversible sobre el destino."
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
            "Contención reversible seleccionada por "
            "comportamiento tipo ransomware confirmado "
            "en laboratorio. La acción será ejecutada por "
            "el bridge defensivo autorizado y su resultado "
            "será verificado por CyberShield."
        )
    elif event_type == "possible_data_exfiltration":
        destination_ip = details.get(
            "destination_ip"
        )

        if not destination_ip:
            return None

        action_type = "RESTRICT_DATA_FLOW"
        target = destination_ip
        duration_seconds = 180

        reason = (
            "Restricción reversible seleccionada por "
            "posible exfiltración confirmada por telemetría "
            "de Suricata. El bridge defensivo aplicará y "
            "verificará el bloqueo del flujo de laboratorio."
        )
    elif event_type == "possible_lateral_movement":
        if not source_ip:
            return None

        action_type = "RESTRICT_LATERAL_COMMUNICATION"
        target = source_ip
        duration_seconds = 180

        reason = (
            "Restricción reversible seleccionada por "
            "movimiento lateral SSH confirmado en laboratorio. "
            "El bridge defensivo aplicará el bloqueo temporal "
            "y CyberShield registrará su verificación."
        )
    if action_type is None:
        return None

    # =====================================================
    # EVITAR CONTENCIONES DUPLICADAS DEL MISMO DESTINO
    # =====================================================
    #
    # Si ya existe una restricción de datos activa para
    # el mismo destino, no creamos otra acción paralela.
    #
    # El evento/incidente puede conservarse como evidencia,
    # pero la infraestructura no necesita otra regla firewall.
    if action_type == "RESTRICT_DATA_FLOW":
        active_same_target = (
            db.query(ResponseAction)
            .filter(
                ResponseAction.action_type
                == "RESTRICT_DATA_FLOW",
                ResponseAction.target == target,
                ResponseAction.status.in_(
                    [
                        "pending",
                        "approved",
                        "executed",
                    ]
                ),
            )
            .order_by(
                ResponseAction.id.desc()
            )
            .first()
        )

        if active_same_target:
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

    if commit:
        db.commit()
        db.refresh(action)
    else:
        # Envía el INSERT dentro de la transacción actual
        # y asigna el ID, pero NO confirma los cambios.
        db.flush()

    return action