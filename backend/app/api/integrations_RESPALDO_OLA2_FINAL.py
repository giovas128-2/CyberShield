from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.schemas.event import (
    SecurityEventRequest,
)

from app.services.event_service import (
    process_security_event,
)

from app.cybersecurity.wazuh_adapter import (
    normalize_wazuh_event,
)

from app.cybersecurity.suricata_adapter import (
    normalize_suricata_event,
)

from app.models.server import Server
from typing import Literal

from pydantic import BaseModel
from app.services.response_action_service import (
    get_latest_response_action_for_target,
    register_execution_result,
    register_rollback_result,
)

router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
)

class ActiveResponseReport(BaseModel):
    operation: Literal[
        "add",
        "delete",
    ]

    action_type: str
    target: str
    success: bool
    result: str

def validate_server(
    db: Session,
    server_id: int,
):
    server = (
        db.query(Server)
        .filter(Server.id == server_id)
        .first()
    )

    if not server:
        raise HTTPException(
            status_code=404,
            detail=f"No existe server_id={server_id}",
        )

    return server


@router.post("/wazuh")
def receive_wazuh_event(
    raw_event: dict,

    server_id: int = Query(
        default=2,
        description=(
            "Servidor CyberShield que generó "
            "la alerta. En el laboratorio actual "
            "srv-yahir-01 corresponde al ID 1."
        ),
    ),

    db: Session = Depends(get_db),
):
    validate_server(
        db,
        server_id,
    )

    normalized = normalize_wazuh_event(
        raw_event=raw_event,
        server_id=server_id,
    )

    event = SecurityEventRequest(
        **normalized
    )

    return process_security_event(
        db,
        event,
    )


@router.post("/suricata")
def receive_suricata_event(
    raw_event: dict,

    server_id: int = Query(
        default=2,
        description=(
            "Servidor asociado al sensor "
            "Suricata del laboratorio."
        ),
    ),

    db: Session = Depends(get_db),
):
    validate_server(
        db,
        server_id,
    )

    normalized = normalize_suricata_event(
        raw_event=raw_event,
        server_id=server_id,
    )

    event = SecurityEventRequest(
        **normalized
    )

    return process_security_event(
        db,
        event,
    )
@router.post("/wazuh/active-response")
def receive_wazuh_active_response(
    data: ActiveResponseReport,
    db: Session = Depends(get_db),
):
    """
    Recibe el resultado real de Wazuh Active Response.

    ADD:
        Corresponde a la ejecución de una acción defensiva.

    DELETE:
        Corresponde al rollback de una acción temporal.

    CyberShield NO ejecuta comandos privilegiados aquí.
    Wazuh realiza la acción y este endpoint solamente
    registra su resultado.
    """

    # =========================================================
    # EJECUCIÓN DE RESPUESTA
    # =========================================================

    if data.operation == "add":

        action = (
            get_latest_response_action_for_target(
                db=db,
                action_type=data.action_type,
                target=data.target,
                statuses=[
                    "pending",
                    "approved",
                ],
            )
        )

        if not action:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No existe una acción pendiente "
                    f"{data.action_type} para "
                    f"{data.target}"
                ),
            )

        updated = register_execution_result(
            db=db,
            action_id=action.id,
            success=data.success,
            result=data.result,
        )

        return {
            "success": True,
            "operation": "add",
            "response_action": updated,
        }

    # =========================================================
    # ROLLBACK
    # =========================================================

    action = (
        get_latest_response_action_for_target(
            db=db,
            action_type=data.action_type,
            target=data.target,
            statuses=[
                "executed",
            ],
        )
    )

    if not action:
        raise HTTPException(
            status_code=404,
            detail=(
                "No existe una acción ejecutada "
                f"{data.action_type} para "
                f"{data.target}"
            ),
        )

    if not action.reversible:
        raise HTTPException(
            status_code=400,
            detail=(
                "La acción encontrada "
                "no es reversible"
            ),
        )

    updated = register_rollback_result(
        db=db,
        action_id=action.id,
        success=data.success,
        result=data.result,
    )

    return {
        "success": True,
        "operation": "delete",
        "response_action": updated,
    }