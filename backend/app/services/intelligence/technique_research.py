"""MITRE ATT&CK: informe documental de revisión defensiva, sin IA generativa.

Solo lee tablas existentes; nunca modifica protecciones ni contactos externos.
Los datos documentales no demuestran vulnerabilidad o despliegue local.
"""
import re
from sqlalchemy import text

MITRE_ID = re.compile(r"^T\d{4}(?:\.\d{3})?$")


def build_documentary_report(db, attack_id: str) -> dict:
    """Prepara un informe en español usando exclusivamente datos MITRE importados."""
    attack_id = attack_id.upper()
    if not MITRE_ID.fullmatch(attack_id):
        raise ValueError("Identificador MITRE inválido")

    technique = db.execute(text("""
        SELECT t.attack_id, t.name, t.description,
               t.source_version, t.modified_at
        FROM intelligence_mitre_techniques t
        JOIN intelligence_sources s ON s.id = t.source_id
        WHERE t.attack_id = :attack_id
          AND s.name = 'MITRE ATT&CK Enterprise'
    """), {"attack_id": attack_id}).mappings().first()
    if technique is None:
        raise LookupError("Técnica MITRE no encontrada en el catálogo importado")

    mitigations = db.execute(text("""
        SELECT DISTINCT m.mitigation_id, m.name
        FROM intelligence_mitre_techniques t
        JOIN intelligence_mitre_relationships r
          ON r.technique_id = t.id
        JOIN intelligence_mitre_mitigations m
          ON m.id = r.mitigation_id
        WHERE t.attack_id = :attack_id
        ORDER BY m.mitigation_id
    """), {"attack_id": attack_id}).mappings().all()

    ids = [row["mitigation_id"] for row in mitigations]
    parts = attack_id.split(".")
    reference = "https://attack.mitre.org/techniques/" + "/".join(parts) + "/"
    total = len(ids)
    title = technique["name"]
    return {
        "attack_id": attack_id,
        "name": title,
        "source": "MITRE ATT&CK Enterprise",
        "source_version": technique["source_version"],
        "reference_url": reference,
        "mitigation_count": total,
        "mitigations": [
            {"id": row["mitigation_id"], "name": row["name"]}
            for row in mitigations
        ],
        "summary_es": (
            f"MITRE ATT&CK documenta la técnica {attack_id} ({title}). "
            f"La base de datos de CyberShield contiene {total} "
            f"mitigación(es) documental(es) vinculada(s). "
            "Este resultado no demuestra que un servidor sea vulnerable, "
            "ni que exista una defensa instalada o probada."
        ),
        "verification_steps": [
            "Comprobar si la técnica corresponde al sistema operativo, servicio o activo evaluado.",
            "Revisar la documentación oficial de cada mitigación relacionada.",
            "Comparar las mitigaciones propuestas con controles y sensores realmente configurados.",
            "Solicitar aprobación humana y planificar pruebas autorizadas antes de cualquier implementación.",
        ],
        "mode": "documental_sin_ia_generativa",
        "needs_human_review": True,
        "automatic_application": False,
        "executable_controls_verified": False,
        "note": (
            "Informe generado de forma determinista con los registros MITRE importados. "
            "No es un análisis de IA ni una validación de seguridad del servidor."
        ),
    }
