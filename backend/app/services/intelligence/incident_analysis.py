"""Interpretación explicable de incidentes existentes, sin mutaciones."""
from typing import Any, Mapping

from app.cybersecurity.investigation import get_investigation_guide

VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
KNOWN_SOURCES = {"wazuh", "suricata", "lab", "remote_lab_http"}

def analyze_incident(
    incident: Mapping[str, Any],
    event: Mapping[str, Any],
    mitre: Mapping[str, Any] | None,
    response: Mapping[str, Any] | None,
) -> dict:
    severity = str(incident.get("severity") or "unknown").lower()
    event_type = str(event.get("event_type") or "unknown")
    source = str(event.get("source") or "unknown")
    details = event.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    simulated = source == "lab" or details.get("simulation") is True or str(details.get("simulation", "")).lower() == "true"
    scope = str(event.get("scope") or "").upper()
    scope_known = scope in {"BLOCKED", "REACHED", "IMPACT"}
    response_status = str(response.get("status") or "") if response else ""
    priority = ("urgente" if severity == "critical" else
                "alta" if severity == "high" else
                "media" if severity == "medium" else "revisión")
    if scope == "IMPACT":
        impact = "El evento fue clasificado con impacto; debe verificarse la evidencia del efecto."
    elif scope == "BLOCKED":
        impact = "El evento se clasificó como bloqueado antes de producir efecto."
    elif scope == "REACHED":
        impact = "El evento alcanzó el objetivo, sin impacto comprobado en este registro."
    else:
        impact = "No hay alcance confirmado registrado para este evento."
    if not response:
        response_text = "No hay acción defensiva registrada para este incidente."
    elif response_status == "executed":
        response_text = "La base de datos registra una respuesta ejecutada; comprobar evidencia de aplicación."
    elif response_status == "failed":
        response_text = "La base de datos registra una respuesta fallida; requiere atención del operador."
    else:
        response_text = f"Última acción registrada con estado '{response_status}'; no asumir ejecución efectiva."
    mitre_code = str(mitre.get("technique_id") or "") if mitre else ""
    parts = [
        f"Se registró un evento de tipo {event_type} procedente de {source}.",
        f"Severidad registrada: {severity}; prioridad de revisión sugerida: {priority}.",
        impact, response_text,
    ]
    if mitre_code:
        parts.append(f"Existe una clasificación documental MITRE ATT&CK: {mitre_code}.")
    else:
        parts.append("Este incidente no tiene clasificación MITRE registrada.")
    guide = get_investigation_guide(event_type)
    evidence = [
        {"label": "Evento", "value": event_type, "source": "events.event_type"},
        {"label": "Sensor declarado", "value": source, "source": "events.source"},
        {"label": "Severidad", "value": severity, "source": "incidents.severity"},
    ]
    if scope_known:
        evidence.append({"label": "Alcance", "value": scope, "source": "events.scope"})
    if mitre_code:
        evidence.append({"label": "Técnica MITRE", "value": mitre_code, "source": "incident_mitre.technique_id"})
    if response:
        evidence.append({"label": "Estado respuesta", "value": response_status or "sin estado", "source": "response_actions.status"})
    return {
        "incident_id": incident["id"],
        "engine": "deterministic_rules",
        "ai_generated": False,
        "classification": {
            "severity": severity, "priority": priority,
            "mitre_technique_id": mitre_code or None,
            "mitre_technique_name": mitre.get("technique_name") if mitre else None,
            "mitre_tactic": mitre.get("tactic") if mitre else None,
            "simulated": simulated, "scope": scope if scope_known else None,
        },
        "summary": " ".join(parts),
        "evidence": evidence,
        "recommendation": guide["recommendation"],
        "investigation_steps": guide["investigation_steps"],
        "resolution_criteria": guide["resolution_criteria"],
        "response_assessment": response_text,
        "frameworks": [
            {"name": "MITRE ATT&CK", "basis": "Técnica registrada" if mitre_code else "Sin mapeo registrado", "technique_id": mitre_code or None},
            {"name": "NIST CSF 2.0", "basis": "Referencia orientativa a Detect/Respond; no certifica cumplimiento"},
        ],
        "disclaimer": "Interpretación automatizada de registros existentes. No constituye un nuevo incidente, detección validada o prueba de compromiso.",
    }
