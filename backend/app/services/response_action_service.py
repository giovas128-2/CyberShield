from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.response_action import ResponseAction


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

    # Solo proponemos respuesta automática para
    # incidentes realmente críticos y con impacto comprobado.
    if severity.lower() != "critical":
        return None

    if scope != "IMPACT":
        return None

    # Protección básica:
    # no preparar bloqueo contra orígenes marcados como
    # administrativos o permitidos.
    if details.get("admin_protected", False):
        return None

    if details.get("allowlisted", False):
        return None

    action_type = None
    target = None
    duration_seconds = None
    reason = None

    # ---------------------------------------------------------
    # Política 1:
    # credenciales comprometidas / acceso no autorizado
    # ---------------------------------------------------------
    if event_type in (
        "authentication_burst",
        "authentication_failure",
        "multiple_login_attempts",
    ):
        if not source_ip:
            return None

        action_type = "BLOCK_SOURCE_IP"
        target = source_ip
        duration_seconds = 900

        reason = (
            "Incidente CRITICAL con IMPACT: "
            "acceso no autorizado o compromiso de "
            "autenticación confirmado"
        )

    # ---------------------------------------------------------
    # Más políticas se agregarán después:
    #
    # privilege_escalation
    # -> TEMPORARY_ACCOUNT_LOCK / REVOKE_SESSION
    #
    # data_exfiltration
    # -> BLOCK_EGRESS
    #
    # ransomware
    # -> ISOLATE_HOST
    #
    # movimiento lateral
    # -> REVOKE_SESSION / ISOLATE_HOST
    # ---------------------------------------------------------

    if action_type is None:
        return None

    # Evitar crear la misma acción dos veces
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