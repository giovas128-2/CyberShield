from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database.connection import get_db
from app.models.server import Server
from app.schemas.server import ServerCreate, HeartbeatRequest
from app.core.service_auth import require_service_key
from app.core.auth_dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/servers",
    tags=["Servers"]
)


@router.get("")
def get_servers(
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_user),
):
    servers = (
        db.query(Server)
        .order_by(Server.id.asc())
        .all()
    )

    now = datetime.now(timezone.utc)

    heartbeat_timeout_seconds = 90

    result = []

    for server in servers:
        effective_status = server.status

        if server.last_seen is not None:
            last_seen = server.last_seen

            # PostgreSQL TIMESTAMPTZ normalmente devuelve
            # datetime con zona horaria. Este fallback evita
            # errores si alguna instalación entrega uno naive.
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(
                    tzinfo=timezone.utc
                )

            age_seconds = (
                now - last_seen
            ).total_seconds()

            if age_seconds > heartbeat_timeout_seconds:
                effective_status = "offline"

        result.append({
            "id": server.id,
            "name": server.name,
            "ip_address": str(server.ip_address),
            "status": effective_status,
            "agent": server.agent,
            "created_at": server.created_at,
            "last_seen": server.last_seen
        })

    return result


@router.post("")
def create_server(
    data: ServerCreate,
    db: Session = Depends(get_db),
    _current_user = Depends(
        require_roles("admin", "engineer")
    ),
):
    existing_server = (
        db.query(Server)
        .filter(Server.ip_address == data.ip_address)
        .first()
    )

    if existing_server:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un servidor registrado con esa IP"
        )

    server = Server(
        name=data.name,
        ip_address=data.ip_address,
        status=data.status,
        agent=data.agent
    )

    db.add(server)

    try:
        db.commit()
        db.refresh(server)

    except IntegrityError as exc:
        db.rollback()

        diag = getattr(exc.orig, "diag", None)
        constraint = getattr(
            diag, "constraint_name", None
        )

        sqlstate = (
            getattr(exc.orig, "sqlstate", None)
            or getattr(exc.orig, "pgcode", None)
        )

        if (
            sqlstate == "23505"
            and constraint == "cs_servers_ip_unique"
        ):
            raise HTTPException(
                status_code=409,
                detail="Ya existe un servidor con esa IP",
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Servidor registrado correctamente",
        "server": {
            "id": server.id,
            "name": server.name,
            "ip_address": str(server.ip_address),
            "status": server.status,
            "agent": server.agent,
            "created_at": server.created_at,
            "last_seen": server.last_seen
        }
    }


@router.post(
    "/heartbeat",
    dependencies=[Depends(require_service_key)],
)
def heartbeat(
    data: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    server = (
        db.query(Server)
        .filter(Server.ip_address == data.ip_address)
        .with_for_update()
        .first()
    )

    # La tabla de credenciales se instala mediante
    # una migracion SQL independiente.
    credentials_table = db.execute(
        text("""
            SELECT to_regclass(
                'public.server_agent_credentials'
            )
        """)
    ).scalar_one()

    if server is not None and credentials_table is not None:
        # La regla incluye credenciales revocadas:
        # no se permite volver al mecanismo compartido.
        individual_history = db.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM public.server_agent_credentials
                    WHERE server_id = :server_id
                )
            """),
            {"server_id": server.id},
        ).scalar_one()

        if individual_history:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Este servidor utiliza autenticacion "
                    "individual. El heartbeat compartido "
                    "ya no esta permitido"
                ),
            )

    now = datetime.now(timezone.utc)

    if server is None:
        server = Server(
            name=data.name,
            ip_address=data.ip_address,
            status="online",
            agent=data.agent,
            last_seen=now
        )

        db.add(server)

    else:
        server.name = data.name
        server.status = "online"
        server.agent = data.agent
        server.last_seen = now

    try:
        db.commit()
        db.refresh(server)

    except IntegrityError as exc:
        db.rollback()

        diag = getattr(exc.orig, "diag", None)
        constraint = getattr(
            diag, "constraint_name", None
        )

        sqlstate = (
            getattr(exc.orig, "sqlstate", None)
            or getattr(exc.orig, "pgcode", None)
        )

        if (
            sqlstate == "23505"
            and constraint == "cs_servers_ip_unique"
        ):
            raise HTTPException(
                status_code=409,
                detail="Ya existe un servidor con esa IP",
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Heartbeat recibido",
        "server": {
            "id": server.id,
            "name": server.name,
            "ip_address": str(server.ip_address),
            "status": server.status,
            "agent": server.agent,
            "last_seen": server.last_seen
        }
    }
