from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.incident import Incident
from app.cybersecurity.rules import analyze_security_event
from app.services.notification_service import (
    create_incident_notification,
)
from app.services.response_action_service import (
    create_automatic_response_action,
)
from app.services.incident_mitre_service import (
    create_automatic_incident_mitre,
)

def process_security_event(db: Session, data):
    analysis = analyze_security_event(data)

    details = dict(data.details or {})

    if getattr(data, "user", None):
        details["user"] = data.user

    scope = (
        getattr(data, "scope", None)
        or analysis.get("scope")
    )

    event = Event(
        event_type=data.event_type,
        source=data.source,
        severity=analysis["risk_level"],
        source_ip=data.source_ip,
        description=data.description,
        details=details,
        server_id=getattr(data, "server_id", None),
        scope=scope,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    incident = None
    notification = None
    response_action = None
    mitre = None

    correlated_incident = None

    # ==========================================================
    # CORRELACIÓN RANSOMWARE-LIKE
    # ==========================================================
    # Varios eventos FIM de la misma ráfaga representan
    # un solo incidente, no un incidente por archivo.
    if (
        analysis["create_incident"]
        and event.event_type == "possible_ransomware_behavior"
        and bool(
            (event.details or {}).get(
                "sensor_confirmed_ransomware_like",
                False,
            )
        )
    ):
        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(seconds=30)
        )

        correlated_incident = (
            db.query(Incident)
            .join(
                Event,
                Incident.event_id == Event.id,
            )
            .filter(
                Event.event_type
                == "possible_ransomware_behavior",
                Event.server_id == event.server_id,
                Event.id != event.id,
                Event.created_at >= cutoff,
            )
            .order_by(
                Incident.id.desc()
            )
            .first()
        )

    if correlated_incident:
        incident = correlated_incident

        analysis["create_incident"] = False
        analysis[
            "correlated_to_incident_id"
        ] = incident.id

    elif analysis["create_incident"]:
        incident = Incident(
            event_id=event.id,
            severity=analysis["risk_level"],
            status="open",
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        mitre = create_automatic_incident_mitre(
            db=db,
            incident_id=incident.id,
            event_type=event.event_type,
            details=event.details,
        )

        # HIGH y CRITICAL generan una notificación
        notification = create_incident_notification(
            db=db,
            incident_id=incident.id,
            severity=incident.severity,
            event_type=event.event_type,
            server_id=event.server_id,
        )
        response_action = create_automatic_response_action(
            db=db,
            incident_id=incident.id,
            event_type=event.event_type,
            severity=incident.severity,
            scope=event.scope,
            source_ip=(
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            details=event.details,
        )

    return {
        "success": True,

        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "source_ip": (
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            "server_id": event.server_id,
            "scope": event.scope,
            "description": event.description,
            "details": event.details,
            "created_at": event.created_at,
        },

        "analysis": analysis,

        "incident": {
            "id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,
        }
        if incident
        else None,

        "notification": {
            "id": notification.id,
            "incident_id": notification.incident_id,
            "recipient": notification.recipient,
            "channel": notification.channel,
            "status": notification.status,
            "message": notification.message,
            "created_at": notification.created_at,
            "sent_at": notification.sent_at,
        }
        if notification
        else None,

        "response_action": {
            "id": response_action.id,
            "incident_id": response_action.incident_id,
            "action_type": response_action.action_type,
            "target": response_action.target,
            "status": response_action.status,
            "reversible": response_action.reversible,
            "duration_seconds": response_action.duration_seconds,
            "reason": response_action.reason,
            "result": response_action.result,
            "created_at": response_action.created_at,
            "executed_at": response_action.executed_at,
            "rolled_back_at": response_action.rolled_back_at,
        }
        if response_action
        else None,
    "mitre": {
            "id": mitre.id,
            "incident_id": mitre.incident_id,
            "technique_id": mitre.technique_id,
            "technique_name": mitre.technique_name,
            "tactic": mitre.tactic,
            "reference_url": mitre.reference_url,
            "is_primary": mitre.is_primary,
            "notes": mitre.notes,
    }
    if mitre
    else None,
    }


def get_events(
    db: Session,
    limit: int = 100,
):
    events = (
        db.query(Event)
        .order_by(Event.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "source_ip": (
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            "server_id": event.server_id,
            "scope": event.scope,
            "description": event.description,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]


def get_event_stats(
    db: Session,
    window: str,
    server_id: int | None = None,
    source_ip: str | None = None,
    event_type: str | None = None,
    scope: str | None = None,
):
    if window == "1s":
        seconds = 1

    elif window == "60s":
        seconds = 60

    else:
        raise ValueError(
            "La ventana debe ser '1s' o '60s'"
        )

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=seconds)

    # ---------------------------------------------------------
    # Helper interno para aplicar los mismos filtros
    # ---------------------------------------------------------

    def apply_filters(query):
        query = query.filter(
            Event.created_at >= cutoff,
            Event.created_at <= now,
        )

        if server_id is not None:
            query = query.filter(
                Event.server_id == server_id
            )

        if source_ip is not None:
            query = query.filter(
                Event.source_ip == source_ip
            )

        if event_type is not None:
            query = query.filter(
                Event.event_type == event_type
            )

        if scope is not None:
            query = query.filter(
                Event.scope == scope
            )

        return query

    # ---------------------------------------------------------
    # Total
    # ---------------------------------------------------------

    total_events = apply_filters(
        db.query(Event)
    ).count()

    # ---------------------------------------------------------
    # Por origen
    # ---------------------------------------------------------

    source_rows = (
        apply_filters(
            db.query(
                Event.source_ip,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.source_ip)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    by_source = [
        {
            "source_ip": (
                str(row.source_ip)
                if row.source_ip
                else None
            ),
            "count": row.count,
        }
        for row in source_rows
    ]

    # ---------------------------------------------------------
    # Por tipo
    # ---------------------------------------------------------

    type_rows = (
        apply_filters(
            db.query(
                Event.event_type,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    by_type = [
        {
            "event_type": row.event_type,
            "count": row.count,
        }
        for row in type_rows
    ]

    # ---------------------------------------------------------
    # Por scope
    # ---------------------------------------------------------

    scope_rows = (
        apply_filters(
            db.query(
                Event.scope,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.scope)
        .all()
    )

    by_scope = {
        "BLOCKED": 0,
        "REACHED": 0,
        "IMPACT": 0,
    }

    unclassified = 0

    for row in scope_rows:
        if row.scope in by_scope:
            by_scope[row.scope] = row.count
        else:
            unclassified += row.count

    # ---------------------------------------------------------
    # Por servidor
    # ---------------------------------------------------------

    server_rows = (
        apply_filters(
            db.query(
                Event.server_id,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.server_id)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    by_server = [
        {
            "server_id": row.server_id,
            "count": row.count,
        }
        for row in server_rows
    ]

    return {
        "window": window,
        "window_seconds": seconds,
        "generated_at": now,

        "filters": {
            "server_id": server_id,
            "source_ip": source_ip,
            "event_type": event_type,
            "scope": scope,
        },

        "total_events": total_events,
        "by_source": by_source,
        "by_type": by_type,
        "by_scope": by_scope,
        "unclassified_scope": unclassified,
        "by_server": by_server,
    }
