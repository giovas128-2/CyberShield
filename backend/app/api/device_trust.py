from app.core.auth_dependencies import require_roles
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database.connection import get_db
from app.schemas.device_trust import (
    DeviceCreate,
    DeviceResponse,
    UserDeviceCreate,
    UserDeviceResponse,
    SessionCreate,
    SessionResponse,
)
from app.services.device_trust_service import (
    list_devices,
    create_device,
    assign_device_to_user,
    list_sessions,
    create_session,
    revoke_session,
    evaluate_device_trust,
    create_access_event,
)

from app.schemas.event import SecurityEventRequest
from app.services.event_service import process_security_event

router = APIRouter(tags=["Device Trust"])


@router.get(
    "/devices",
    response_model=list[DeviceResponse],
    dependencies=[Depends(require_roles("admin", "engineer"))],
)
def get_devices(db: DBSession = Depends(get_db)):
    return list_devices(db)


@router.post(
    "/devices",
    response_model=DeviceResponse,
    dependencies=[Depends(require_roles("admin", "engineer"))],
)
def post_device(
    payload: DeviceCreate,
    db: DBSession = Depends(get_db),
):
    try:
        return create_device(
            db,
            device_uuid=payload.device_uuid,
            device_name=payload.device_name,
            platform=payload.platform,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/user-devices",
    response_model=UserDeviceResponse,
    dependencies=[Depends(require_roles("admin"))],
)
def post_user_device(
    payload: UserDeviceCreate,
    db: DBSession = Depends(get_db),
):
    try:
        return assign_device_to_user(
            db,
            user_id=payload.user_id,
            device_id=payload.device_id,
            is_primary=payload.is_primary,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    dependencies=[Depends(require_roles("admin", "engineer"))],
)
def get_sessions(db: DBSession = Depends(get_db)):
    return list_sessions(db)


@router.post(
    "/sessions",
    response_model=SessionResponse,
    dependencies=[Depends(require_roles("admin", "engineer"))],
)
def post_session(
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
):
    try:
        return create_session(
            db,
            user_id=payload.user_id,
            device_id=payload.device_id,
            source_ip=payload.source_ip,
            session_token_hash=payload.session_token_hash,
            expires_at=payload.expires_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/sessions/{session_id}/revoke",
    response_model=SessionResponse,
    dependencies=[Depends(require_roles("admin"))],
)
def post_revoke_session(
    session_id: int,
    db: DBSession = Depends(get_db),
):
    session = revoke_session(db, session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post("/access/evaluate")
def post_access_evaluate(
    user_id: int,
    device_uuid: str,
    source_ip: str | None = None,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(
        require_roles("admin", "engineer")
    ),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "No puedes evaluar dispositivos "
                "en nombre de otro usuario"
            ),
        )
    result = evaluate_device_trust(
        db,
        user_id=user_id,
        device_uuid=device_uuid,
        source_ip=source_ip,
    )

    create_access_event(
        db,
        user_id=user_id,
        device_id=result.get("device_id"),
        session_id=None,
        event_type=result["event_type"],
        decision=result["decision"],
        severity=result["severity"],
        source_ip=source_ip,
        details={
            "reason": result["reason"],
            "device_uuid": device_uuid,
            "allowed": result["allowed"],
        },
    )

    if result["event_type"] == "unauthorized_device_access":
        security_event = SecurityEventRequest(
            event_type="unauthorized_device_access",
            source="device_trust",
            source_ip=source_ip,
            server_id=2,
            description=(
                "Acceso restringido desde dispositivo "
                "no autorizado o no registrado"
            ),
            scope="BLOCKED",
            details={
                "auth_result": "success",
                "device_state": (
                    "unregistered"
                    if result["reason"] == "device_not_registered"
                    else "untrusted"
                ),
                "reason": result["reason"],
                "device_uuid": device_uuid,
                "allowed": result["allowed"],
                "device_trust_real": True,
            },
        )

        process_security_event(
            db,
            security_event,
        )

    return result
