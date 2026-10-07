from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.models.event import Event
from app.models.incident import Incident


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db)
):
    users_count = db.query(User).count()
    events_count = db.query(Event).count()
    incidents_count = db.query(Incident).count()

    critical_incidents = (
        db.query(Incident)
        .filter(Incident.severity == "critical")
        .count()
    )

    high_incidents = (
        db.query(Incident)
        .filter(Incident.severity == "high")
        .count()
    )

    risk_score = (
        15
        + (critical_incidents * 25)
        + (high_incidents * 15)
    )

    risk_score = min(risk_score, 100)

    if risk_score < 30:
        status = "protected"
    elif risk_score < 60:
        status = "warning"
    else:
        status = "high_risk"

    return {
        "users": users_count,
        "servers": 1,
        "events": events_count,
        "incidents": incidents_count,
        "risk_score": risk_score,
        "status": status
    }