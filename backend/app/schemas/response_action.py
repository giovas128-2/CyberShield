from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ResponseActionType = Literal[
    "BLOCK_SOURCE_IP",
    "REVOKE_SESSION",
    "TEMPORARY_ACCOUNT_LOCK",
    "BLOCK_EGRESS",
    "ISOLATE_HOST",
]


ResponseActionStatus = Literal[
    "pending",
    "approved",
    "executed",
    "failed",
    "rolled_back",
    "cancelled",
]


class ResponseActionCreate(BaseModel):
    incident_id: int
    action_type: ResponseActionType

    target: str | None = None

    reversible: bool = True

    duration_seconds: int | None = None

    reason: str


class ResponseActionResponse(BaseModel):
    id: int
    incident_id: int

    action_type: ResponseActionType
    target: str | None

    status: ResponseActionStatus
    reversible: bool

    duration_seconds: int | None

    reason: str
    result: str | None

    created_at: datetime
    executed_at: datetime | None
    rolled_back_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )