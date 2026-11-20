"""Almacén de borradores MITRE sujeto a revisión humana.

No altera controles existentes. Sin commit: el llamador controla la transacción.
ON CONFLICT DO NOTHING preserva notas y estados que el ingeniero haya revisado.
"""
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.protection_draft_generator import ProtectionDraft


def store_protection_drafts(
    db: Session, drafts: Sequence[ProtectionDraft],
) -> int:
    """Inserta hasta 50 borradores validados; devuelve inserciones nuevas.

    No ejecuta acciones ni crea defensas reales. No actualiza revisiones.
    """
    if len(drafts) > 50:
        raise ValueError("Máximo 50 propuestas por lote")
    identifiers = set()
    for draft in drafts:
        if not isinstance(draft, ProtectionDraft):
            raise TypeError("Se espera ProtectionDraft")
        if (
            draft.status != "review_required"
            or draft.generation_mode != "deterministic_template"
            or draft.telemetry_verified
            or draft.detection_verified
            or draft.execution_allowed
            or draft.executed
        ):
            raise ValueError("Propuesta con estado o ejecución no permitidos")
        if (
            not draft.technique_id
            or len(draft.technique_id) > 32
            or not draft.technique_name.strip()
            or not draft.title.strip()
            or not draft.candidate_sensor.strip()
            or not draft.required_evidence.strip()
            or not draft.validation_plan.strip()
            or type(draft.priority) is not int
            or not 1 <= draft.priority <= 5
        ):
            raise ValueError("Datos de propuesta incompletos")
        if draft.technique_id in identifiers:
            raise ValueError("Técnica duplicada en el lote")
        identifiers.add(draft.technique_id)

    query = text("""
        INSERT INTO cybershield_protection_proposals (
            technique_id, technique_name, title, candidate_sensor,
            required_evidence, validation_plan, priority,
            status, generation_mode, telemetry_verified,
            detection_verified, execution_allowed, executed
        ) VALUES (
            :technique_id, :technique_name, :title, :candidate_sensor,
            :required_evidence, :validation_plan, :priority,
            'review_required', 'deterministic_template', FALSE,
            FALSE, FALSE, FALSE
        )
        ON CONFLICT (technique_id) DO NOTHING
        RETURNING id
    """)
    inserted = 0
    for draft in drafts:
        created = db.execute(query, {
            "technique_id": draft.technique_id,
            "technique_name": draft.technique_name,
            "title": draft.title,
            "candidate_sensor": draft.candidate_sensor,
            "required_evidence": draft.required_evidence,
            "validation_plan": draft.validation_plan,
            "priority": draft.priority,
        }).scalar_one_or_none()
        inserted += int(created is not None)
    return inserted
