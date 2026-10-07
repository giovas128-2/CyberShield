from typing import Any

from pydantic import BaseModel


class SecurityEventRequest(BaseModel):
    event_type: str
    source: str
    source_ip: str
    description: str
    details: dict[str, Any]