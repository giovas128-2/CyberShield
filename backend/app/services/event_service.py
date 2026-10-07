from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.incident import Incident
from app.cybersecurity.rules import analyze_security_event


def process_security_event(db: Session, data):
    analysis = analyze_security_event(data)

    event = Event(
        event_type=data.event_type,
        source=data.source,
        severity=analysis["risk_level"],
        source_ip=data.source_ip,
        description=data.description,
        details=data.details
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    analysis = analyze_security_event(data)

    incident = None

    if analysis["create_incident"]:
        incident = Incident(
            event_id=event.id,
            severity=analysis["risk_level"],
            status="open"
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

    return {
        "success": True,
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "source_ip": str(event.source_ip),
            "description": event.description,
                "details": event.details,
            "created_at": event.created_at
        },
        "analysis": analysis,
        "incident": {
            "id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at
        } if incident else None
    }


def get_events(db: Session):
    events = (
        db.query(Event)
        .order_by(Event.id.desc())
        .all()
    )

    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "source_ip": str(event.source_ip),
            "description": event.description,
            "details": event.details,
            "created_at": event.created_at
        }
        for event in events
    ]