from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.response_action import (
    ResponseActionCreate,
)
from app.services.response_action_service import (
    create_response_action,
    get_response_action_by_id,
    get_response_actions,
)


router = APIRouter(
    prefix="/response-actions",
    tags=["Response Actions"],
)


@router.get("")
def list_response_actions(
    incident_id: int | None = Query(
        default=None
    ),

    status: Literal[
        "pending",
        "approved",
        "executed",
        "failed",
        "rolled_back",
        "cancelled",
    ]
    | None = Query(default=None),

    action_type: Literal[
        "BLOCK_SOURCE_IP",
        "REVOKE_SESSION",
        "TEMPORARY_ACCOUNT_LOCK",
        "BLOCK_EGRESS",
        "ISOLATE_HOST",
    ]
    | None = Query(default=None),

    db: Session = Depends(get_db),
):
    actions = get_response_actions(
        db=db,
        incident_id=incident_id,
        status=status,
        action_type=action_type,
    )

    return actions


@router.get("/{action_id}")
def get_response_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    action = get_response_action_by_id(
        db,
        action_id,
    )

    if not action:
        raise HTTPException(
            status_code=404,
            detail="Response action no encontrada",
        )

    return action


@router.post("")
def create_action(
    data: ResponseActionCreate,
    db: Session = Depends(get_db),
):
    try:
        action = create_response_action(
            db=db,
            incident_id=data.incident_id,
            action_type=data.action_type,
            target=data.target,
            reversible=data.reversible,
            duration_seconds=data.duration_seconds,
            reason=data.reason,
        )

        return action

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )