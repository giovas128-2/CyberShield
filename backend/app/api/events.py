from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.event import SecurityEventRequest
from app.services.event_service import (
    process_security_event,
    get_events,
    get_event_stats,
)


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.post("/simulate")
def simulate_event(
    data: SecurityEventRequest,
    db: Session = Depends(get_db),
):
    return process_security_event(db, data)


@router.get("/stats")
def event_stats(
    window: Literal["1s", "60s"] = Query(
        default="60s",
        description="Ventana móvil de estadísticas",
    ),
    server_id: int | None = Query(
        default=None,
    ),
    source_ip: str | None = Query(
        default=None,
    ),
    event_type: str | None = Query(
        default=None,
    ),
    scope: Literal[
        "BLOCKED",
        "REACHED",
        "IMPACT",
    ]
    | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    try:
        return get_event_stats(
            db=db,
            window=window,
            server_id=server_id,
            source_ip=source_ip,
            event_type=event_type,
            scope=scope,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("")
def list_events(
    db: Session = Depends(get_db),
):
    return get_events(db)