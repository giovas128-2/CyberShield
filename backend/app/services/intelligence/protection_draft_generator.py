"""CyberShield: borradores de cobertura MITRE para revisión HUMANA.

Motor determinista inicial: NO usa un LLM, NO instala reglas, NO crea controles
en BD, NO envía comandos y NO declara una técnica detectada. Los sensores
enumerados son posibilidades de investigación, no capacidades verificadas.
"""
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

# Hipótesis de observabilidad que requieren revisión técnica individual.
# Solo técnica exacta del inventario local; nunca extrapolar sub-técnicas.
CANDIDATE_RECIPES = {
    "T1001.003": {
        "title": "Revisar suplantación de protocolo o servicio",
        "sensor": "Suricata (EVE)",
        "evidence": "Alertas IDS específicas y metadatos de protocolos; falta validar reglas, falsos positivos y tráfico permitido",
        "validation": "Revisión pasiva de alertas existentes y reglas IDS en laboratorio, sin bloquear tráfico",
        "priority": 2,
    },
    "T1003.008": {
        "title": "Evaluar exposición de /etc/passwd y /etc/shadow",
        "sensor": "Wazuh (FIM + telemetría adicional por definir)",
        "evidence": "La FIM identifica cambios, no lecturas; se requieren registros de acceso auditados y contexto de proceso",
        "validation": "Revisar disponibilidad de auditoría de lectura en datos sintéticos; sin acceder a credenciales reales",
        "priority": 3,
    },
    "T1005": {
        "title": "Investigar recolección anómala de datos locales",
        "sensor": "Wazuh (eventos de proceso, si están habilitados)",
        "evidence": "Acceso a archivos y secuencia de procesos; FIM por sí sola es insuficiente para observar lectura",
        "validation": "Verificar cobertura de telemetría de procesos con datos de prueba existentes",
        "priority": 3,
    },
    "T1059": {
        "title": "Investigar ejecución anómala de intérpretes",
        "sensor": "Wazuh (telemetría de procesos, si está habilitada)",
        "evidence": "Creación de procesos, intérprete, argumentos filtrados y contexto del usuario; no se ha validado su disponibilidad",
        "validation": "Comprobar si ya existen registros de procesos seguros y ejemplos sintéticos",
        "priority": 1,
    },
}


@dataclass(frozen=True)
class ProtectionDraft:
    technique_id: str
    technique_name: str
    title: str
    candidate_sensor: str
    required_evidence: str
    validation_plan: str
    priority: int
    status: str = "review_required"
    generation_mode: str = "deterministic_template"
    telemetry_verified: bool = False
    detection_verified: bool = False
    execution_allowed: bool = False
    executed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def generate_protection_drafts(
    techniques: Sequence[Mapping[str, Any]],
    controls: Sequence[Mapping[str, Any]],
    *,
    limit: int = 10,
) -> tuple[ProtectionDraft, ...]:
    """Genera borradores sólo de técnicas conocidas sin control asociado."""
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("limit debe estar entre 1 y 50")

    covered = set()
    for control in controls:
        entries = control.get("mitre_techniques")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                identifier = entry.get("technique_id")
                if isinstance(identifier, str):
                    covered.add(identifier.strip())

    known = {}
    for item in techniques:
        code = item.get("attack_id")
        if isinstance(code, str) and code.strip():
            known[code.strip()] = str(item.get("name") or "")

    drafts = []
    for attack_id, recipe in CANDIDATE_RECIPES.items():
        if attack_id in covered or attack_id not in known:
            continue
        drafts.append(ProtectionDraft(
            technique_id=attack_id,
            technique_name=known[attack_id],
            title=recipe["title"],
            candidate_sensor=recipe["sensor"],
            required_evidence=recipe["evidence"],
            validation_plan=recipe["validation"],
            priority=recipe["priority"],
        ))
    drafts.sort(key=lambda d: (d.priority, d.technique_id))
    return tuple(drafts[:limit])


def protection_drafts_from_database(
    db: Session, *, limit: int = 10,
) -> tuple[ProtectionDraft, ...]:
    """Solo SELECT sobre conocimiento y catálogo; ninguna escritura."""
    techniques = db.execute(text("""
        SELECT attack_id, name FROM intelligence_mitre_techniques
        WHERE attack_id IS NOT NULL
    """)).mappings().all()
    controls = db.execute(text("""
        SELECT mitre_techniques FROM cybershield_protection_catalog
    """)).mappings().all()
    return generate_protection_drafts(techniques, controls, limit=limit)
