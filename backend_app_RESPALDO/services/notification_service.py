from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_incident_notification(
    db: Session,
    incident_id: int,
    severity: str,
    event_type: str,
    server_id: int | None = None,
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
    db.commit()
    db.refresh(notification)

    return notification


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