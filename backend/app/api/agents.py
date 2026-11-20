import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_roles
from app.database.connection import get_db


router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agent Enrollment"],
)

agent_bearer = HTTPBearer(auto_error=False)


class AgentRegistration(BaseModel):
    server_id: int = Field(gt=0)
    platform: str = Field(min_length=1, max_length=64)
    agent_version: str = Field(min_length=1, max_length=32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/register", status_code=201)
def register_agent(
    data: AgentRegistration,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "engineer")),
):
    server = db.execute(
        text("""
            SELECT id
            FROM public.servers
            WHERE id = :server_id
            FOR UPDATE
        """),
        {"server_id": data.server_id},
    ).scalar_one_or_none()

    if server is None:
        raise HTTPException(
            status_code=404,
            detail="Servidor no encontrado",
        )

    existing = db.execute(
        text("""
            SELECT agent_id
            FROM public.server_agent_credentials
            WHERE server_id = :server_id
              AND revoked_at IS NULL
        """),
        {"server_id": data.server_id},
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="El servidor ya tiene un agente activo",
        )

    agent_id = uuid4()
    token = secrets.token_urlsafe(32)

    try:
        db.execute(
            text("""
                INSERT INTO public.server_agent_credentials (
                    agent_id,
                    server_id,
                    token_hash,
                    platform,
                    agent_version
                )
                VALUES (
                    CAST(:agent_id AS uuid),
                    :server_id,
                    :token_hash,
                    :platform,
                    :agent_version
                )
            """),
            {
                "agent_id": str(agent_id),
                "server_id": data.server_id,
                "token_hash": token_digest(token),
                "platform": data.platform,
                "agent_version": data.agent_version,
            },
        )
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar el agente",
        )

    except Exception:
        db.rollback()
        raise

    return {
        "agent_id": str(agent_id),
        "server_id": data.server_id,
        "token": token,
        "message": "Guarda el token: no se mostrará nuevamente",
    }


@router.post("/{agent_id}/heartbeat")
def agent_heartbeat(
    agent_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        agent_bearer
    ),
    db: Session = Depends(get_db),
):
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise HTTPException(
            status_code=401,
            detail="Credencial de agente requerida",
        )

    supplied_hash = token_digest(credentials.credentials)

    row = db.execute(
        text("""
            SELECT server_id, token_hash, revoked_at
            FROM public.server_agent_credentials
            WHERE agent_id = CAST(:agent_id AS uuid)
            FOR UPDATE
        """),
        {"agent_id": str(agent_id)},
    ).mappings().first()

    if (
        row is None
        or row["revoked_at"] is not None
        or not hmac.compare_digest(
            row["token_hash"].strip(),
            supplied_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Credencial de agente inválida",
        )

    now = datetime.now(timezone.utc)

    try:
        db.execute(
            text("""
                UPDATE public.server_agent_credentials
                SET last_seen = :now
                WHERE agent_id = CAST(:agent_id AS uuid)
            """),
            {"now": now, "agent_id": str(agent_id)},
        )

        db.execute(
            text("""
                UPDATE public.servers
                SET last_seen = :now,
                    status = 'online'
                WHERE id = :server_id
            """),
            {"now": now, "server_id": row["server_id"]},
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "agent_id": str(agent_id),
        "server_id": row["server_id"],
        "heartbeat": "accepted",
        "last_seen": now.isoformat(),
    }


@router.post("/{agent_id}/revoke")
def revoke_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "engineer")),
):
    row = db.execute(
        text("""
            SELECT agent_id, revoked_at
            FROM public.server_agent_credentials
            WHERE agent_id = CAST(:agent_id AS uuid)
            FOR UPDATE
        """),
        {"agent_id": str(agent_id)},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Agente no encontrado",
        )

    if row["revoked_at"] is not None:
        raise HTTPException(
            status_code=409,
            detail="La credencial ya fue revocada",
        )

    try:
        db.execute(
            text("""
                UPDATE public.server_agent_credentials
                SET revoked_at = GREATEST(
                    CURRENT_TIMESTAMP,
                    created_at
                )
                WHERE agent_id = CAST(:agent_id AS uuid)
            """),
            {"agent_id": str(agent_id)},
        )
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "agent_id": str(agent_id),
        "revoked": True,
    }
