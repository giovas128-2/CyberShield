from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.incident import Incident
from app.models.event import Event
from app.schemas.incident import IncidentStatusUpdate
from app.cybersecurity.investigation import get_investigation_guide


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


@router.get("")
def list_incidents(
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Incident, Event)
        .join(
            Event,
            Event.id == Incident.event_id
        )
        .order_by(Incident.id.desc())
        .all()
    )

    result = []

    for incident, event in rows:
        guide = get_investigation_guide(
            event.event_type
        )

        result.append({
            "id": incident.id,
            "event_id": incident.event_id,
            "event_type": event.event_type,
            "source_ip": str(event.source_ip),
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,

            "recommendation": guide[
                "recommendation"
            ],

            "investigation_steps": guide[
                "investigation_steps"
            ],

            "resolution_criteria": guide[
                "resolution_criteria"
            ]
        })

    return result


@router.patch("/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incidente no encontrado"
        )

    incident.status = data.status

    try:
        db.commit()
        db.refresh(incident)

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Estado del incidente actualizado",
        "incident": {
            "id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at
        }
    }