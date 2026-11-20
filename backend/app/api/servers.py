from datetime import datetime, timezone
from ipaddress import ip_address
import hashlib
import secrets
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from fastapi import APIRouter, Depends, HTTPException, Response
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



# Alta atómica de servidor y token individual. No se conecta a la IP introducida.
class ServerOnboardRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    ip_address: str = Field(min_length=3, max_length=45)
    platform: Literal["linux", "windows", "macos", "other"]
    agent_version: str = Field(default="1.0", min_length=1, max_length=32)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(char) < 32 for char in value):
            raise ValueError("Nombre de servidor inválido")
        return value

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        try:
            parsed = ip_address(value.strip())
        except ValueError as exc:
            raise ValueError("Escribe una dirección IPv4 o IPv6 válida") from exc
        if parsed.is_unspecified or parsed.is_multicast:
            raise ValueError("No se admiten IP de multidifusión ni no especificadas")
        return str(parsed)


@router.post("/onboard", status_code=201)
def onboard_server(
    data: ServerOnboardRequest,
    response: Response,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "engineer")),
):
    """Registra servidor y credencial individual. Conectado solo tras heartbeat."""
    credentials_table = db.execute(
        text("SELECT to_regclass('public.server_agent_credentials')")
    ).scalar_one()
    if credentials_table is None:
        raise HTTPException(
            status_code=503,
            detail="Falta migración 003_server_agent_credentials.sql para integrar agentes",
        )
    already = db.query(Server.id).filter(Server.ip_address == data.ip_address).first()
    if already:
        raise HTTPException(status_code=409, detail="Ya existe un servidor registrado con esa IP")

    server = Server(
        name=data.name, ip_address=data.ip_address, status="registered",
        agent=f"CyberShield Agent ({data.platform})", last_seen=None,
    )
    agent_id = uuid4()
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    try:
        db.add(server)
        db.flush()
        db.execute(text("""
            INSERT INTO public.server_agent_credentials
                (agent_id, server_id, token_hash, platform, agent_version)
            VALUES
                (CAST(:agent_id AS UUID), :server_id, :token_hash, :platform, :version)
        """), {
            "agent_id": str(agent_id), "server_id": server.id,
            "token_hash": digest, "platform": data.platform,
            "version": data.agent_version,
        })
        db.commit()
        db.refresh(server)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="No se pudo registrar servidor/agente: verifica IP duplicada",
        ) from exc
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return {
        "success": True,
        "server": {
            "id": server.id, "name": server.name,
            "ip_address": str(server.ip_address),
            "status": "registered", "last_seen": None,
        },
        "agent": {
            "agent_id": str(agent_id), "platform": data.platform,
            "token": token, "token_shown_once": True,
        },
        "message": "Servidor registrado; pendiente del primer heartbeat autenticado.",
    }


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
    agents_by_server = {}
    table_exists = db.execute(
        text("SELECT to_regclass('public.server_agent_credentials')")
    ).scalar_one()
    if table_exists:
        records = db.execute(text("""
            SELECT DISTINCT ON (server_id)
                server_id, agent_id, platform, agent_version, last_seen, revoked_at
            FROM public.server_agent_credentials
            ORDER BY server_id, (revoked_at IS NULL) DESC, created_at DESC
        """)).mappings().all()
        agents_by_server = {row["server_id"]:row for row in records}

    result = []
    for server in servers:
        agent = agents_by_server.get(server.id)
        agent_state = "not_enrolled"
        agent_last_seen = None
        agent_id = None
        platform = None
        version = None
        if agent is not None:
            agent_id = str(agent["agent_id"])
            agent_last_seen = agent["last_seen"]
            platform = agent["platform"]
            version = agent["agent_version"]
            if agent["revoked_at"] is not None:
                agent_state = "revoked"
            elif agent_last_seen is None:
                agent_state = "awaiting_heartbeat"
            else:
                last = agent_last_seen
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                agent_state = (
                    "connected"
                    if (now-last).total_seconds() <= heartbeat_timeout_seconds
                    else "disconnected"
                )

        effective_status = server.status
        if agent is not None:
            effective_status = (
                "online" if agent_state == "connected" else
                "registered" if agent_state == "awaiting_heartbeat" else "offline"
            )
        elif server.last_seen is not None:
            last_seen = server.last_seen
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if (now-last_seen).total_seconds() > heartbeat_timeout_seconds:
                effective_status = "offline"

        result.append({
            "id": server.id, "name": server.name,
            "ip_address": str(server.ip_address),
            "status": effective_status, "agent": server.agent,
            "created_at": server.created_at, "last_seen": server.last_seen,
            "agent_connection": {
                "state": agent_state, "agent_id": agent_id,
                "platform": platform, "agent_version": version,
                "last_seen": agent_last_seen,
            },
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
