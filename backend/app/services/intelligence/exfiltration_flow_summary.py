"""Consolidación c6 *solo shadow*: señales Suricata de un mismo flujo/ventana.

No reemplaza ni filtra eventos originales, incidentes, acciones o notificaciones.
No consulta PostgreSQL ni envía peticiones; cada alerta original sigue disponible
en el sensor. Agrega estadísticas de evidencia, NO confirma exfiltración.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

WINDOW_SECONDS = 300
SIGNATURE = "1000002"
MIN_BYTES = 10_000_000


@dataclass(frozen=True)
class ExfilFlowSummary:
    flow_id: str
    window_start: str
    alerts: int
    distinct_timestamps: int
    raw_alert_records: int
    max_bytes_toserver: int
    bulk_transfer_observed: bool
    status: str = "simulation_only"
    execution_allowed: bool = False
    executed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    # Suricata EVE typically emits +HHMM; datetime.fromisoformat supports it.
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        return None
    return ts.astimezone(timezone.utc)


def consolidate_exfiltration_flows(
    events: Iterable[Mapping[str, Any]],
    window_seconds: int = WINDOW_SECONDS,
) -> list[ExfilFlowSummary]:
    """Clasifica alertas EVE SC6 en intervalos sin ejecutar respuestas.

    Agrupa únicamente por flow_id, servidor/sensor implícito en el lote,
    y ventana UTC. Los lotes de diferentes sensores deben mantenerse separados.
    Repeticiones exactas de la misma marca temporal cuentan como una
    observación; nunca se usa flow_id para descartar alertas distintas.
    """
    if type(window_seconds) is not int or window_seconds <= 0:
        raise ValueError("window_seconds debe ser entero positivo")

    groups: dict[tuple[str, int], dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, Mapping):
            continue
        flow_id = event.get("flow_id")
        ts = _timestamp(event.get("timestamp"))
        if flow_id is None or isinstance(flow_id, bool) or ts is None:
            continue
        sensor_type = event.get("event_type")
        alert = event.get("alert") or {}
        flow = event.get("flow") or {}
        if sensor_type == "alert":
            if str(alert.get("signature_id")) != SIGNATURE:
                continue
        elif sensor_type == "flow":
            if (
                event.get("dest_ip") != "172.25.176.1"
                or str(event.get("dest_port")) != "8765"
            ):
                continue
        else:
            continue
        try:
            bytes_up = int(flow.get("bytes_toserver") or 0)
        except (TypeError, ValueError):
            continue
        if bytes_up < 0:
            continue
        # Evita contar como observación SC6 los flujos de poca transferencia.
        if sensor_type == "flow" and bytes_up < MIN_BYTES:
            continue

        bucket = int(ts.timestamp()) // window_seconds * window_seconds
        key = (str(flow_id), bucket)
        group = groups.setdefault(
            key, {"timestamps": set(), "raw_alert_records": 0, "max_bytes": 0, "bulk": False}
        )
        group["timestamps"].add(ts.isoformat())
        if sensor_type == "alert":
            group["raw_alert_records"] += 1
        group["max_bytes"] = max(group["max_bytes"], bytes_up)
        group["bulk"] = group["bulk"] or (
            sensor_type == "flow" and bytes_up >= MIN_BYTES
        )

    result = []
    for (flow_id, bucket), group in sorted(groups.items()):
        result.append(ExfilFlowSummary(
            flow_id=flow_id,
            window_start=datetime.fromtimestamp(
                bucket, tz=timezone.utc
            ).isoformat(),
            alerts=len(group["timestamps"]),
            distinct_timestamps=len(group["timestamps"]),
            raw_alert_records=group["raw_alert_records"],
            max_bytes_toserver=group["max_bytes"],
            bulk_transfer_observed=group["bulk"],
        ))
    return result
