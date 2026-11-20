"""Análisis defensivo de código fuente: reglas locales y explicación opcional con LLM.

No ejecuta el código, no usa shell, no clona repositorios y no crea incidentes.
Las coincidencias requieren revisión; no son CVE confirmados.
"""
import os
import re
from typing import Any

import httpx

MAX_FILES = 20
MAX_BYTES_PER_FILE = 60_000
MAX_TOTAL = 180_000
ALLOWED_EXTENSIONS = (".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".java", ".go", ".rb", ".yml", ".yaml", ".json", ".env.example", ".sql")
IGNORED_PARTS = {"node_modules", "vendor", "dist", "build", ".git", "venv", ".venv", "coverage", "tests", "__tests__"}
PATTERNS = (
    ("CS-CODE-01", "critical", "Posible ejecución de código dinámico",
     r"\beval\s*\(|\bexec\s*\(|\bnew\s+Function\s*\(", "CWE-95",
     "Evita evaluar cadenas externas; utiliza parsers y operaciones permitidas."),
    ("CS-CODE-02", "high", "Comando del sistema con shell habilitada",
     r"\bshell\s*=\s*True\b|\b(?:exec|system)\s*\(\s*\$_(?:GET|POST|REQUEST)", "CWE-78",
     "Evita ejecutar órdenes construidas con datos externos y usa APIs seguras."),
    ("CS-CODE-03", "high", "Posible consulta SQL por concatenación",
     r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b.{0,120}(?:\+|\$\{|\{\w+\}|\$_(?:GET|POST))", "CWE-89",
     "Usa consultas parametrizadas y valida los datos de entrada."),
    ("CS-CODE-04", "medium", "Verificación TLS deshabilitada",
     r"verify\s*=\s*False\b|rejectUnauthorized\s*:\s*false", "CWE-295",
     "Mantén la validación de certificados TLS habilitada."),
    ("CS-CODE-05", "high", "Modo de depuración habilitado",
     r"\bDEBUG\s*=\s*True\b|\bdebug\s*=\s*True\b|app\.run\(.{0,100}debug\s*=\s*True", "CWE-489",
     "Desactiva la depuración en despliegues y evita filtrar información sensible."),
    ("CS-CODE-06", "high", "Posible secreto incrustado",
     r"\b(?:password|secret_key|api_key|access_token)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "CWE-798",
     "Usa un gestor de secretos o variables de entorno; rota las credenciales expuestas."),
)

def is_allowed(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    if any(x.lower() in IGNORED_PARTS for x in parts):
        return False
    if path.startswith("/") or ".." in parts:
        return False
    return path.lower().endswith(ALLOWED_EXTENSIONS)

def scan_sources(files: list[dict[str, str]]) -> dict[str, Any]:
    if not files or len(files) > MAX_FILES:
        raise ValueError("Se requieren entre 1 y 20 archivos de código")
    total = 0
    findings: list[dict[str, Any]] = []
    inspected: list[str] = []
    for item in files:
        path, content = item.get("path"), item.get("content")
        if not isinstance(path, str) or not isinstance(content, str) or not is_allowed(path):
            raise ValueError("Ruta o archivo no permitido")
        size = len(content.encode("utf-8"))
        total += size
        if size > MAX_BYTES_PER_FILE or total > MAX_TOTAL:
            raise ValueError("Archivos demasiado grandes para una revisión segura")
        inspected.append(path)
        for number, line in enumerate(content.splitlines(), 1):
            if len(line) > 3000:
                continue
            for rule_id, severity, title, pattern, cwe, recommendation in PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "id": f"{path}:{number}:{rule_id}",
                        "file": path, "line": number,
                        "rule": rule_id, "severity": severity,
                        "title": title, "cwe": cwe,
                        "recommendation": recommendation,
                        "evidence": "Coincidencia de patrón; revisar el contexto y los datos de entrada",
                        "verification": "unverified",
                    })
                    if len(findings) >= 100:
                        break
            if len(findings) >= 100:
                break
    return {
        "source": "static_rules",
        "files_scanned": len(inspected), "files": inspected,
        "findings": findings, "findings_total": len(findings),
        "execution": "none", "incidents_created": 0,
        "note": "Resultados preliminares: las coincidencias no demuestran explotación.",
    }

def github_public_files(owner: str, repo: str, branch: str = "") -> list[dict[str, str]]:
    """Lectura acotada de repos públicos; no se admiten URLs arbitrarias ni tokens."""
    slug = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
    if not slug.fullmatch(owner) or not slug.fullmatch(repo) or (branch and not re.fullmatch(r"[A-Za-z0-9_./-]{1,100}", branch)):
        raise ValueError("Repositorio o rama inválidos")
    base = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CyberShield-CodeReview"}
    with httpx.Client(timeout=12, follow_redirects=False, headers=headers) as client:
        if not branch:
            info = client.get(base)
            info.raise_for_status()
            metadata = info.json()
            if metadata.get("private") is not False:
                raise ValueError("Solo se aceptan repositorios públicos")
            branch = metadata["default_branch"]
        tree = client.get(f"{base}/git/trees/{branch}", params={"recursive": "1"})
        tree.raise_for_status()
        data = tree.json()
        if data.get("truncated"):
            raise ValueError("Repositorio demasiado grande para una revisión completa")
        entries = [x for x in data.get("tree", []) if x.get("type") == "blob" and is_allowed(x.get("path", "")) and x.get("size", MAX_BYTES_PER_FILE+1) <= MAX_BYTES_PER_FILE]
        if len(entries) > MAX_FILES:
            raise ValueError(f"Repositorio con demasiados archivos elegibles ({len(entries)}); máximo {MAX_FILES}")
        files = []
        for entry in entries:
            blob = client.get(entry["url"])
            blob.raise_for_status()
            value = blob.json()
            if value.get("encoding") != "base64":
                continue
            import base64
            raw = base64.b64decode(value["content"])
            try:
                source = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            files.append({"path": entry["path"], "content": source})
        return files

def explain_with_llm(scan: dict[str, Any], enabled: bool) -> dict[str, Any]:
    """Solo envía metadatos, hallazgos y recomendaciones al proveedor IA, nunca el código."""
    if not enabled:
        return {"mode": "rules_only", "summary": "Análisis estático mediante reglas. IA generativa no configurada."}
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"mode": "rules_only", "summary": "IA no configurada: falta OPENAI_API_KEY."}
    try:
        from openai import OpenAI
        import json
        safe = [{"file": f["file"], "line": f["line"], "cwe": f["cwe"], "title": f["title"], "recommendation": f["recommendation"]} for f in scan["findings"][:25]]
        result = OpenAI(api_key=key, timeout=12).responses.create(
            model=os.getenv("CYBERSHIELD_AI_MODEL", "gpt-4.1-mini"),
            instructions="Eres un analista defensivo. Explica en español los hallazgos tentativos. No declares vulnerabilidades confirmadas ni ejecución de ataques. No inventes evidencia. Responde con un párrafo breve y recomendaciones priorizadas.",
            input=json.dumps({"files_scanned": scan["files_scanned"], "findings": safe}, ensure_ascii=False),
            max_output_tokens=450,
        )
        return {"mode": "llm_explanation", "summary": result.output_text}
    except Exception:
        return {"mode": "rules_only", "summary": "Análisis por reglas disponible. No se pudo contactar con el proveedor de IA."}
