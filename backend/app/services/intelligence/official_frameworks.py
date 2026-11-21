"""Investigación defensiva de versiones en fuentes oficiales (sin ejecutar defensas).

Solo URLs fijas, HTTPS y datos públicos. No se envían incidentes, servidores,
credenciales o telemetría a fuentes externas ni a modelos de IA.
La primera consulta válida establece una referencia; posteriores cambios
de versión/catálogo requieren revisión humana, nunca aplicación automática.
"""
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import re

import httpx
from sqlalchemy import text

SOURCE_DEFS = (
    {"key": "mitre", "name": "MITRE ATT&CK Enterprise",
     "url": "https://attack.mitre.org/resources/versions/"},
    {"key": "nist", "name": "NIST Cybersecurity Framework",
     "url": "https://www.nist.gov/cyberframework"},
    {"key": "cis", "name": "CIS Critical Security Controls",
     "url": "https://www.cisecurity.org/controls"},
    {"key": "cisa", "name": "CISA Known Exploited Vulnerabilities",
     "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"},
)
SOURCE_BY_KEY = {source["key"]: source for source in SOURCE_DEFS}
TABLE = "public.intelligence_official_framework_checks"
MAX_HTML_BYTES = 2_000_000
MAX_CISA_BYTES = 20_000_000

# Alineaciones orientativas; NO equivalen a certificación NIST/CIS.
CONTROL_REFERENCES = {
    "c1": {"cis": ["6 · Gestión de accesos", "8 · Registros de auditoría"],
           "nist": ["Proteger · Identidades y control de acceso", "Detectar · Monitorización continua"]},
    "c2": {"cis": ["1 · Inventario de activos", "6 · Gestión de accesos"],
           "nist": ["Identificar · Gestión de activos", "Proteger · Identidades y control de acceso"]},
    "c3": {"cis": ["3 · Protección de datos", "8 · Registros de auditoría"],
           "nist": ["Proteger · Seguridad de los datos", "Detectar · Monitorización continua"]},
    "c4": {"cis": ["5 · Gestión de cuentas", "6 · Gestión de accesos"],
           "nist": ["Proteger · Identidades y control de acceso", "Detectar · Monitorización continua"]},
    "c5": {"cis": ["12 · Infraestructura de red", "13 · Monitorización y defensa de red"],
           "nist": ["Detectar · Monitorización continua", "Responder · Gestión de incidentes"]},
    "c6": {"cis": ["3 · Protección de datos", "13 · Monitorización y defensa de red"],
           "nist": ["Proteger · Seguridad de los datos", "Detectar · Monitorización continua"]},
    "c7": {"cis": ["10 · Defensas contra malware", "11 · Recuperación de datos"],
           "nist": ["Detectar · Análisis de eventos", "Recuperar · Planificación y ejecución"]},
    "c8": {"cis": ["6 · Gestión de accesos", "13 · Monitorización y defensa de red"],
           "nist": ["Proteger · Identidades y control de acceso", "Detectar · Monitorización continua"]},
}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def version_from_page(key: str, html: str) -> str:
    """Solo versiones detectadas en el documento oficial; nunca inventar."""
    parser = PlainText()
    parser.feed(html)
    body = " ".join(parser.text().split())
    patterns = {
        "mitre": r"ATT&CK\s+(?:content\s+)?v(\d{1,2}(?:\.\d{1,2})?)\b",
        "nist": r"\b(?:CSF|Cybersecurity Framework)\s+(?:version\s*)?(\d{1,2}\.\d{1,2})\b",
        "cis": r"\b(?:CIS\s+(?:Critical\s+Security\s+)?Controls)\s+v(?:ersion\s*)?(\d{1,2}\.\d{1,2})\b",
    }
    if key not in patterns:
        raise ValueError("Fuente no compatible con HTML")
    values = re.findall(patterns[key], body, flags=re.IGNORECASE)
    if not values:
        raise ValueError("No se pudo verificar la versión en la página oficial")
    return max(values, key=lambda value: tuple(int(part) for part in value.split(".")))


def read_official_source(key: str, *, transport=None) -> dict:
    """Consulta únicamente destinos codificados. No hay URL de usuario ni redirecciones."""
    source = SOURCE_BY_KEY[key]
    with httpx.Client(timeout=15, follow_redirects=False, transport=transport,
                      headers={"User-Agent": "CyberShield-Academic-Official-Framework-Monitor/1.0",
                               "Accept": "text/html,application/json"}) as client:
        with client.stream("GET", source["url"]) as response:
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code} en fuente oficial")
            max_bytes = MAX_CISA_BYTES if key == "cisa" else MAX_HTML_BYTES
            collected = bytearray()
            for chunk in response.iter_bytes():
                collected.extend(chunk)
                if len(collected) > max_bytes:
                    raise ValueError("La fuente supera el tamaño autorizado")
            raw = bytes(collected)

    if key == "cisa":
        import json
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("vulnerabilities"), list):
            raise ValueError("Formato CISA KEV inválido")
        entries = data["vulnerabilities"]
        if not entries:
            raise ValueError("Catálogo CISA KEV vacío")
        ids = []
        cve_ids = set()
        for item in entries:
            if not isinstance(item, dict) or not re.fullmatch(
                r"CVE-\d{4}-\d{4,}", str(item.get("cveID", ""))
            ):
                raise ValueError("Entrada CISA KEV inválida")
            if item["cveID"] in cve_ids:
                raise ValueError("Catálogo CISA con CVE duplicadas")
            cve_ids.add(item["cveID"])
            ids.append(f'{item["cveID"]}|{str(item.get("dateAdded", ""))}')
        version = str(data.get("catalogVersion") or "").strip()
        if not version or len(version) > 100:
            raise ValueError("Versión CISA KEV inválida")
        signature = sha256((version + "|" + "|".join(sorted(ids))).encode()).hexdigest()
        return {"version": version, "fingerprint": signature, "record_count": len(entries)}

    html = raw.decode("utf-8", errors="replace")
    version = version_from_page(key, html)
    return {"version": version, "fingerprint": sha256(f"{key}:{version}".encode()).hexdigest(),
            "record_count": None}


def table_exists(db) -> bool:
    return db.execute(text("SELECT to_regclass(:table_name)"),
                      {"table_name": TABLE}).scalar_one() is not None


def read_snapshots(db) -> list[dict]:
    rows = {}
    if table_exists(db):
        result = db.execute(text(f"""SELECT source_key, baseline_version, observed_version,
                          last_checked_at, last_success_at, status,
                          needs_review, record_count, last_changed_at
                          FROM {TABLE}""")).mappings().all()
        rows = {row["source_key"]: dict(row) for row in result}
    sources = []
    for definition in SOURCE_DEFS:
        row = rows.get(definition["key"], {})
        sources.append({
            **definition,
            "baseline_version": row.get("baseline_version"),
            "observed_version": row.get("observed_version"),
            "last_checked_at": row.get("last_checked_at"),
            "last_success_at": row.get("last_success_at"),
            "status": row.get("status", "not_checked"),
            "needs_review": bool(row.get("needs_review")),
            "record_count": row.get("record_count"),
            "last_changed_at": row.get("last_changed_at"),
        })
    return sources


def references_for_controls(controls: list[dict]) -> list[dict]:
    result = []
    for control in controls:
        if control.get("id") not in CONTROL_REFERENCES:
            continue  # Esta vista se limita a los ocho controles originales.
        mapping = CONTROL_REFERENCES[control["id"]]
        techniques = [x.get("technique_id") for x in control.get("mitre_techniques", [])
                      if isinstance(x, dict) and re.fullmatch(
                          r"T\d{4}(?:\.\d{3})?", str(x.get("technique_id", "")))]
        result.append({
            "id": control.get("id"),
            "name": control.get("name"),
            "mode": control.get("mode"),
            "mitre": [{"id": technique, "url": "https://attack.mitre.org/techniques/" +
                       technique.replace(".", "/") + "/"} for technique in techniques],
            "nist": mapping["nist"],
            "cis": mapping["cis"],
            "mapping_status": "orientative_requires_review" if mapping["nist"] else "not_mapped",
        })
    return result


def check_official_sources(db, *, keys=None) -> dict:
    """Guarda solo versiones y hashes del contenido oficial; nunca cambia protecciones."""
    if not table_exists(db):
        raise RuntimeError("Falta migración 013_official_framework_checks.sql")
    requested = tuple(keys) if keys is not None else tuple(SOURCE_BY_KEY)
    if any(key not in SOURCE_BY_KEY for key in requested):
        raise ValueError("Fuente no autorizada")
    errors = []
    for key in requested:
        source = SOURCE_BY_KEY[key]
        checked_at = datetime.now(timezone.utc)
        try:
            found = read_official_source(key)
        except Exception as exc:
            # Mensaje deliberadamente acotado: no incluir HTML ni datos remotos.
            errors.append(key)
            db.execute(text(f"""
                INSERT INTO {TABLE} (source_key, name, official_url, status, last_checked_at)
                VALUES (:key, :name, :url, 'unavailable', :checked_at)
                ON CONFLICT (source_key) DO UPDATE SET
                  last_checked_at = EXCLUDED.last_checked_at,
                  status = 'unavailable'
            """), {"key": key, "name": source["name"], "url": source["url"],
                   "checked_at": checked_at})
            db.commit()
            continue
        db.execute(text(f"""
            INSERT INTO {TABLE}
              (source_key, name, official_url, baseline_version, observed_version,
               baseline_fingerprint, observed_fingerprint, status, needs_review,
               record_count, last_checked_at, last_success_at)
            VALUES
              (:key, :name, :url, :version, :version,
               :fingerprint, :fingerprint, 'verified', FALSE,
               :count, :checked_at, :checked_at)
            ON CONFLICT (source_key) DO UPDATE SET
              name = EXCLUDED.name, official_url = EXCLUDED.official_url,
              baseline_version = COALESCE({TABLE}.baseline_version,
                                          EXCLUDED.baseline_version),
              baseline_fingerprint = COALESCE({TABLE}.baseline_fingerprint,
                                               EXCLUDED.baseline_fingerprint),
              observed_version = EXCLUDED.observed_version,
              observed_fingerprint = EXCLUDED.observed_fingerprint,
              status = 'verified',
              needs_review = (COALESCE({TABLE}.baseline_fingerprint,
                                       EXCLUDED.baseline_fingerprint)
                              IS DISTINCT FROM EXCLUDED.observed_fingerprint),
              record_count = EXCLUDED.record_count,
              last_checked_at = EXCLUDED.last_checked_at,
              last_success_at = EXCLUDED.last_success_at,
              last_changed_at = CASE
                WHEN {TABLE}.observed_fingerprint IS DISTINCT FROM
                     EXCLUDED.observed_fingerprint THEN EXCLUDED.last_checked_at
                ELSE {TABLE}.last_changed_at END
        """), {"key": key, "name": source["name"], "url": source["url"],
               "version": found["version"], "fingerprint": found["fingerprint"],
               "count": found["record_count"], "checked_at": checked_at})
        db.commit()
    return {"failed_sources": errors, "sources": read_snapshots(db)}


def explain_official_changes_with_ai(db) -> dict:
    """IA opcional: únicamente metadatos PÚBLICOS ya obtenidos de fuentes fijas.

    No permite al modelo navegar arbitrariamente ni modificar configuraciones.
    Solo se invoca tras la acción explícita de un ingeniero/administrador.
    """
    import json
    import os

    snapshots = read_snapshots(db)
    verified = [source for source in snapshots if source["status"] == "verified"]
    if not verified:
        return {"mode": "unavailable", "summary": (
            "Primero consulta las fuentes oficiales. No hay versiones verificadas "
            "que una IA pueda analizar de forma responsable."
        )}
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return {"mode": "unavailable", "summary": (
            "IA opcional no configurada: OPENAI_API_KEY no está disponible. "
            "La vigilancia oficial por versiones funciona sin IA."
        )}

    public_data = {
        "sources": [{
            "name": item["name"], "official_url": item["url"],
            "reference_version": item["baseline_version"],
            "observed_version": item["observed_version"],
            "changed_since_reference": item["needs_review"],
        } for item in snapshots],
        "existing_mitre_techniques": [
            "T1110", "T1078", "T1565.001", "T1548.003",
            "T1041", "T1486", "T1021.004",
        ],
    }
    try:
        from openai import OpenAI
        result = OpenAI(api_key=key, timeout=18).responses.create(
            model=os.getenv("CYBERSHIELD_AI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "Eres analista defensivo documental. Recibirás exclusivamente "
                "metadatos públicos de cuatro fuentes oficiales ya consultadas. "
                "No dispones de navegacion web propia ni de detalles de servidores. "
                "No inventes cambios, nuevos ataques, CVEs, versiones o cumplimiento. "
                "Distingue cambios comprobados de actualizaciones no verificadas; "
                "si no hay cambios observados dilo expresamente. No afirmes que "
                "MITRE/NIST/CIS se aplica automáticamente ni que el servidor "
                "está vulnerable. En español, explica brevemente prioridades "
                "de investigación documental y pruebas humanas para las técnicas "
                "existentes. No incluyas comandos ni acciones ejecutables."
            ),
            input=json.dumps(public_data, ensure_ascii=False),
            max_output_tokens=420,
        )
        summary = (result.output_text or "").strip()
        if not summary:
            raise ValueError("Respuesta vacía")
        return {"mode": "public_metadata_ai", "summary": summary[:4000],
                "automatic_application": False}
    except Exception:
        return {"mode": "unavailable", "summary": (
            "El proveedor de IA no respondió. Conserva la comprobación "
            "documental y consulta manualmente las publicaciones oficiales."
        )}
