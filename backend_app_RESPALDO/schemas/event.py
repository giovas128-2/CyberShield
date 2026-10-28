from typing import Any, Literal

from pydantic import BaseModel, Field


EventScope = Literal["BLOCKED", "REACHED", "IMPACT"]


class SecurityEventRequest(BaseModel):
    event_type: str
    source: str
    source_ip: str | None = None

    server_id: int | None = None
    user: str | None = None

    description: str | None = None

    # En simulaciones/integraciones el backend seguirá
    # determinando la severidad cuando corresponda.
    scope: EventScope | None = None

    details: dict[str, Any] = Field(default_factory=dict)