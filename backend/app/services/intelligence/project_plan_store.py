"""Bandeja aislada de planes de proyecto. No escribe controles ni ejecuta acciones."""
import json
from sqlalchemy import text

from app.services.intelligence.project_protection_comparison import (
    compare_recommendations_to_catalog,
)

def list_protections(db):
    """Consulta real solo cuando se crea un plan, no durante un import de pruebas.

    Se conserva esta función como punto de sustitución para pruebas aisladas.
    """
    from app.api.protections import list_protections as read_protections
    return read_protections(db)


TABLE = "cybershield_project_review_plans"
ALLOWED_NEXT = {
    "review_required": frozenset(("under_review", "rejected")),
    "under_review": frozenset(("planned", "rejected")),
    "planned": frozenset(),
    "rejected": frozenset(),
}


class PlanStoreMissing(Exception):
    """La migración 014 todavía no está instalada."""


class PlanNotFound(Exception):
    pass


class PlanConflict(Exception):
    pass


def require_plan_tables(db):
    # Sin migraciones automáticas. La aprobación de aplicar SQL es separada.
    reg = db.execute(text("""
        SELECT to_regclass('public.cybershield_project_review_plans') IS NOT NULL
           AND to_regclass('public.cybershield_project_review_tasks') IS NOT NULL
           AND to_regclass('public.cybershield_project_review_history') IS NOT NULL
    """)).scalar_one()
    if not reg:
        raise PlanStoreMissing(
            "La bandeja aún no está habilitada. La migración 014 debe "
            "validarse y aplicarse únicamente a la base de pruebas."
        )


def create_plan(db, actor_id: int, project_name: str,
                recommendation_ids: list[str]) -> dict:
    if not isinstance(actor_id, int) or actor_id < 1:
        raise ValueError("Usuario no identificado")
    name = project_name.strip()
    if not 1 <= len(name) <= 100:
        raise ValueError("Nombre del plan inválido")
    require_plan_tables(db)
    # La lista del cliente contiene exclusivamente códigos permitidos.
    # Todos los textos del plan se reconstruyen en el servidor.
    comparison = compare_recommendations_to_catalog(
        recommendation_ids, list_protections(db)
    )
    tasks = comparison["project_plan"]["tasks"]
    try:
        inserted = db.execute(text("""
            INSERT INTO public.cybershield_project_review_plans
                (project_name, created_by, task_snapshot)
            VALUES (:name, :actor, CAST(:snapshot AS jsonb))
            RETURNING id, project_name, created_by, created_at
        """), {
            "name": name, "actor": actor_id,
            "snapshot": json.dumps(tasks, ensure_ascii=False),
        }).mappings().one()
        for task in tasks:
            db.execute(text("""
                INSERT INTO public.cybershield_project_review_tasks
                    (plan_id, recommendation_id)
                VALUES (:plan_id, :recommendation_id)
            """), {
                "plan_id": inserted["id"],
                "recommendation_id": task["task_id"],
            })
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        **dict(inserted), "tasks_total": len(tasks),
        "status": "review_required", "stored_in_database": True,
        "implementation_approved": False, "execution_allowed": False,
        "note": "Plan registrado sin instalar ni aprobar protecciones.",
    }


def list_plans(db, page: int, size: int) -> dict:
    require_plan_tables(db)
    params = {"limit": size, "offset": (page - 1) * size}
    total = db.execute(text("""
        SELECT COUNT(*) FROM public.cybershield_project_review_plans
    """)).scalar_one()
    rows = db.execute(text("""
        SELECT p.id, p.project_name, p.created_by, p.created_at,
            COUNT(t.id)::integer AS tasks_total,
            COUNT(t.id) FILTER (WHERE t.status = 'review_required')::integer AS pending,
            COUNT(t.id) FILTER (WHERE t.status = 'under_review')::integer AS reviewing,
            COUNT(t.id) FILTER (WHERE t.status = 'planned')::integer AS planned,
            COUNT(t.id) FILTER (WHERE t.status = 'rejected')::integer AS rejected
        FROM public.cybershield_project_review_plans p
        JOIN public.cybershield_project_review_tasks t ON t.plan_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC, p.id DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    return {
        "page": page, "size": size, "total": total,
        "items": [dict(r) for r in rows], "execution_allowed": False,
    }


def get_plan(db, plan_id: int) -> dict:
    require_plan_tables(db)
    head = db.execute(text("""
        SELECT id, project_name, created_by, task_snapshot, created_at
        FROM public.cybershield_project_review_plans
        WHERE id = :plan_id
    """), {"plan_id": plan_id}).mappings().first()
    if head is None:
        raise PlanNotFound("Plan no encontrado")
    data = dict(head)
    snapshot = data.pop("task_snapshot")
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    reviews = db.execute(text("""
        SELECT id, recommendation_id, status, reviewed_by,
               review_notes, reviewed_at, created_at
        FROM public.cybershield_project_review_tasks
        WHERE plan_id = :plan_id
        ORDER BY id ASC
    """), {"plan_id": plan_id}).mappings().all()
    history = db.execute(text("""
        SELECT h.id, h.task_id, h.actor_id, h.from_status,
               h.to_status, h.notes, h.created_at
        FROM public.cybershield_project_review_history h
        JOIN public.cybershield_project_review_tasks t ON t.id = h.task_id
        WHERE t.plan_id = :plan_id
        ORDER BY h.id DESC
        LIMIT 100
    """), {"plan_id": plan_id}).mappings().all()
    by_code = {t["recommendation_id"]: dict(t) for t in reviews}
    data["tasks"] = [
        {**task, "review": by_code.get(task["task_id"])}
        for task in snapshot
    ]
    data["history"] = [dict(r) for r in history]
    data["execution_allowed"] = False
    data["implementation_approved"] = False
    data["note"] = (
        "Plan persistente para revisión documental. 'Aceptada para planificación' "
        "no significa instalada, aprobada para ejecución ni verificada en el proyecto."
    )
    return data


def review_task(db, plan_id: int, task_id: int, actor_id: int,
                next_status: str, notes: str) -> dict:
    require_plan_tables(db)
    if not isinstance(actor_id, int) or actor_id < 1:
        raise ValueError("Usuario no identificado")
    note = notes.strip()
    if len(note) < 10 or len(note) > 2000:
        raise ValueError("Las observaciones requieren entre 10 y 2000 caracteres")
    # Bloqueo sobre la tarea; solo transición autorizada. Estado terminal no reversible.
    try:
        row = db.execute(text("""
            SELECT id, plan_id, recommendation_id, status
            FROM public.cybershield_project_review_tasks
            WHERE id = :task_id AND plan_id = :plan_id
            FOR UPDATE
        """), {"task_id": task_id, "plan_id": plan_id}).mappings().first()
        if row is None:
            raise PlanNotFound("Tarea no encontrada")
        old_status = row["status"]
        if next_status not in ALLOWED_NEXT.get(old_status, frozenset()):
            raise PlanConflict("Transición no permitida para esta tarea")
        updated = db.execute(text("""
            UPDATE public.cybershield_project_review_tasks
            SET status = :next_status, reviewed_by = :actor_id,
                review_notes = :notes, reviewed_at = NOW()
            WHERE id = :task_id AND plan_id = :plan_id
              AND status = :old_status
            RETURNING id, plan_id, recommendation_id, status,
                      reviewed_by, review_notes, reviewed_at
        """), {
            "next_status": next_status, "actor_id": actor_id,
            "notes": note, "task_id": task_id,
            "plan_id": plan_id, "old_status": old_status,
        }).mappings().first()
        if updated is None:
            raise PlanConflict("La tarea cambió de estado durante la revisión")
        db.execute(text("""
            INSERT INTO public.cybershield_project_review_history
                (task_id, actor_id, from_status, to_status, notes)
            VALUES (:task_id, :actor_id, :old_status, :next_status, :notes)
        """), {
            "task_id": task_id, "actor_id": actor_id,
            "old_status": old_status, "next_status": next_status, "notes": note,
        })
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "task": dict(updated), "history_recorded": True,
        "execution_allowed": False, "implementation_approved": False,
        "note": "Estado de revisión guardado. No se ejecutó ninguna defensa.",
    }
