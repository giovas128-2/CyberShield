from typing import Literal

from pydantic import BaseModel


class IncidentStatusUpdate(BaseModel):
    status: Literal[
        "open",
        "investigating",
        "resolved"
    ]