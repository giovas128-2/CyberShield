"""Plan preliminar de seguridad por proyecto, sin persistencia ni ejecución.

Se deriva exclusivamente de identificadores reconocidos por el asesor,
más relaciones comprobadas contra el catálogo interno c1-c8.
No incluye código, evidencias textuales, secretos ni datos personales.
"""
from app.services.intelligence.project_advisor import RULES, PROFILE_RULES

PROFILE_MAP = {
    key: (title, priority, reason, action, verify)
    for key, title, priority, reason, action, verify in PROFILE_RULES
}
API_RULE = (
    "Evaluar controles propios de API", "medium",
    "La persona declaró que su aplicación es una API.",
    "Revisar validación de entradas, autenticación por endpoint, autorización y límites de consumo.",
    "Inventariar rutas y comprobar controles existentes con pruebas autorizadas.",
)
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _known_recommendation(recommendation_id: str) -> dict:
    if recommendation_id.startswith("code:") and recommendation_id[5:] in RULES:
        rule = recommendation_id[5:]
        title, priority, cwe, reason, action, verify = RULES[rule]
        number = cwe.partition("-")[2]
        return {
            "title": title, "priority": priority, "origin": "code_pattern",
            "action_type": "code_correction", "owner_role": "developer",
            "rationale": reason, "next_step": action,
            "verification": verify,
            "reference_url": f"https://cwe.mitre.org/data/definitions/{number}.html",
        }
    key = recommendation_id.partition(":")[2]
    if recommendation_id.startswith("profile:"):
        info = PROFILE_MAP.get(key)
        if key == "api":
            info = API_RULE
        if info:
            title, priority, reason, action, verify = info
            return {
                "title": title, "priority": priority, "origin": "user_declared",
                "action_type": (
                    "control_evaluation" if key in ("uses_authentication", "handles_sensitive_data")
                    else "environment_review"
                ),
                "owner_role": "security_engineer",
                "rationale": reason, "next_step": action,
                "verification": verify, "reference_url": None,
            }
    raise ValueError("Recomendación no admitida en el plan")


def build_security_plan(comparison_items: list[dict]) -> dict:
    """Crear borradores de tareas, sin estados de aprobación ni efectos secundarios."""
    if not isinstance(comparison_items, list) or not 1 <= len(comparison_items) <= 12:
        raise ValueError("El plan requiere de 1 a 12 recomendaciones")
    seen = set()
    tasks = []
    for item in comparison_items:
        recommendation_id = item.get("recommendation_id")
        if not isinstance(recommendation_id, str) or recommendation_id in seen:
            raise ValueError("Identificador inválido o duplicado")
        seen.add(recommendation_id)
        base = _known_recommendation(recommendation_id)
        control_ids = []
        # Las relaciones complementarias proceden del comparador c1-c8,
        # nunca equivalen a controles instalados en el proyecto.
        for control in item.get("related_controls", []):
            control_id = control.get("id") if isinstance(control, dict) else None
            if control_id in ("c1", "c5", "c6") and control_id not in control_ids:
                control_ids.append(control_id)
        tasks.append({
            "task_id": recommendation_id,
            **base,
            "related_catalog_controls": control_ids,
            "status": "draft_for_human_review",
            "project_deployment_verified": False,
            "implementation_approved": False,
            "execution_allowed": False,
        })
    tasks.sort(key=lambda t: (
        PRIORITY_ORDER.get(t["priority"], 9),
        0 if t["origin"] == "code_pattern" else 1,
        t["task_id"],
    ))
    return {
        "mode": "local_review_draft",
        "tasks": tasks,
        "tasks_total": len(tasks),
        "code_corrections": sum(t["action_type"] == "code_correction" for t in tasks),
        "control_evaluations": sum(t["action_type"] == "control_evaluation" for t in tasks),
        "environment_reviews": sum(t["action_type"] == "environment_review" for t in tasks),
        "stored_in_database": False,
        "read_only": True,
        "automatic_application": False,
        "human_review_required": True,
        "project_protections_verified": 0,
        "note": (
            "Borrador documental de planificación. No se ha guardado como propuesta "
            "formal, no representa aprobación ni implementación, y no acredita "
            "protecciones desplegadas en el proyecto. Cualquier medida requiere "
            "validación humana y autorización antes de aplicarse."
        ),
    }
