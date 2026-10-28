from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.incident import Incident
from app.models.event import Event
from app.models.incident_mitre import IncidentMitre
from app.models.response_action import ResponseAction
from app.schemas.incident import IncidentStatusUpdate
from app.cybersecurity.investigation import get_investigation_guide


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.get("")
def list_incidents(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Incident, Event)
        .join(
            Event,
            Event.id == Incident.event_id,
        )
        .order_by(Incident.id.desc())
        .all()
    )

    result = []

    for incident, event in rows:
        guide = get_investigation_guide(
            event.event_type
        )

        mitre = (
            db.query(IncidentMitre)
            .filter(
                IncidentMitre.incident_id
                == incident.id
            )
            .order_by(
                IncidentMitre.is_primary.desc(),
                IncidentMitre.id.asc(),
            )
            .first()
        )

        response_action = (
            db.query(ResponseAction)
            .filter(
                ResponseAction.incident_id
                == incident.id
            )
            .order_by(
                ResponseAction.id.desc()
            )
            .first()
        )

        result.append({
            "id": incident.id,
            "event_id": incident.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "source_ip": (
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,

            "mitre": {
                "id": mitre.id,
                "technique_id": mitre.technique_id,
                "technique_name": mitre.technique_name,
                "tactic": mitre.tactic,
                "reference_url": mitre.reference_url,
                "is_primary": mitre.is_primary,
                "notes": mitre.notes,
            }
            if mitre
            else None,

            "response_action": {
                "id": response_action.id,
                "action_type": response_action.action_type,
                "target": response_action.target,
                "status": response_action.status,
                "reversible": response_action.reversible,
                "duration_seconds": (
                    response_action.duration_seconds
                ),
                "reason": response_action.reason,
                "result": response_action.result,
                "created_at": response_action.created_at,
                "executed_at": response_action.executed_at,
                "rolled_back_at": (
                    response_action.rolled_back_at
                ),
            }
            if response_action
            else None,

            "recommendation": guide[
                "recommendation"
            ],

            "investigation_steps": guide[
                "investigation_steps"
            ],

            "resolution_criteria": guide[
                "resolution_criteria"
            ],
        })

    return result


@router.patch("/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incidente no encontrado",
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
        "message": (
            "Estado del incidente actualizado"
        ),
        "incident": {
            "id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,
        },
    }
