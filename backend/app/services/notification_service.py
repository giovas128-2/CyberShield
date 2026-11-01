from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.telegram_service import (
    send_telegram_message,
)

def create_telegram_notification(
    db: Session,
    incident_id: int,
    message: str,
):
    """
    Envía Telegram y registra el resultado real
    en la tabla notifications.

    Telegram puede fallar sin detener CyberShield.
    """

    result = send_telegram_message(
        message
    )

    sent = bool(
        result.get("sent", False)
    )

    notification = Notification(
        incident_id=incident_id,
        recipient="security_engineer",
        channel="telegram",
        status=(
            "sent"
            if sent
            else "failed"
        ),
        message=message,
        sent_at=(
            datetime.now(timezone.utc)
            if sent
            else None
        ),
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def create_incident_telegram_notification(
    db: Session,
    incident_id: int,
    severity: str,
    event_type: str,
    server_id: int | None = None,
):
    """
    Envía únicamente la notificación móvil inicial
    del incidente.

    Se mantiene separada de la transacción principal
    para que un fallo de Telegram no deshaga
    el evento/incidente almacenado.
    """

    severity_upper = severity.upper()

    if severity_upper not in ("HIGH", "CRITICAL"):
        return None

    telegram_message = (
        "🚨 CYBERSHIELD - ATAQUE DETECTADO\n\n"
        f"Incidente: {incident_id}\n"
        f"Severidad: {severity_upper}\n"
        f"Tipo: {event_type}\n"
        f"Servidor: "
        f"{server_id if server_id is not None else 'N/D'}\n\n"
        "CyberShield inició el proceso de análisis "
        "y respuesta defensiva."
    )

    return create_telegram_notification(
        db=db,
        incident_id=incident_id,
        message=telegram_message,
    )


def create_incident_notification(
    db: Session,
    incident_id: int,
    severity: str,
    event_type: str,
    server_id: int | None = None,
    commit: bool = True,
    send_telegram: bool = True,
):
    """
    Crea una notificación para incidentes HIGH o CRITICAL.
    Por ahora el canal real implementado es el dashboard.
    """

    severity_upper = severity.upper()

    if severity_upper not in ("HIGH", "CRITICAL"):
        return None

    server_text = (
        f" en servidor {server_id}"
        if server_id is not None
        else ""
    )

    message = (
        f"Incidente {severity_upper}: "
        f"{event_type}{server_text}"
    )

    notification = Notification(
        incident_id=incident_id,
        recipient="security_engineer",
        channel="dashboard",
        status="pending",
        message=message,
    )

    db.add(notification)

    if commit:
        db.commit()
        db.refresh(notification)
    else:
        # Se registra dentro de la transacción principal
        # sin confirmarla todavía.
        db.flush()

    # =========================================================
    # NOTIFICACIÓN MÓVIL TELEGRAM
    # =========================================================
    #
    # El fallo de Telegram NO afecta la creación del incidente
    # ni la notificación del dashboard.
    # =========================================================

    if send_telegram:
        create_incident_telegram_notification(
            db=db,
            incident_id=incident_id,
            severity=severity,
            event_type=event_type,
            server_id=server_id,
        )

    return notification


def create_response_notification(
    db: Session,
    incident_id: int,
    success: bool,
    action_type: str,
    target: str | None,
):
    """
    Registra el resultado de la respuesta defensiva
    en dashboard y Telegram.
    """

    now = datetime.now(
        timezone.utc
    )

    if success:
        dashboard_message = (
            f"Ataque contenido: "
            f"{action_type} ejecutado correctamente."
        )

        telegram_message = (
            "✅ CYBERSHIELD - ATAQUE CONTENIDO\n\n"
            f"Incidente: {incident_id}\n"
            f"Acción: {action_type}\n"
            f"Objetivo: {target or 'N/D'}\n"
            "Estado: CONTENIDO\n\n"
            "La respuesta defensiva fue ejecutada "
            "y verificada correctamente."
        )

    else:
        dashboard_message = (
            f"Ataque NO contenido: "
            f"{action_type}. "
            "Se requiere intervención."
        )

        telegram_message = (
            "⚠️ CYBERSHIELD - ATAQUE NO CONTENIDO\n\n"
            f"Incidente: {incident_id}\n"
            f"Acción: {action_type}\n"
            f"Objetivo: {target or 'N/D'}\n"
            "Estado: INTERVENCIÓN REQUERIDA\n\n"
            "La respuesta defensiva no logró "
            "contener el incidente."
        )

    dashboard_notification = Notification(
        incident_id=incident_id,
        recipient="security_engineer",
        channel="dashboard",
        status="sent",
        message=dashboard_message,
        sent_at=now,
    )

    db.add(
        dashboard_notification
    )
    db.commit()
    db.refresh(
        dashboard_notification
    )

    telegram_notification = (
        create_telegram_notification(
            db=db,
            incident_id=incident_id,
            message=telegram_message,
        )
    )

    return {
        "dashboard":
            dashboard_notification,
        "telegram":
            telegram_notification,
    }


def get_notifications(
    db: Session,
    status: str | None = None,
    severity: str | None = None,
    incident_id: int | None = None,
):
    """
    Lista las notificaciones más recientes.

    severity se obtiene mediante la relación lógica
    con incidents.
    """

    from app.models.incident import Incident

    query = (
        db.query(Notification, Incident)
        .join(
            Incident,
            Incident.id == Notification.incident_id,
        )
    )

    if status is not None:
        query = query.filter(
            Notification.status == status
        )

    if severity is not None:
        query = query.filter(
            Incident.severity == severity.lower()
        )

    if incident_id is not None:
        query = query.filter(
            Notification.incident_id == incident_id
        )

    rows = (
        query
        .order_by(Notification.id.desc())
        .all()
    )

    return [
        {
            "id": notification.id,
            "incident_id": notification.incident_id,
            "severity": incident.severity,
            "recipient": notification.recipient,
            "channel": notification.channel,
            "message": notification.message,
            "status": notification.status,
            "created_at": notification.created_at,
            "sent_at": notification.sent_at,
        }
        for notification, incident in rows
    ]