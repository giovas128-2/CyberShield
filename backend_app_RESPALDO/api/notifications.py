from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.notification_service import (
    get_notifications,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("")
def list_notifications(
    status: Literal[
        "pending",
        "sent",
        "failed",
    ]
    | None = Query(default=None),

    severity: Literal[
        "normal",
        "warning",
        "high",
        "critical",
    ]
    | None = Query(default=None),

    incident_id: int | None = Query(default=None),

    db: Session = Depends(get_db),
):
    return get_notifications(
        db=db,
        status=status,
        severity=severity,
        incident_id=incident_id,
    )