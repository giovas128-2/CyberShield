"""Comparación documental entre recomendaciones de proyecto y controles c1–c8.

El inventario es de CyberShield, NO del proyecto analizado. Una relación
funcional solo sugiere qué control evaluar; jamás certifica cobertura,
instalación, compatibilidad, telemetría o respuesta en el proyecto.
"""
import re

VALID_IDS = frozenset((
    "code:CS-CODE-01", "code:CS-CODE-02", "code:CS-CODE-03",
    "code:CS-CODE-04", "code:CS-CODE-05", "code:CS-CODE-06",
    "profile:internet_exposed", "profile:uses_authentication",
    "profile:handles_sensitive_data", "profile:api",
))
# Solo correspondencias conservadoras. No existe control c1-c8 que
# sustituya una corrección en código (SQL, TLS, depuración o secretos).
RELATED = {
    "profile:uses_authentication": (
        ("c1", "El control c1 vigila señales de fuerza bruta en el laboratorio.",
         "No implementa autorización por roles, gestión segura de sesiones ni protección de contraseñas en la aplicación."),
    ),
    "profile:handles_sensitive_data": (
        ("c5", "El control c5 observa conexiones externas sospechosas con telemetría de Suricata.",
         "No garantiza detección de todas las fugas ni cifrado o control de acceso a los datos de la aplicación."),
        ("c6", "El control c6 representa un escenario de posible exfiltración con datos ficticios.",
         "Es una simulación; no demuestra protección real contra exfiltración."),
    ),
}
NO_DIRECT_NOTE = (
    "Ninguna de las ocho protecciones registradas corrige automáticamente "
    "esta medida en la aplicación. Requiere evaluación o implementación "
    "específica en el proyecto."
)


def compare_recommendations_to_catalog(
    recommendation_ids: list[str],
    controls: list[dict],
) -> dict:
    """Solo clasificación de catálogo; sin SQL, escritura ni llamadas externas."""
    if len(recommendation_ids) > 12 or not recommendation_ids:
        raise ValueError("Se requieren entre 1 y 12 recomendaciones")
    if len(set(recommendation_ids)) != len(recommendation_ids):
        raise ValueError("Existen recomendaciones duplicadas")
    if any(not isinstance(key, str) or key not in VALID_IDS for key in recommendation_ids):
        raise ValueError("Identificador de recomendación no autorizado")

    available = {
        item.get("id"): item for item in controls
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and re.fullmatch(r"c[1-8]", item["id"])
    }
    output = []
    for recommendation_id in recommendation_ids:
        candidates = []
        for control_id, reason, limitation in RELATED.get(recommendation_id, ()):
            control = available.get(control_id)
            if not control:
                continue
            mode = control.get("mode", "unknown")
            candidates.append({
                "id": control_id,
                "name": control.get("name") or control_id,
                "sensor": control.get("sensor") or "no especificado",
                "catalog_mode": mode if mode in {"integrated", "simulated", "pending"} else "unknown",
                "relationship": "complementary",
                "why_related": reason,
                "limitation": limitation,
                "execution_enabled_in_catalog": control.get("execution_enabled")
                   if type(control.get("execution_enabled")) is bool else None,
                "execution_verified_in_catalog": control.get("execution_verified")
                   if type(control.get("execution_verified")) is bool else None,
                "verified_for_project": False,
            })
        output.append({
            "recommendation_id": recommendation_id,
            "coverage": "unverified_for_project",
            "direct_solution_in_catalog": False,
            "related_controls": candidates,
            "missing_action": NO_DIRECT_NOTE,
        })
    return {
        "source": "CyberShield / catálogo de ocho protecciones históricas",
        "catalog_controls_total": len(available),
        "items": output,
        "read_only": True,
        "automatic_application": False,
        "project_controls_verified": False,
        "note": (
            "El diagnóstico previo llega como resumen del navegador y NO se "
            "reanaliza aquí. La relación con un control es solo orientativa; "
            "ni modo integrado ni ejecución verificada en catálogo significa "
            "despliegue en este proyecto. Los controles simulados solo prueban "
            "escenarios de laboratorio. No se instalaron ni activaron defensas."
        ),
    }
