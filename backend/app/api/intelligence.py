"""CyberShield Intelligence: consultas autenticadas de solo lectura."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user, require_roles
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

    controls = list_protections(db)
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


# ============================================================
# PROPUESTAS MITRE: BANDEJA DE SOLO LECTURA
# Roles: engineer, admin. Sin endpoints POST/PATCH/DELETE.
# ============================================================

@router.get("/protection-proposals")
def list_protection_proposals(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    """Lista propuestas persistidas, sin capacidad de aprobar ni ejecutar."""
    allowed = {"review_required", "under_review", "rejected"}
    if status is not None and status not in allowed:
        raise HTTPException(status_code=422, detail="Estado de propuesta inválido")
    params = {
        "status": status,
        "limit": size,
        "offset": (page - 1) * size,
    }
    clause = """
        FROM cybershield_protection_proposals
        WHERE (CAST(:status AS TEXT) IS NULL OR status = CAST(:status AS TEXT))
    """
    total = db.execute(
        text("SELECT COUNT(*) " + clause), params
    ).scalar_one()
    rows = db.execute(text("""
        SELECT id, technique_id, technique_name, title,
               candidate_sensor, required_evidence, validation_plan,
               priority, status, generation_mode,
               telemetry_verified, detection_verified,
               execution_allowed, executed,
               review_notes, reviewed_by, reviewed_at, created_at, updated_at
    """ + clause + """
        ORDER BY priority ASC, id ASC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    return {
        "page": page,
        "size": size,
        "total": total,
        "items": [dict(row) for row in rows],
        "read_only": True,
    }


@router.get("/protection-proposals/{proposal_id}")
def protection_proposal_detail(
    proposal_id: int,
    db: Session = Depends(get_db),
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    """Detalle de propuesta para ingeniero autenticado, solo SELECT."""
    if proposal_id < 1:
        raise HTTPException(status_code=422, detail="ID de propuesta inválido")
    row = db.execute(text("""
        SELECT id, technique_id, technique_name, title,
               candidate_sensor, required_evidence, validation_plan,
               priority, status, generation_mode,
               telemetry_verified, detection_verified,
               execution_allowed, executed,
               review_notes, reviewed_by, reviewed_at, created_at, updated_at
        FROM cybershield_protection_proposals
        WHERE id = :proposal_id
    """), {"proposal_id": proposal_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    return dict(row)


# ============================================================
# REVISIÓN HUMANA NO EJECUTABLE
# No admite aprobación ni registro en catálogo de defensas.
# ============================================================

class ProposalReviewRequest(BaseModel):
    status: Literal["under_review", "rejected"]
    notes: str = Field(min_length=10, max_length=2000)


@router.patch("/protection-proposals/{proposal_id}/review")
def review_protection_proposal(
    proposal_id: int,
    payload: ProposalReviewRequest,
    db: Session = Depends(get_db),
    reviewer = Depends(require_roles("admin", "engineer")),
):
    """Cambia solo estado y notas; bloquea propuestas rechazadas.

    La transición atómica impide sobrescribir una revisión terminal.
    No cambia catálogo de protecciones ni permite ejecución.
    """
    if proposal_id < 1:
        raise HTTPException(status_code=422, detail="ID de propuesta inválido")
    notes = payload.notes.strip()
    if len(notes) < 10:
        raise HTTPException(status_code=422, detail="Escribe al menos 10 caracteres de observaciones")
    actor_id = getattr(reviewer, "id", None)
    if not isinstance(actor_id, int) or actor_id < 1:
        raise HTTPException(status_code=403, detail="Revisor no identificado")

    # Actualización atómica: solo se permiten estas transiciones.
    # No existe estado 'approved' en esta tabla.
    row = db.execute(text("""
        UPDATE cybershield_protection_proposals
        SET status = :next_status,
            review_notes = :review_notes,
            reviewed_by = :reviewed_by,
            reviewed_at = NOW(),
            updated_at = NOW()
        WHERE id = :proposal_id
          AND status IN ('review_required', 'under_review')
          AND execution_allowed = FALSE
          AND executed = FALSE
          AND telemetry_verified = FALSE
          AND detection_verified = FALSE
        RETURNING id, technique_id, status, review_notes,
                  reviewed_by, reviewed_at, execution_allowed, executed
    """), {
        "proposal_id": proposal_id,
        "next_status": payload.status,
        "review_notes": notes,
        "reviewed_by": str(actor_id),
    }).mappings().first()

    if row is None:
        db.rollback()
        exists = db.execute(text("""
            SELECT status FROM cybershield_protection_proposals
            WHERE id = :proposal_id
        """), {"proposal_id": proposal_id}).scalar_one_or_none()
        if exists is None:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        raise HTTPException(
            status_code=409,
            detail="La propuesta ya fue rechazada o no puede revisarse en su estado actual",
        )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "success": True,
        "proposal": dict(row),
        "execution_allowed": False,
        "executed": False,
        "note": "La revisión no activa ni aprueba defensas",
    }


# ============================================================
# AUDITORÍA DE CÓDIGO (SIN EJECUCIÓN NI CREACIÓN DE INCIDENTES)
# ============================================================

class CodeFilePayload(BaseModel):
    path: str = Field(min_length=1, max_length=240)
    content: str = Field(max_length=60000)


class CodeReviewPayload(BaseModel):
    files: list[CodeFilePayload] = Field(min_length=1, max_length=20)
    use_ai: bool = False


class GithubReviewPayload(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    branch: str = Field(default="", max_length=100)
    use_ai: bool = False


@router.post("/code-review/files")
def review_code_files(
    payload: CodeReviewPayload,
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    """Procesa solamente código fuente enviado voluntariamente, sin almacenarlo."""
    from app.services.intelligence.code_review import scan_sources, explain_with_llm
    try:
        scan = scan_sources([item.model_dump() for item in payload.files])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scan["analysis"] = explain_with_llm(scan, payload.use_ai)
    return scan


@router.post("/code-review/github")
def review_github_repository(
    payload: GithubReviewPayload,
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    """Consulta la API pública de GitHub; nunca clona ni ejecuta el repositorio."""
    import httpx
    from app.services.intelligence.code_review import (
        github_public_files, scan_sources, explain_with_llm,
    )
    try:
        files = github_public_files(payload.owner, payload.repo, payload.branch)
        scan = scan_sources(files)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (httpx.HTTPStatusError, httpx.RequestError):
        raise HTTPException(
            status_code=502,
            detail="No se pudo leer el repositorio público. Comprueba nombre, rama y conectividad.",
        )
    scan["analysis"] = explain_with_llm(scan, payload.use_ai)
    return scan


class ZipReviewPayload(BaseModel):
    """ZIP enviado como base64 para evitar dependencias multipart adicionales."""
    filename: str = Field(default="proyecto.zip",max_length=200)
    archive_base64: str = Field(min_length=4,max_length=10_666_672)
    use_ai: bool = False


@router.post("/code-review/zip")
def review_zip_project(
    payload: ZipReviewPayload,
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    """Analiza realmente el código de un ZIP, sin extraerlo ni ejecutarlo.

    IA opcional requiere habilitación explícita y OPENAI_API_KEY. Solo entonces
    se envía al proveedor una muestra acotada de fragmentos del proyecto.
    """
    from app.services.intelligence.archive_review import (
        decode_archive, analyze_zip, review_zip_with_ai,
    )
    if not payload.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=422, detail="Solo se admiten archivos .zip")
    try:
        raw = decode_archive(payload.archive_base64)
        scan, sources = analyze_zip(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scan["analysis"] = review_zip_with_ai(scan, sources, payload.use_ai)
    return scan


# ============================================================
# INVESTIGACIÓN DE FUENTES OFICIALES PARA LAS 8 PROTECCIONES
# GET: solo PostgreSQL (sin bloquear la interfaz con solicitudes externas).
# POST: consulta HTTPS únicamente a MITRE/NIST/CIS/CISA (rol autorizado).
# No envía datos internos a terceros ni modifica reglas o defensas.
# ============================================================

@router.get("/official-frameworks")
def official_frameworks(db: Session = Depends(get_db)):
    from app.api.protections import list_protections
    from app.services.intelligence.official_frameworks import (
        read_snapshots, references_for_controls, table_exists,
    )
    configured = table_exists(db)
    return {
        "configured": configured,
        "sources": read_snapshots(db),
        "controls": references_for_controls(list_protections(db)),
        "automatic_application": False,
        "note": (
            "Las referencias NIST/CIS son orientativas y requieren validación humana. "
            "La comprobación solo observa cambios de versión o del catálogo CISA; "
            "no demuestra protección desplegada ni aplica reglas nuevas. "
            "Si falta la migración 013, instala la tabla antes de consultar."
        ),
    }


@router.post("/official-frameworks/check")
def check_official_frameworks(
    db: Session = Depends(get_db),
    _reviewer=Depends(require_roles("admin", "engineer")),
):
    from app.api.protections import list_protections
    from app.services.intelligence.official_frameworks import (
        check_official_sources, references_for_controls, table_exists,
    )
    if not table_exists(db):
        raise HTTPException(
            status_code=503, detail="Falta migración 013_official_framework_checks.sql"
        )
    result = check_official_sources(db)
    return {
        "configured": True,
        "sources": result["sources"],
        "failed_sources": result["failed_sources"],
        "controls": references_for_controls(list_protections(db)),
        "automatic_application": False,
        "note": "Consulta verificada de fuentes oficiales; sin modificar las defensas.",
    }


@router.post("/official-frameworks/ai-review")
def official_frameworks_ai_review(
    db: Session = Depends(get_db),
    _reviewer=Depends(require_roles("admin", "engineer")),
):
    """Solo tras petición explícita, interpretar metadatos públicos verificados."""
    from app.services.intelligence.official_frameworks import (
        explain_official_changes_with_ai, table_exists,
    )
    if not table_exists(db):
        raise HTTPException(
            status_code=503, detail="Falta migración 013_official_framework_checks.sql"
        )
    return explain_official_changes_with_ai(db)

# ============================================================
# CATALOGO DOCUMENTAL UNIFICADO (MITRE + CISA) — SOLO LECTURA
# Reutiliza migraciones 005/006. Nunca habilita defensas.
# ============================================================

@router.get("/threat-catalog")
def documented_threat_catalog(
    kind: Literal["all", "mitre", "cisa"] = Query(default="all"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
):
    from app.services.intelligence.threat_catalog import list_documented_threats
    return list_documented_threats(
        db, kind=kind, page=page, size=size, search=search,
    )

# ============================================================
# INVESTIGACIÓN DOCUMENTAL EN ESPAÑOL (SIN IA GENERATIVA)
# MITRE importado, solo consultas, sin modificaciones de defensas.
# ============================================================

@router.get("/techniques/{attack_id}/research")
def technique_documentary_research(
    attack_id: str,
    db: Session = Depends(get_db),
):
    from app.services.intelligence.technique_research import build_documentary_report
    try:
        return build_documentary_report(db, attack_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

# ============================================================
# IA LOCAL OPCIONAL — OLLAMA EN LOOPBACK (SIN COSTO DE API)
# Acceso solo admin/engineer; deshabilitada por defecto.
# ============================================================

@router.get("/local-ai/status")
def local_ai_status_endpoint(
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    from app.services.intelligence.local_ollama import local_ai_status
    return local_ai_status()


@router.post("/local-ai/techniques/{attack_id}/interpret")
def local_ai_interpret_technique(
    attack_id: str,
    db: Session = Depends(get_db),
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    from app.services.intelligence.local_ollama import (
        LocalAIUnavailable,
        interpret_mitre_with_local_ai,
    )
    try:
        return interpret_mitre_with_local_ai(db, attack_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalAIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
