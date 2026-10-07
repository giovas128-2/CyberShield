from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.event import SecurityEventRequest
from app.services.event_service import process_security_event
from app.cybersecurity.wazuh_adapter import normalize_wazuh_event
from app.cybersecurity.suricata_adapter import normalize_suricata_event


router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"]
)


@router.post("/wazuh")
def receive_wazuh_event(
    raw_event: dict,
    db: Session = Depends(get_db)
):
    normalized = normalize_wazuh_event(raw_event)

    event = SecurityEventRequest(**normalized)

    return process_security_event(db, event)


@router.post("/suricata")
def receive_suricata_event(
    raw_event: dict,
    db: Session = Depends(get_db)
):
    normalized = normalize_suricata_event(raw_event)

    event = SecurityEventRequest(**normalized)

    return process_security_event(db, event)