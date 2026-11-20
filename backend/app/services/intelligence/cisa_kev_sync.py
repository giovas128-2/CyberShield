"""
CyberShield Intelligence - CISA KEV.

Consulta el catálogo oficial y valida sus registros.
Modo de prueba: no escribe en PostgreSQL ni
activa defensas.
"""

import json
import re
import ssl
import urllib.request
from datetime import datetime
from urllib.parse import urlparse

SOURCE_URL = (
    "https://www.cisa.gov/sites/default/files/"
    "feeds/known_exploited_vulnerabilities.json"
)

CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$")
MAX_BYTES = 20 * 1024 * 1024


def fetch_catalog():
    parsed = urlparse(SOURCE_URL)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.cisa.gov"
    ):
        raise ValueError("Fuente no autorizada")

    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "CyberShield-Academic/1.0",
            "Accept": "application/json",
        },
    )

    context = ssl.create_default_context()

    with urllib.request.urlopen(
        request,
        timeout=20,
        context=context,
    ) as response:

        final_url = urlparse(response.geturl())

        if (
            final_url.scheme != "https"
            or final_url.hostname != "www.cisa.gov"
        ):
            raise ValueError(
                "Redirección fuera de la fuente autorizada"
            )

        content = response.read(MAX_BYTES + 1)

    if len(content) > MAX_BYTES:
        raise ValueError("Catálogo demasiado grande")

    return json.loads(content.decode("utf-8"))


def validate_catalog(data):
    if not isinstance(data, dict):
        raise ValueError("Formato de catálogo incorrecto")

    records = data.get("vulnerabilities")

    if not isinstance(records, list) or not records:
        raise ValueError("Catálogo vacío o inválido")

    valid = []
    invalid = 0
    seen = set()

    for item in records:
        if not isinstance(item, dict):
            invalid += 1
            continue

        cve = item.get("cveID")
        name = item.get("vulnerabilityName")
        action = item.get("requiredAction")

        if (
            not isinstance(cve, str)
            or not CVE_PATTERN.fullmatch(cve)
            or not isinstance(name, str)
            or not name.strip()
            or not isinstance(action, str)
            or not action.strip()
            or cve in seen
        ):
            invalid += 1
            continue

        seen.add(cve)
        valid.append({
            "cve": cve,
            "name": name,
            "required_action": action,
        })

    return {
        "version": data.get("catalogVersion", "desconocida"),
        "valid": valid,
        "invalid": invalid,
    }


def main():
    print("=== CYBERSHIELD INTELLIGENCE ===")
    print("Fuente: CISA KEV")
    print("Fecha de consulta:", datetime.now().isoformat())

    catalog = fetch_catalog()
    result = validate_catalog(catalog)

    print("Versión:", result["version"])
    print("Registros válidos:", len(result["valid"]))
    print("Registros rechazados:", result["invalid"])

    if result["invalid"]:
        print("[REVISAR] Hay registros no válidos")
    else:
        print("[APROBADO] Estructura validada")

    print("\nEjemplos del catálogo:")
    for item in result["valid"][:5]:
        print("-", item["cve"], item["name"][:100])

    print("\nPostgreSQL modificado: NO")
    print("Acciones defensivas activadas: NINGUNA")


if __name__ == "__main__":
    main()
