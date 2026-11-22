"""Recomendaciones contextuales de seguridad: código revisado + perfil declarado.

Sin LLM, red, ejecución de código, escrituras de base de datos ni cambios
de protección. Distingue indicios por reglas de necesidades que declara el usuario.
"""
from collections import Counter
from pathlib import PurePosixPath
import re

RULES = {
    "CS-CODE-01": ("Evitar evaluación dinámica de código", "critical", "CWE-95",
        "Se detectó un patrón compatible con evaluación dinámica; validar si el contenido es controlado.",
        "Sustituir evaluación de cadenas por parsers o funciones de una lista permitida.",
        "Revisar el archivo y confirmar que ninguna entrada externa llega a una evaluación dinámica."),
    "CS-CODE-02": ("Reducir exposición a ejecución de comandos", "high", "CWE-78",
        "Se detectó un patrón que podría construir comandos desde datos no confiables.",
        "Usar APIs seguras, evitar shell y validar los argumentos en el servidor.",
        "Inspeccionar flujo de entradas y realizar pruebas autorizadas de validación."),
    "CS-CODE-03": ("Parametrizar consultas a base de datos", "high", "CWE-89",
        "Existe una coincidencia con construcción dinámica de consultas; no confirma inyección.",
        "Usar consultas parametrizadas y permisos mínimos para la cuenta de base de datos.",
        "Revisar la consulta marcada y comprobar que las entradas no alteren su estructura SQL."),
    "CS-CODE-04": ("Mantener la validación TLS", "medium", "CWE-295",
        "Se detectó un ajuste que podría desactivar la verificación de certificados.",
        "Mantener verificación TLS y certificados confiables, sin saltarse errores.",
        "Verificar configuración de clientes HTTPS en entornos de prueba y producción."),
    "CS-CODE-05": ("Desactivar depuración en producción", "high", "CWE-489",
        "Se encontró una configuración compatible con modo de depuración.",
        "Separar configuraciones de desarrollo y producción y ocultar errores internos.",
        "Comprobar que el modo de depuración esté deshabilitado en el despliegue real."),
    "CS-CODE-06": ("Gestionar y rotar posibles secretos", "high", "CWE-798",
        "Se detectó un patrón parecido a un secreto incrustado; requiere comprobación manual.",
        "Mover secretos a un gestor seguro y rotar credenciales realmente expuestas.",
        "Confirmar si el valor es una credencial real sin mostrarla ni copiarla al informe."),
}
LANGUAGES = {
    ".py": "Python", ".php": "PHP", ".ts": "TypeScript", ".tsx": "TypeScript/TSX",
    ".js": "JavaScript", ".jsx": "JavaScript/JSX", ".java": "Java",
    ".go": "Go", ".rb": "Ruby", ".sql": "SQL",
}
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Las recomendaciones contextuales NO son hallazgos detectados.
PROFILE_RULES = (
    ("internet_exposed", "Revisar protección de la superficie pública",
     "high", "La persona indicó que la aplicación está disponible desde internet.",
     "Verificar HTTPS, configuración del servidor, exposición de servicios y límites de solicitudes.",
     "Comprobar con autorización los servicios realmente publicados y sus configuraciones."),
    ("uses_authentication", "Revisar autenticación, sesiones y autorización",
     "high", "La persona indicó que hay cuentas o inicio de sesión.",
     "Aplicar control de acceso del lado servidor, gestión segura de sesiones y límites de intentos.",
     "Probar con cuentas de distintos roles que los recursos ajenos no puedan consultarse."),
    ("handles_sensitive_data", "Proteger información sensible declarada",
     "high", "La persona indicó que se manejan datos sensibles.",
     "Minimizar datos, revisar permisos de acceso, cifrado y manejo de secretos.",
     "Inventariar datos y accesos autorizados; verificar configuraciones reales."),
)


def project_advice(scan: dict, files: list[str], context: dict | None = None) -> dict:
    """Genera propuestas legibles sin convertir coincidencias en vulnerabilidades confirmadas."""
    context = context or {}
    safe_paths = [str(path)[:240] for path in files[:160] if isinstance(path, str)]
    by_language = Counter()
    language_evidence: dict[str, list[str]] = {}
    for path in safe_paths:
        suffix = PurePosixPath(path.replace("\\", "/")).suffix.lower()
        language = LANGUAGES.get(suffix)
        if language:
            by_language[language] += 1
            language_evidence.setdefault(language, [])
            if len(language_evidence[language]) < 2:
                language_evidence[language].append(path)

    recommendations = []
    findings = scan.get("findings", [])
    for rule, (title, priority, cwe, reason, action, verify) in RULES.items():
        matched = [f for f in findings if isinstance(f, dict) and f.get("rule") == rule]
        if not matched:
            continue
        examples = [{
            "file": str(f.get("file", ""))[:240],
            "line": int(f.get("line", 0)) if isinstance(f.get("line"), int) else 0,
            "rule": rule,
        } for f in matched[:3]]
        number = cwe.partition("-")[-1]
        recommendations.append({
            "id": f"code:{rule}",
            "title": title, "priority": priority,
            "reason": reason, "suggested_action": action,
            "verification_plan": verify, "origin": "code_pattern",
            "evidence_status": "requires_human_verification",
            "evidence": examples, "matches": len(matched),
            "reference_url": f"https://cwe.mitre.org/data/definitions/{number}.html",
            "protection_installed": False,
        })

    for key, title, priority, reason, action, verify in PROFILE_RULES:
        if context.get(key) is True:
            recommendations.append({
                "id": f"profile:{key}", "title": title, "priority": priority,
                "reason": reason, "suggested_action": action,
                "verification_plan": verify, "origin": "user_declared",
                "evidence_status": "not_verified_in_code",
                "evidence": [], "matches": 0, "reference_url": None,
                "protection_installed": False,
            })

    if context.get("project_type") == "api":
        recommendations.append({
            "id": "profile:api", "title": "Evaluar controles propios de API",
            "priority": "medium",
            "reason": "La persona describió el proyecto como una API.",
            "suggested_action": "Revisar validación de entradas, autenticación por endpoint, autorización y límites de consumo.",
            "verification_plan": "Inventariar rutas y comprobar controles existentes con pruebas autorizadas.",
            "origin": "user_declared", "evidence_status": "not_verified_in_code",
            "evidence": [], "matches": 0, "reference_url": None,
            "protection_installed": False,
        })

    recommendations.sort(key=lambda rec: (
        PRIORITY_ORDER.get(rec["priority"], 9),
        0 if rec["origin"] == "code_pattern" else 1,
        rec["id"],
    ))
    return {
        "project": {
            "name": str(context.get("name") or "").strip()[:100],
            "description": str(context.get("description") or "").strip()[:1500],
            "project_type": str(context.get("project_type") or "unspecified"),
            "declared_characteristics": [
                key for key in ("internet_exposed", "uses_authentication", "handles_sensitive_data")
                if context.get(key) is True
            ],
            "languages_observed": [
                {"name": name, "files": count, "examples": language_evidence.get(name, [])}
                for name, count in by_language.most_common()
            ],
            "description_origin": "user_declared",
            "technology_origin": "file_extensions_only",
        },
        "recommendations": recommendations[:12],
        "recommendations_total": len(recommendations),
        "source_files_reviewed": int(scan.get("files_scanned", len(safe_paths))),
        "status": "preliminary_contextual_review",
        "automatic_application": False,
        "protection_installed": False,
        "note": (
            "El perfil es declarado por la persona y los lenguajes se infieren solo "
            "de extensiones de archivos. Las coincidencias por reglas son indicios, "
            "no vulnerabilidades demostradas. Las medidas sugeridas por el perfil "
            "no son hallazgos técnicos. El análisis es parcial y no garantiza seguridad."
        ),
    }
