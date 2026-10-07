from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ServerStatus = Literal[
    "online",
    "offline",
    "registered"
]


class ServerCreate(BaseModel):
    name: str
    ip_address: str
    status: ServerStatus = "offline"
    agent: str | None = None


class ServerResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    status: str
    agent: str | None
    created_at: datetime
    last_seen: datetime | None