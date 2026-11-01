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


class RemoteLabEventRequest(BaseModel):
    """
    Telemetría básica enviada desde otro dispositivo
    del laboratorio.

    El cliente NO puede decidir:
    - source_ip
    - event_type
    - severity
    - scope
    - confirmaciones de sensores

    La IP se obtiene del socket HTTP.
    """

    server_id: int | None = 2
    user: str | None = None

    description: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )
