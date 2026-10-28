import os
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.event import Event
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.event import SecurityEventRequest
from app.services.auth_service import (
    register_user,
    login_user,
)
from app.services.event_service import process_security_event


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv(
        "CYBERSHIELD_ADMIN_EMAILS",
        "yahirgonzalez@gmail.com,admin.demo@cybershield.local",
    ).split(",")
    if email.strip()
}

ADMIN_ALLOWED_IPS = {
    ip.strip()
    for ip in os.getenv(
        "CYBERSHIELD_ADMIN_ALLOWED_IPS",
        "127.0.0.1,::1,10.20.1.82",
    ).split(",")
    if ip.strip()
}


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    result = register_user(
        db=db,
        name=data.name,
        email=data.email,
        password=data.password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


@router.post("/login")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    # ---------------------------------------------------------
    # 1. Validar credenciales
    # ---------------------------------------------------------
    result = login_user(
        db=db,
        email=data.email,
        password=data.password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail=result["message"],
        )

    is_admin = (
        data.email.lower()
        in ADMIN_EMAILS
    )

    # ---------------------------------------------------------
    # 2. Admin con credenciales válidas,
    #    pero desde origen NO autorizado
    # ---------------------------------------------------------
    if (
        is_admin
        and client_ip not in ADMIN_ALLOWED_IPS
    ):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=60)

        # Contamos eventos previos del mismo:
        # - tipo
        # - origen
        # - servidor
        # durante los últimos 60 segundos.
        previous_attempts = (
            db.query(Event)
            .filter(
                Event.event_type
                == "unauthorized_admin_login",
                Event.source_ip == client_ip,
                Event.server_id == 2,
                Event.created_at >= cutoff,
                Event.created_at <= now,
            )
            .count()
        )

        # Sumamos el intento actual, que todavía
        # no ha sido insertado en la base.
        attempts = previous_attempts + 1

        security_event = SecurityEventRequest(
            event_type="unauthorized_admin_login",
            source="authentication",
            source_ip=client_ip,
            server_id=2,
            description=(
                "Intento de acceso administrativo "
                "desde un origen no autorizado"
            ),
            scope="BLOCKED",
            details={
                "email": data.email,
                "credentials_valid": True,
                "origin_authorized": False,
                "admin_protected": True,
                "attempts": attempts,
                "time_window_seconds": 60,
            },
        )

        process_security_event(
            db,
            security_event,
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "Acceso administrativo bloqueado: "
                "origen no autorizado"
            ),
        )

    # ---------------------------------------------------------
    # 3. Acceso autorizado
    # ---------------------------------------------------------
    result["client_ip"] = client_ip

    if is_admin:
        result["access_origin"] = "authorized"

    return result