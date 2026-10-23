from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, IPvAnyAddress

class DeviceCreate(BaseModel):
    device_uuid: str
    device_name: Optional[str] = None
    platform: Optional[str] = None
    status: str = "untrusted"


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uuid: str
    device_name: Optional[str] = None
    platform: Optional[str] = None
    status: str
    first_seen: datetime
    last_seen: datetime


class UserDeviceCreate(BaseModel):
    user_id: int
    device_id: int
    is_primary: bool = False


class UserDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    device_id: int
    is_primary: bool
    trusted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime


class SessionCreate(BaseModel):
    user_id: int
    device_id: Optional[int] = None
    session_token_hash: Optional[str] = None
    status: str = "active"
    source_ip: Optional[str] = None
    expires_at: Optional[datetime] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    device_id: Optional[int] = None
    status: str
    source_ip: Optional[IPvAnyAddress] = None
    created_at: datetime
    last_seen: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class AccessEventCreate(BaseModel):
    user_id: Optional[int] = None
    device_id: Optional[int] = None
    session_id: Optional[int] = None
    event_type: str
    decision: str
    severity: str
    source_ip: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class AccessEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    device_id: Optional[int] = None
    session_id: Optional[int] = None
    event_type: str
    decision: str
    severity: str
    source_ip: Optional[IPvAnyAddress] = None
    details: Optional[dict[str, Any]] = None
    created_at: datetime