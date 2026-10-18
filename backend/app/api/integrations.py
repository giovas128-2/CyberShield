from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.schemas.event import (
    SecurityEventRequest,
)

from app.services.event_service import (
    process_security_event,
)

from app.cybersecurity.wazuh_adapter import (
    normalize_wazuh_event,
)

from app.cybersecurity.suricata_adapter import (
    normalize_suricata_event,
)

from app.models.server import Server


router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
)


def validate_server(
    db: Session,
    server_id: int,
):
    server = (
        db.query(Server)
        .filter(Server.id == server_id)
        .first()
    )

    if not server:
        raise HTTPException(
            status_code=404,
            detail=f"No existe server_id={server_id}",
        )

    return server


@router.post("/wazuh")
def receive_wazuh_event(
    raw_event: dict,

    server_id: int = Query(
        default=2,
        description=(
            "Servidor CyberShield que generó "
            "la alerta. En el laboratorio actual "
            "srv-cyber-01 corresponde al ID 2."
        ),
    ),

    db: Session = Depends(get_db),
):
    validate_server(
        db,
        server_id,
    )

    normalized = normalize_wazuh_event(
        raw_event=raw_event,
        server_id=server_id,
    )

    event = SecurityEventRequest(
        **normalized
    )

    return process_security_event(
        db,
        event,
    )


@router.post("/suricata")
def receive_suricata_event(
    raw_event: dict,

    server_id: int = Query(
        default=2,
        description=(
            "Servidor asociado al sensor "
            "Suricata del laboratorio."
        ),
    ),

    db: Session = Depends(get_db),
):
    validate_server(
        db,
        server_id,
    )

    normalized = normalize_suricata_event(
        raw_event=raw_event,
        server_id=server_id,
    )

    event = SecurityEventRequest(
        **normalized
    )

    return process_security_event(
        db,
        event,
    )