"""Catálogo documental unificado de MITRE ATT&CK y CISA KEV.

Consulta únicamente tablas existentes (migraciones 005 y 006).
No visita URLs, no ejecuta IA, no crea incidentes ni instala protecciones.
"""
import re

from sqlalchemy import text

MITRE_ID = re.compile(r"^T\d{4}(?:\.\d{3})?$")
CVE_ID = re.compile(r"^CVE-\d{4}-\d{4,}$")
CISA_CATALOG_URL = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"

# El importador histórico guarda \`requiredAction\` concatenado a description.
# Interpretar solo el separador exacto escrito por import_cisa_kev.prepare_records.
CISA_ACTION_SEPARATOR = "\n\nAcción recomendada por CISA: "


def split_cisa_imported_action(description: str | None) -> tuple[str | None, str | None]:
    """Separa el requiredAction ya guardado, sin generar recomendaciones."""
    if not description:
        return description, None
    before, separator, action = description.rpartition(CISA_ACTION_SEPARATOR)
    if not separator or not action.strip():
        return description, None
    return before.strip() or None, action.strip()


ENTRIES_SQL = """
WITH entries AS (
    SELECT
        'mitre'::text AS kind,
        t.attack_id::text AS external_id,
        t.name::text AS name,
        t.description::text AS description,
        s.name::text AS source_name,
        s.official_url::text AS source_url,
        t.source_version::text AS source_version,
        t.modified_at AS documented_at,
        t.is_subtechnique AS is_subtechnique
    FROM intelligence_mitre_techniques t
    JOIN intelligence_sources s ON s.id = t.source_id
    WHERE s.name = 'MITRE ATT&CK Enterprise'

    UNION ALL

    SELECT
        'cisa'::text AS kind,
        t.external_id::text AS external_id,
        t.name::text AS name,
        t.description::text AS description,
        s.name::text AS source_name,
        s.official_url::text AS source_url,
        t.source_version::text AS source_version,
        t.reviewed_at AS documented_at,
        FALSE AS is_subtechnique
    FROM intelligence_threats t
    JOIN intelligence_sources s ON s.id = t.source_id
    WHERE s.name = 'CISA KEV'
), filtered AS (
    SELECT * FROM entries
    WHERE (:kind = 'all' OR kind = :kind)
      AND (:term = ''
           OR LOWER(external_id) LIKE :pattern ESCAPE '!'
           OR LOWER(name) LIKE :pattern ESCAPE '!')
)
"""


def search_pattern(term: str) -> str:
    """Busca texto literal: !, % y _ no se interpretan como comodines SQL."""
    return "%" + term.lower().replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"


def official_record_url(kind: str, external_id: str) -> str | None:
    """Construye enlaces solo para identificadores oficiales validados."""
    if kind == "mitre" and MITRE_ID.fullmatch(external_id):
        parts = external_id.split(".")
        return "https://attack.mitre.org/techniques/" + "/".join(parts) + "/"
    if kind == "cisa" and CVE_ID.fullmatch(external_id):
        return CISA_CATALOG_URL
    return None


def list_documented_threats(db, *, kind: str = "all", page: int = 1,
                            size: int = 20, search: str = "") -> dict:
    """Vista paginada y de solo lectura sobre fuentes ya importadas.

    Una fila MITRE es técnica/subtécnica; una fila CISA es CVE incluida en KEV.
    Ninguna fila supone que exista una detección o protección instalada.
    """
    if kind not in ("all", "mitre", "cisa"):
        raise ValueError("Tipo de catálogo inválido")
    if page < 1 or not 1 <= size <= 100 or len(search) > 100:
        raise ValueError("Parámetros de paginación inválidos")
    term = search.strip()
    params = {
        "kind": kind, "term": term, "pattern": search_pattern(term),
        "limit": size, "offset": (page - 1) * size,
    }
    total = db.execute(
        text(ENTRIES_SQL + "SELECT COUNT(*) FROM filtered"),
        params,
    ).scalar_one()
    rows = db.execute(text(
        ENTRIES_SQL + """
        SELECT kind, external_id, name, description,
               source_name, source_url, source_version,
               documented_at, is_subtechnique
        FROM filtered
        ORDER BY kind, external_id
        LIMIT :limit OFFSET :offset
        """
    ), params).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        if item["kind"] == "cisa":
            clean_description, required_action = split_cisa_imported_action(
                item["description"]
            )
            item["description"] = clean_description
            item["cisa_required_action"] = required_action
            item["cisa_action_origin"] = (
                "requiredAction del catálogo CISA KEV importado"
                if required_action else None
            )
        else:
            item["cisa_required_action"] = None
            item["cisa_action_origin"] = None
        item["reference_url"] = official_record_url(item["kind"], item["external_id"])
        item["evidence_status"] = "official_catalog_imported"
        item["protection_installed"] = False
        items.append(item)
    return {
        "page": page, "size": size, "total": int(total),
        "kind": kind, "items": items,
        "read_only": True, "automatic_application": False,
        "note": (
            "MITRE describe técnicas; CISA KEV lista vulnerabilidades explotadas conocidas. "
            "Ninguna entrada certifica detección, vulnerabilidad local ni protección instalada."
        ),
    }
