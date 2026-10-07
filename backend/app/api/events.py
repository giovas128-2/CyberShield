from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.event import SecurityEventRequest
from app.services.event_service import process_security_event, get_events


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


@router.post("/simulate")
def simulate_event(
    data: SecurityEventRequest,
    db: Session = Depends(get_db)
):
    return process_security_event(db, data)


@router.get("")
def list_events(
    db: Session = Depends(get_db)
):
    return get_events(db)