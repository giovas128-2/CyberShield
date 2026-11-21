"""Persistencia de decisiones SHADOW después del registro del evento.

Sólo registra decisiones explicables; nunca ejecuta acciones.
La migración 008 es un requisito previo.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.intelligence.defensive_decision_engine import Decision


def save_shadow_decision(db: Session, event_id: int, decision: Decision) -> int:
    if not isinstance(event_id, int) or isinstance(event_id, bool) or event_id <= 0:
        raise ValueError("ID de evento inválido")
    if decision.execution_allowed or decision.executed:
        raise ValueError("El almacén shadow rechaza decisiones ejecutables")

    row = db.execute(text("""
        INSERT INTO cybershield_autonomous_decisions (
            event_id, technique_id, control_id, recommended_action,
            target, decision_status, reason, mode,
            execution_allowed, executed
        )
        VALUES (
            :event_id, :technique_id, :control_id, :action,
            CAST(:target AS inet), :status, :reason, 'shadow',
            FALSE, FALSE
        )
        ON CONFLICT (event_id) DO UPDATE SET
            technique_id = EXCLUDED.technique_id,
            control_id = EXCLUDED.control_id,
            recommended_action = EXCLUDED.recommended_action,
            target = EXCLUDED.target,
            decision_status = EXCLUDED.decision_status,
            reason = EXCLUDED.reason,
            updated_at = NOW()
        RETURNING id
    """), {
        "event_id": event_id,
        "technique_id": decision.technique_id,
        "control_id": decision.control_id,
        "action": decision.recommended_action,
        "target": decision.target,
        "status": decision.status,
        "reason": decision.reason,
    }).scalar_one()
    db.commit()
    return row
