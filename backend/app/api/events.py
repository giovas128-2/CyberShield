from typing import Literal
from ipaddress import ip_address, ip_network

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.event import (
    SecurityEventRequest,
    RemoteLabEventRequest,
)
from app.services.event_service import (
    process_security_event,
    get_events,
    get_event_stats,
)


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


TAILSCALE_NETWORK = ip_network(
    "100.64.0.0/10"
)


# Datos que un cliente remoto NO puede autoconfirmar.
# Esas señales solo deben provenir de sensores confiables
# como Wazuh/Suricata o de lógica interna de CyberShield.
REMOTE_ALLOWED_DETAIL_KEYS = {
    "client_name",
    "test_id",
    "script_name",
    "note",
}


def _remote_lab_source_ip(
    request: Request,
) -> tuple[str, int | None]:
    """
    Obtiene la IP REAL observada por el socket HTTP.

    No utiliza:
    - source_ip del JSON
    - X-Forwarded-For
    - headers suministrados por el cliente

    El laboratorio acepta únicamente:
    - loopback
    - redes privadas
    - rango Tailscale 100.64.0.0/10
    """

    if request.client is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No fue posible identificar "
                "el origen de la conexión."
            ),
        )

    raw_host = request.client.host

    try:
        address = ip_address(
            raw_host
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                "La conexión no presenta "
                "una dirección IP válida."
            ),
        )

    allowed = (
        address.is_loopback
        or address.is_private
        or address in TAILSCALE_NETWORK
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=(
                "El endpoint remoto solo está "
                "habilitado para la red de laboratorio."
            ),
        )

    return (
        str(address),
        request.client.port,
    )


@router.post("/simulate")
def simulate_event(
    data: SecurityEventRequest,
    db: Session = Depends(get_db),
):
    return process_security_event(db, data)


@router.post("/remote-lab")
def receive_remote_lab_event(
    request: Request,
    data: RemoteLabEventRequest,
    db: Session = Depends(get_db),
):
    """
    Entrada para pruebas desde otro dispositivo.

    La IP de origen NO se recibe del body.
    Se obtiene de request.client.host.
    """

    source_ip, source_port = (
        _remote_lab_source_ip(
            request
        )
    )

    # Allowlist estricta:
    # un cliente remoto solo puede adjuntar metadata
    # descriptiva. No puede enviar indicadores que
    # modifiquen la clasificación de seguridad.
    details = {
        key: value
        for key, value
        in (data.details or {}).items()
        if key in REMOTE_ALLOWED_DETAIL_KEYS
    }

    details.update(
        {
            "integration": "remote_lab_http",
            "remote_lab": True,
            "source_ip_observation": "http_peer",
            "source_ip_role": "remote_lab_client",
            "observed_source_ip": source_ip,
            "observed_source_port": source_port,
        }
    )

    event = SecurityEventRequest(
        # El cliente NO selecciona el tipo de ataque.
        # Esta ruta solamente prueba comunicación y
        # registra la IP realmente observada.
        event_type="remote_lab_connectivity_test",

        source="remote_lab_http",
        source_ip=source_ip,
        server_id=data.server_id,
        user=data.user,

        description=(
            data.description
            or "Conexión remota observada por CyberShield"
        ),

        scope=None,
        details=details,
    )

    return process_security_event(
        db,
        event,
    )


@router.get("/stats")
def event_stats(
    window: Literal["1s", "60s"] = Query(
        default="60s",
        description="Ventana móvil de estadísticas",
    ),
    server_id: int | None = Query(
        default=None,
    ),
    source_ip: str | None = Query(
        default=None,
    ),
    event_type: str | None = Query(
        default=None,
    ),
    scope: Literal[
        "BLOCKED",
        "REACHED",
        "IMPACT",
    ]
    | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    try:
        return get_event_stats(
            db=db,
            window=window,
            server_id=server_id,
            source_ip=source_ip,
            event_type=event_type,
            scope=scope,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("")
def list_events(
    db: Session = Depends(get_db),
):
    return get_events(db)