"""CyberShield Intelligence: consultas autenticadas de solo lectura."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user
from app.database.connection import get_db

router = APIRouter(
    prefix="/intelligence",
    tags=["CyberShield Intelligence"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary")
def intelligence_summary(db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT
          (SELECT COUNT(*) FROM intelligence_threats t
           JOIN intelligence_sources s ON s.id = t.source_id
           WHERE s.name = 'CISA KEV') AS vulnerabilities,
          (SELECT COUNT(*)
           FROM intelligence_mitre_techniques) AS techniques,
          (SELECT COUNT(*)
           FROM intelligence_mitre_mitigations) AS mitigations,
          (SELECT COUNT(*)
           FROM intelligence_mitre_relationships) AS relationships
    """)).mappings().one()

    return {
        "source": "CyberShield Intelligence",
        "vulnerabilities": row["vulnerabilities"],
        "techniques": row["techniques"],
        "mitigations": row["mitigations"],
        "relationships": row["relationships"],
    }


@router.get("/techniques/{attack_id}")
def technique_detail(
    attack_id: str,
    db: Session = Depends(get_db),
):
    attack_id = attack_id.upper()

    if not re.fullmatch(r"T\d{4}(?:\.\d{3})?", attack_id):
        raise HTTPException(
            status_code=422,
            detail="Identificador MITRE inválido",
        )

    technique = db.execute(text("""
        SELECT attack_id, name, description,
               is_subtechnique, modified_at
        FROM intelligence_mitre_techniques
        WHERE attack_id = :attack_id
    """), {"attack_id": attack_id}).mappings().first()

    if technique is None:
        raise HTTPException(
            status_code=404,
            detail="Técnica MITRE no encontrada",
        )

    mitigations = db.execute(text("""
        SELECT m.mitigation_id, m.name, m.description
        FROM intelligence_mitre_mitigations m
        JOIN intelligence_mitre_relationships r
          ON r.mitigation_id = m.id
        JOIN intelligence_mitre_techniques t
          ON t.id = r.technique_id
        WHERE t.attack_id = :attack_id
        ORDER BY m.mitigation_id
    """), {"attack_id": attack_id}).mappings().all()

    result = dict(technique)
    result["mitigations"] = [dict(row) for row in mitigations]
    result["mitigation_count"] = len(mitigations)
    return result


@router.get("/vulnerabilities")
def list_vulnerabilities(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
):
    term = search.strip()

    params = {
        "term": term,
        "pattern": (
            "%" + term.replace("\\", "\\\\")
                      .replace("%", "\\%")
                      .replace("_", "\\_") + "%"
        ),
        "limit": size,
        "offset": (page - 1) * size,
    }

    where_clause = """
        FROM intelligence_threats t
        JOIN intelligence_sources s ON s.id = t.source_id
        WHERE s.name = 'CISA KEV'
          AND (
            :term = ''
            OR t.external_id ILIKE :pattern ESCAPE '\\'
            OR t.name ILIKE :pattern ESCAPE '\\'
          )
    """

    total = db.execute(
        text("SELECT COUNT(*) " + where_clause),
        params,
    ).scalar_one()

    rows = db.execute(text("""
        SELECT t.external_id, t.name, t.description,
               t.reference_url, t.source_version
    """ + where_clause + """
        ORDER BY t.external_id DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    return {
        "page": page,
        "size": size,
        "total": total,
        "items": [dict(row) for row in rows],
    }


@router.get("/protection-coverage")
def protection_coverage(db: Session = Depends(get_db)):
    """Relaciona las 8 protecciones existentes con mitigaciones documentales MITRE.

    Solo lectura: no registra nuevos controles ni ejecuta respuestas.
    """
    from app.api.protections import list_protections

    controls = list_protections()
    technique_ids = {
        entry["technique_id"]
        for control in controls
        for entry in control.get("mitre_techniques", [])
        if entry.get("technique_id")
    }

    # Los parámetros SQL proceden del catálogo interno; se enlazan igualmente
    # para evitar concatenar identificadores en consultas.
    mitigations_by_technique = {technique_id: [] for technique_id in technique_ids}
    for technique_id in sorted(technique_ids):
        rows = db.execute(text("""
            SELECT DISTINCT m.mitigation_id, m.name, m.description
            FROM intelligence_mitre_techniques t
            JOIN intelligence_mitre_relationships r
              ON r.technique_id = t.id
            JOIN intelligence_mitre_mitigations m
              ON m.id = r.mitigation_id
            WHERE t.attack_id = :attack_id
            ORDER BY m.mitigation_id
        """), {"attack_id": technique_id}).mappings().all()
        mitigations_by_technique[technique_id] = [dict(row) for row in rows]

    items = []
    for control in controls:
        mitre_ids = [
            entry["technique_id"]
            for entry in control.get("mitre_techniques", [])
            if entry.get("technique_id")
        ]
        suggestions = {}
        for technique_id in mitre_ids:
            for m in mitigations_by_technique.get(technique_id, []):
                suggestions[m["mitigation_id"]] = m

        items.append({
            "id": control["id"],
            "name": control["name"],
            "sensor": control["sensor"],
            "mode": control["mode"],
            "mitre_techniques": mitre_ids,
            "mitre_mitigations": list(suggestions.values()),
            "mitigation_count": len(suggestions),
            "execution_status": "not_evaluated",
        })

    return {
        "source": "CyberShield Intelligence / MITRE ATT&CK",
        "controls_total": len(items),
        "controls_integrated": sum(x["mode"] == "integrated" for x in items),
        "controls_simulated": sum(x["mode"] == "simulated" for x in items),
        "controls": items,
        "note": (
            "Las mitigaciones MITRE son recomendaciones documentales; "
            "no se han convertido automáticamente en controles ejecutables. "
            "El campo execution_status no certifica una respuesta aplicada."
        ),
    }
