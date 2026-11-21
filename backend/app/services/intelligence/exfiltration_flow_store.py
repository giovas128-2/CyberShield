"""Persistencia c6 de instantáneas COMPLETAS (solo inteligencia shadow).

NO se invoca desde /integrations/suricata ni cambia el flujo de incidentes.
La ventana debe contener toda la evidencia del lote/archivo analizado:
una actualización parcial NO puede sobrescribir contadores correctos.
"""
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.exfiltration_flow_summary import ExfilFlowSummary


def store_complete_exfil_snapshots(
    db: Session,
    summaries: Sequence[ExfilFlowSummary],
    *,
    sensor_id: str,
    snapshot_complete: bool = False,
) -> int:
    """UPSERT idempotente de resúmenes completos; transacción del llamador.

    No hace commit ni ejecuta respuestas. No usar para ventanas abiertas.
    La identidad del sensor se suministra desde configuración confiable,
    NO del JSON recibido de la red.
    """
    if snapshot_complete is not True:
        raise ValueError("Se requiere snapshot_complete=True")
    if not isinstance(sensor_id, str) or not sensor_id.strip():
        raise ValueError("sensor_id obligatorio")
    if len(sensor_id) > 128:
        raise ValueError("sensor_id demasiado largo")

    # Validar todo ANTES de insertar para no dejar escrituras parciales.
    keys = set()
    for item in summaries:
        if not isinstance(item, ExfilFlowSummary):
            raise TypeError("Resumen de flujo inválido")
        if item.execution_allowed or item.executed or item.status != "simulation_only":
            raise ValueError("Se rechaza un resumen ejecutable")
        if item.raw_alert_records < 0 or item.alerts < 0:
            raise ValueError("Conteos inválidos")
        key = (item.flow_id, item.window_start)
        if key in keys:
            raise ValueError("Lote con ventanas duplicadas")
        keys.add(key)

    query = text("""
        INSERT INTO cybershield_exfil_flow_summaries (
            sensor_id, flow_id, window_start, window_seconds, signature_id,
            observed_alerts, distinct_observations, max_bytes_toserver,
            bulk_transfer_observed, technique_id, control_id,
            decision_status, mode, execution_allowed, executed
        ) VALUES (
            :sensor_id, :flow_id, CAST(:window_start AS timestamptz),
            300, '1000002', :raw_alert_records, :distinct_observations,
            :max_bytes_toserver, :bulk_transfer_observed,
            'T1041', 'c6', 'simulation_only', 'shadow', FALSE, FALSE
        )
        ON CONFLICT ON CONSTRAINT ux_cybershield_exfil_sensor_flow_window
        DO UPDATE SET
            observed_alerts = EXCLUDED.observed_alerts,
            distinct_observations = EXCLUDED.distinct_observations,
            max_bytes_toserver = EXCLUDED.max_bytes_toserver,
            bulk_transfer_observed = EXCLUDED.bulk_transfer_observed,
            updated_at = NOW()
    """)

    for item in summaries:
        db.execute(query, {
            "sensor_id": sensor_id,
            "flow_id": item.flow_id,
            "window_start": item.window_start,
            "raw_alert_records": item.raw_alert_records,
            "distinct_observations": item.distinct_timestamps,
            "max_bytes_toserver": item.max_bytes_toserver,
            "bulk_transfer_observed": item.bulk_transfer_observed,
        })
    return len(summaries)
