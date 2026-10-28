from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.server import Server
from app.schemas.server import ServerCreate, HeartbeatRequest


router = APIRouter(
    prefix="/servers",
    tags=["Servers"]
)


@router.get("")
def get_servers(
    db: Session = Depends(get_db)
):
    servers = (
        db.query(Server)
        .order_by(Server.id.asc())
        .all()
    )

    return [
        {
            "id": server.id,
            "name": server.name,
            "ip_address": str(server.ip_address),
            "status": server.status,
            "agent": server.agent,
            "created_at": server.created_at,
            "last_seen": server.last_seen
        }
        for server in servers
    ]


@router.post("")
def create_server(
    data: ServerCreate,
    db: Session = Depends(get_db)
):
    existing_server = (
        db.query(Server)
        .filter(Server.ip_address == data.ip_address)
        .first()
    )

    if existing_server:
        raise HTTPException(
            status_code=400,
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


@router.post("/heartbeat")
def heartbeat(
    data: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    server = (
        db.query(Server)
        .filter(Server.ip_address == data.ip_address)
        .first()
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
