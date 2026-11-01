from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


NotificationChannel = Literal[
    "dashboard",
    "email",
    "webhook",
    "sms",
]

NotificationStatus = Literal[
    "pending",
    "sent",
    "failed",
]


class NotificationResponse(BaseModel):
    id: int
    incident_id: int

    recipient: str
    channel: NotificationChannel
    status: NotificationStatus

    message: str

    created_at: datetime
    sent_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)