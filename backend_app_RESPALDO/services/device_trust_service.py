from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.models.access_event import AccessEvent
from app.models.device import Device
from app.models.session import Session
from app.models.user_device import UserDevice


VALID_DEVICE_STATUS = {"trusted", "untrusted", "revoked"}
VALID_SESSION_STATUS = {"active", "revoked", "expired"}


def list_devices(db: DBSession) -> list[Device]:
    return db.query(Device).order_by(Device.id.desc()).all()


def get_device(db: DBSession, device_id: int) -> Optional[Device]:
    return db.query(Device).filter(Device.id == device_id).first()


def get_device_by_uuid(db: DBSession, device_uuid: str) -> Optional[Device]:
    return db.query(Device).filter(Device.device_uuid == device_uuid).first()


def create_device(
    db: DBSession,
    *,
    device_uuid: str,
    device_name: Optional[str] = None,
    platform: Optional[str] = None,
    status: str = "untrusted",
) -> Device:
    if status not in VALID_DEVICE_STATUS:
        raise ValueError(f"Invalid device status: {status}")

    existing = get_device_by_uuid(db, device_uuid)
    if existing:
        return existing

    device = Device(
        device_uuid=device_uuid,
        device_name=device_name,
        platform=platform,
        status=status,
    )

    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device_status(
    db: DBSession,
    device_id: int,
    status: str,
) -> Optional[Device]:
    if status not in VALID_DEVICE_STATUS:
        raise ValueError(f"Invalid device status: {status}")

    device = get_device(db, device_id)
    if not device:
        return None

    device.status = status
    device.last_seen = datetime.now(timezone.utc)

    db.commit()
    db.refresh(device)
    return device


def assign_device_to_user(
    db: DBSession,
    *,
    user_id: int,
    device_id: int,
    is_primary: bool = False,
) -> UserDevice:
    existing = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user_id,
            UserDevice.device_id == device_id,
        )
        .first()
    )

    if existing:
        return existing

    relation = UserDevice(
        user_id=user_id,
        device_id=device_id,
        is_primary=is_primary,
    )

    device = get_device(db, device_id)
    if device and device.status == "trusted":
        relation.trusted_at = datetime.now(timezone.utc)

    db.add(relation)
    db.commit()
    db.refresh(relation)
    return relation


def list_sessions(db: DBSession) -> list[Session]:
    return db.query(Session).order_by(Session.id.desc()).all()


def create_session(
    db: DBSession,
    *,
    user_id: int,
    device_id: Optional[int] = None,
    source_ip: Optional[str] = None,
    session_token_hash: Optional[str] = None,
    expires_at=None,
) -> Session:
    session = Session(
        user_id=user_id,
        device_id=device_id,
        source_ip=source_ip,
        session_token_hash=session_token_hash,
        status="active",
        expires_at=expires_at,
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def revoke_session(
    db: DBSession,
    session_id: int,
) -> Optional[Session]:
    session = db.query(Session).filter(Session.id == session_id).first()

    if not session:
        return None

    session.status = "revoked"
    session.revoked_at = datetime.now(timezone.utc)
    session.last_seen = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)
    return session


def create_access_event(
    db: DBSession,
    *,
    user_id: Optional[int],
    device_id: Optional[int],
    session_id: Optional[int],
    event_type: str,
    decision: str,
    severity: str,
    source_ip: Optional[str] = None,
    details: Optional[dict] = None,
) -> AccessEvent:
    event = AccessEvent(
        user_id=user_id,
        device_id=device_id,
        session_id=session_id,
        event_type=event_type,
        decision=decision,
        severity=severity,
        source_ip=source_ip,
        details=details or {},
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def evaluate_device_trust(
    db: DBSession,
    *,
    user_id: int,
    device_uuid: str,
    source_ip: Optional[str] = None,
) -> dict:
    device = get_device_by_uuid(db, device_uuid)

    if device is None:
        return {
            "allowed": False,
            "decision": "restricted",
            "severity": "HIGH",
            "event_type": "unauthorized_device_access",
            "reason": "device_not_registered",
            "device_id": None,
        }

    relation = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user_id,
            UserDevice.device_id == device.id,
        )
        .first()
    )

    if device.status == "revoked":
        return {
            "allowed": False,
            "decision": "blocked",
            "severity": "CRITICAL",
            "event_type": "unauthorized_device_access",
            "reason": "device_revoked",
            "device_id": device.id,
        }

    if device.status == "untrusted":
        return {
            "allowed": False,
            "decision": "restricted",
            "severity": "HIGH",
            "event_type": "unauthorized_device_access",
            "reason": "device_untrusted",
            "device_id": device.id,
        }

    if relation is None:
        return {
            "allowed": False,
            "decision": "restricted",
            "severity": "HIGH",
            "event_type": "unauthorized_device_access",
            "reason": "device_not_assigned_to_user",
            "device_id": device.id,
        }

    return {
        "allowed": True,
        "decision": "allowed",
        "severity": "NORMAL",
        "event_type": "device_access",
        "reason": "trusted_device",
        "device_id": device.id,
    }