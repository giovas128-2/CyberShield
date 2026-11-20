import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.core.service_auth import require_service_key

from app.schemas.event import (
    SecurityEventRequest,
)

from app.services.event_service import (
    process_security_event,
)
from app.services.intelligence.defensive_decision_engine import (
    assess_from_database,
)
from app.services.intelligence.shadow_decision_store import (
    save_shadow_decision,
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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
    dependencies=[Depends(require_service_key)],
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

    result = process_security_event(
        db,
        event,
    )

    # Motor CyberShield 2.0: observación posterior al almacenamiento.
    # La evaluación NO crea acciones, NO ejecuta comandos y NO afecta la
    # lógica de respuestas preexistente. Sólo esta ruta de integración
    # autenticada utiliza el evaluador shadow; /events/simulate no.
    #
    # OJO: autenticar el integrador con una clave de servicio no prueba por
    # sí mismo la autenticidad del sensor ni que su cuerpo JSON sea genuino.
    # Antes de habilitar ejecución autónoma se requerirá validar esa cadena.
    if normalized.get("event_type") in (
        "multiple_login_attempts",
        "authentication_burst",
        "authentication_failure",
    ):
        try:
            stored = result["event"]
            decision = assess_from_database(db, {
                "event_type": stored["event_type"],
                "severity": stored["severity"],
                "source": stored["source"],
                "source_ip": stored["source_ip"],
                "details": stored["details"],
            })
            # El evento ya fue confirmado por process_security_event.
            # Guardamos una evaluación trazable, sin cambiar response_actions.
            decision_id = save_shadow_decision(
                db, int(stored["id"]), decision,
            )
            result["autonomous_decision"] = decision.to_dict()
            result["autonomous_decision"]["mode"] = "shadow"
            result["autonomous_decision"]["decision_id"] = decision_id
        except Exception:
            logger.exception("Evaluación shadow T1110 falló; no se ejecuta defensa")
            db.rollback()
            result["autonomous_decision"] = {
                "mode": "shadow",
                "status": "evaluation_unavailable",
                "execution_allowed": False,
                "executed": False,
            }

    return result


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

        from app.services.wazuh_response_verification import (
            evaluate_wazuh_execution,
        )

        verification = evaluate_wazuh_execution(
            operation="add",
            success=data.success,
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
            "containment_verification": {
                "status": verification.status,
                "notify_engineer": verification.notify_engineer,
                "reason": verification.reason,
            },
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