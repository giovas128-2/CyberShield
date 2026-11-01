from datetime import datetime, timedelta, timezone
import hashlib

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.incident import Incident
from app.models.response_action import ResponseAction
from app.cybersecurity.rules import analyze_security_event
from app.services.notification_service import (
    create_incident_notification,
    create_incident_telegram_notification,
)
from app.services.response_action_service import (
    create_automatic_response_action,
)
from app.services.incident_mitre_service import (
    create_automatic_incident_mitre,
)

AUTHENTICATION_CORRELATION_TYPES = (
    "authentication_failure",
    "multiple_login_attempts",
    "authentication_burst",
)


def _correlation_family(
    event_type: str,
) -> str:
    """
    Los eventos de autenticación pertenecen a una misma
    familia lógica para efectos de correlación.
    """

    if event_type in AUTHENTICATION_CORRELATION_TYPES:
        return "authentication"

    return event_type


def _correlation_lock_key(
    event_type: str,
    source_ip: str | None,
    server_id: int | None,
) -> int:
    """
    Genera una clave BIGINT determinística para PostgreSQL.

    Eventos de la misma familia + IP + servidor obtienen
    la misma clave y, por tanto, se serializan únicamente
    durante la correlación de incidentes.
    """

    family = _correlation_family(
        event_type
    )

    identity = (
        f"{family}|"
        f"{source_ip or '<none>'}|"
        f"{server_id if server_id is not None else '<none>'}"
    )

    digest = hashlib.blake2b(
        identity.encode("utf-8"),
        digest_size=8,
    ).digest()

    return int.from_bytes(
        digest,
        byteorder="big",
        signed=True,
    )


def _acquire_correlation_lock(
    db: Session,
    event_type: str,
    source_ip: str | None,
    server_id: int | None,
):
    """
    Lock transaccional de PostgreSQL.

    Se libera automáticamente con COMMIT o ROLLBACK.
    No bloquea familias/orígenes distintos.
    """

    lock_key = _correlation_lock_key(
        event_type=event_type,
        source_ip=source_ip,
        server_id=server_id,
    )

    db.execute(
        text(
            "SELECT pg_advisory_xact_lock(:lock_key)"
        ),
        {
            "lock_key": lock_key,
        },
    )


def process_security_event(db: Session, data):
    analysis = analyze_security_event(data)

    details = dict(data.details or {})

    if getattr(data, "user", None):
        details["user"] = data.user

    scope = (
        getattr(data, "scope", None)
        or analysis.get("scope")
    )

    event = Event(
        event_type=data.event_type,
        source=data.source,
        severity=analysis["risk_level"],
        source_ip=data.source_ip,
        description=data.description,
        details=details,
        server_id=getattr(data, "server_id", None),
        scope=scope,
    )

    incident = None
    notification = None
    response_action = None
    mitre = None

    correlated_incident = None

    # ==========================================================
    # TRANSACCIÓN PRINCIPAL
    # ==========================================================
    #
    # Evento + incidente + MITRE + notificación dashboard +
    # response_action se confirman juntos.
    #
    # Si cualquiera falla antes del commit, se revierte todo.
    #
    # Telegram se ejecuta DESPUÉS porque un servicio externo
    # no debe invalidar un incidente correctamente almacenado.
    # ==========================================================

    db.add(event)

    try:
        # Necesitamos el ID del evento para crear/correlacionar
        # el incidente, pero todavía NO confirmamos nada.
        db.flush()

        # ======================================================
        # CORRELACIÓN GENERAL DE INCIDENTES
        # ======================================================

        if analysis["create_incident"]:

            if (
                event.event_type
                in AUTHENTICATION_CORRELATION_TYPES
            ):
                correlation_types = (
                    AUTHENTICATION_CORRELATION_TYPES
                )
            else:
                correlation_types = (
                    event.event_type,
                )

            # --------------------------------------------------
            # Evitar carrera:
            # dos eventos simultáneos de la misma familia,
            # origen y servidor no pueden hacer la búsqueda
            # de correlación al mismo tiempo.
            #
            # El segundo espera hasta el COMMIT/ROLLBACK del
            # primero y después vuelve a consultar la BD.
            # --------------------------------------------------

            _acquire_correlation_lock(
                db=db,
                event_type=event.event_type,
                source_ip=(
                    str(event.source_ip)
                    if event.source_ip
                    else None
                ),
                server_id=event.server_id,
            )

            correlation_window_seconds = 300

            cutoff = (
                datetime.now(timezone.utc)
                - timedelta(
                    seconds=correlation_window_seconds
                )
            )

            # --------------------------------------------------
            # 1. Buscar incidente activo.
            # --------------------------------------------------

            correlated_incident = (
                db.query(Incident)
                .join(
                    Event,
                    Incident.event_id == Event.id,
                )
                .filter(
                    Event.event_type.in_(
                        correlation_types
                    ),
                    Event.source_ip
                    == event.source_ip,
                    Event.server_id
                    == event.server_id,
                    Event.id != event.id,
                    Incident.status.in_(
                        (
                            "open",
                            "investigating",
                            "escalated",
                        )
                    ),
                )
                .order_by(
                    Incident.id.desc()
                )
                .first()
            )

            # --------------------------------------------------
            # 2. Absorber eventos tardíos de un incidente
            #    recién resuelto.
            # --------------------------------------------------

            if correlated_incident is None:
                correlated_incident = (
                    db.query(Incident)
                    .join(
                        Event,
                        Incident.event_id == Event.id,
                    )
                    .join(
                        ResponseAction,
                        ResponseAction.incident_id
                        == Incident.id,
                    )
                    .filter(
                        Event.event_type.in_(
                            correlation_types
                        ),
                        Event.source_ip
                        == event.source_ip,
                        Event.server_id
                        == event.server_id,
                        Event.id != event.id,
                        Incident.status
                        == "resolved",
                        ResponseAction.status.in_(
                            (
                                "executed",
                                "rolled_back",
                            )
                        ),
                        func.coalesce(
                            ResponseAction.rolled_back_at,
                            ResponseAction.executed_at,
                            ResponseAction.created_at,
                        ) >= cutoff,
                    )
                    .order_by(
                        Incident.id.desc()
                    )
                    .first()
                )

            # ==================================================
            # INCIDENTE EXISTENTE
            # ==================================================

            if correlated_incident is not None:
                incident = correlated_incident

                analysis[
                    "incident_reused"
                ] = True

                analysis[
                    "correlated_to_incident_id"
                ] = incident.id

                event_details = dict(
                    event.details or {}
                )

                event_details[
                    "correlated_incident_id"
                ] = incident.id

                event_details[
                    "correlation_role"
                ] = "related"

                event.details = event_details

                severity_rank = {
                    "normal": 0,
                    "warning": 1,
                    "high": 2,
                    "critical": 3,
                }

                old_rank = severity_rank.get(
                    str(
                        incident.severity
                    ).lower(),
                    0,
                )

                new_rank = severity_rank.get(
                    str(
                        analysis["risk_level"]
                    ).lower(),
                    0,
                )

                if new_rank > old_rank:
                    incident.severity = (
                        analysis["risk_level"]
                    )

            # ==================================================
            # INCIDENTE NUEVO
            # ==================================================

            else:
                incident = Incident(
                    event_id=event.id,
                    severity=analysis[
                        "risk_level"
                    ],
                    status="open",
                )

                db.add(incident)

                # Necesitamos incident.id para las relaciones,
                # pero seguimos dentro de la misma transacción.
                db.flush()

                analysis[
                    "incident_reused"
                ] = False

                analysis[
                    "correlated_to_incident_id"
                ] = incident.id

                event_details = dict(
                    event.details or {}
                )

                event_details[
                    "correlated_incident_id"
                ] = incident.id

                event_details[
                    "correlation_role"
                ] = "primary"

                event.details = event_details

                # ----------------------------------------------
                # MITRE dentro de la transacción.
                # ----------------------------------------------

                mitre = (
                    create_automatic_incident_mitre(
                        db=db,
                        incident_id=incident.id,
                        event_type=event.event_type,
                        details=event.details,
                        commit=False,
                    )
                )

                # ----------------------------------------------
                # Dashboard dentro de la transacción.
                # Telegram se aplaza hasta después del commit.
                # ----------------------------------------------

                notification = (
                    create_incident_notification(
                        db=db,
                        incident_id=incident.id,
                        severity=incident.severity,
                        event_type=event.event_type,
                        server_id=event.server_id,
                        commit=False,
                        send_telegram=False,
                    )
                )

                # ----------------------------------------------
                # Acción defensiva dentro de la transacción.
                # ----------------------------------------------

                response_action = (
                    create_automatic_response_action(
                        db=db,
                        incident_id=incident.id,
                        event_type=event.event_type,
                        severity=incident.severity,
                        scope=event.scope,
                        source_ip=(
                            str(
                                event.source_ip
                            )
                            if event.source_ip
                            else None
                        ),
                        details=event.details,
                        commit=False,
                    )
                )

        # ======================================================
        # ÚNICO COMMIT DE LA PARTE CRÍTICA
        # ======================================================

        db.commit()

    except Exception:
        # Ninguna pieza parcial del evento/incidente debe quedar
        # persistida si la transacción principal falla.
        db.rollback()
        raise

    # ==========================================================
    # REFRESCAR OBJETOS YA CONFIRMADOS
    # ==========================================================

    db.refresh(event)

    if incident is not None:
        db.refresh(incident)

    if notification is not None:
        db.refresh(notification)

    if response_action is not None:
        db.refresh(response_action)

    if mitre is not None:
        db.refresh(mitre)

    # ==========================================================
    # TELEGRAM FUERA DE LA TRANSACCIÓN PRINCIPAL
    # ==========================================================
    #
    # Solo existe notification para HIGH/CRITICAL nuevos.
    # Un fallo aquí NO debe deshacer lo anterior.
    # ==========================================================

    if notification is not None:
        try:
            create_incident_telegram_notification(
                db=db,
                incident_id=incident.id,
                severity=incident.severity,
                event_type=event.event_type,
                server_id=event.server_id,
            )
        except Exception:
            # Una posible falla de persistencia de la
            # notificación externa tampoco debe dejar
            # la sesión SQLAlchemy en estado fallido.
            db.rollback()

    return {
        "success": True,

        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "source_ip": (
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            "server_id": event.server_id,
            "scope": event.scope,
            "description": event.description,
            "details": event.details,
            "created_at": event.created_at,
        },

        "analysis": analysis,

        "incident": {
            "id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,
        }
        if incident
        else None,

        "notification": {
            "id": notification.id,
            "incident_id": notification.incident_id,
            "recipient": notification.recipient,
            "channel": notification.channel,
            "status": notification.status,
            "message": notification.message,
            "created_at": notification.created_at,
            "sent_at": notification.sent_at,
        }
        if notification
        else None,

        "response_action": {
            "id": response_action.id,
            "incident_id": response_action.incident_id,
            "action_type": response_action.action_type,
            "target": response_action.target,
            "status": response_action.status,
            "reversible": response_action.reversible,
            "duration_seconds": response_action.duration_seconds,
            "reason": response_action.reason,
            "result": response_action.result,
            "created_at": response_action.created_at,
            "executed_at": response_action.executed_at,
            "rolled_back_at": response_action.rolled_back_at,
        }
        if response_action
        else None,

        "mitre": {
            "id": mitre.id,
            "incident_id": mitre.incident_id,
            "technique_id": mitre.technique_id,
            "technique_name": mitre.technique_name,
            "tactic": mitre.tactic,
            "reference_url": mitre.reference_url,
            "is_primary": mitre.is_primary,
            "notes": mitre.notes,
        }
        if mitre
        else None,
    }


def get_events(
    db: Session,
    limit: int = 100,
):
    events = (
        db.query(Event)
        .order_by(Event.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "source_ip": (
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            "server_id": event.server_id,
            "scope": event.scope,
            "description": event.description,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]


def get_event_stats(
    db: Session,
    window: str,
    server_id: int | None = None,
    source_ip: str | None = None,
    event_type: str | None = None,
    scope: str | None = None,
):
    if window == "1s":
        seconds = 1

    elif window == "60s":
        seconds = 60

    else:
        raise ValueError(
            "La ventana debe ser '1s' o '60s'"
        )

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=seconds)

    # ---------------------------------------------------------
    # Helper interno para aplicar los mismos filtros
    # ---------------------------------------------------------

    def apply_filters(query):
        query = query.filter(
            Event.created_at >= cutoff,
            Event.created_at <= now,
        )

        if server_id is not None:
            query = query.filter(
                Event.server_id == server_id
            )

        if source_ip is not None:
            query = query.filter(
                Event.source_ip == source_ip
            )

        if event_type is not None:
            query = query.filter(
                Event.event_type == event_type
            )

        if scope is not None:
            query = query.filter(
                Event.scope == scope
            )

        return query

    # ---------------------------------------------------------
    # Total
    # ---------------------------------------------------------

    total_events = apply_filters(
        db.query(Event)
    ).count()

    # ---------------------------------------------------------
    # Por origen
    # ---------------------------------------------------------

    source_rows = (
        apply_filters(
            db.query(
                Event.source_ip,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.source_ip)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    by_source = [
        {
            "source_ip": (
                str(row.source_ip)
                if row.source_ip
                else None
            ),
            "count": row.count,
        }
        for row in source_rows
    ]

    # ---------------------------------------------------------
    # Por tipo
    # ---------------------------------------------------------

    type_rows = (
        apply_filters(
            db.query(
                Event.event_type,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    by_type = [
        {
            "event_type": row.event_type,
            "count": row.count,
        }
        for row in type_rows
    ]

    # ---------------------------------------------------------
    # Por scope
    # ---------------------------------------------------------

    scope_rows = (
        apply_filters(
            db.query(
                Event.scope,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.scope)
        .all()
    )

    by_scope = {
        "BLOCKED": 0,
        "REACHED": 0,
        "IMPACT": 0,
    }

    unclassified = 0

    for row in scope_rows:
        if row.scope in by_scope:
            by_scope[row.scope] = row.count
        else:
            unclassified += row.count

    # ---------------------------------------------------------
    # Por servidor
    # ---------------------------------------------------------

    server_rows = (
        apply_filters(
            db.query(
                Event.server_id,
                func.count(Event.id).label("count"),
            )
        )
        .group_by(Event.server_id)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    by_server = [
        {
            "server_id": row.server_id,
            "count": row.count,
        }
        for row in server_rows
    ]

    return {
        "window": window,
        "window_seconds": seconds,
        "generated_at": now,

        "filters": {
            "server_id": server_id,
            "source_ip": source_ip,
            "event_type": event_type,
            "scope": scope,
        },

        "total_events": total_events,
        "by_source": by_source,
        "by_type": by_type,
        "by_scope": by_scope,
        "unclassified_scope": unclassified,
        "by_server": by_server,
    }
