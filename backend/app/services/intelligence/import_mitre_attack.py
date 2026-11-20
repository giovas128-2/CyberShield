"""
CyberShield Intelligence - Preparación de datos MITRE.

Valida técnicas, mitigaciones y relaciones STIX.
No escribe en PostgreSQL ni ejecuta defensas.
"""

import json
import ssl
import urllib.request
from urllib.parse import urlparse

from app.services.intelligence.mitre_attack_reader import (
    URL,
    attack_id,
)

MAX_BYTES = 100 * 1024 * 1024


def fetch_bundle():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "CyberShield-Academic/1.0"},
    )

    with urllib.request.urlopen(
        request,
        timeout=90,
        context=ssl.create_default_context(),
    ) as response:
        final_url = urlparse(response.geturl())

        if (
            final_url.scheme != "https"
            or final_url.hostname != "raw.githubusercontent.com"
        ):
            raise ValueError("Origen MITRE no autorizado")

        content = response.read(MAX_BYTES + 1)

    if len(content) > MAX_BYTES:
        raise ValueError("Archivo demasiado grande")

    bundle = json.loads(content.decode("utf-8"))

    if bundle.get("type") != "bundle":
        raise ValueError("Formato STIX inválido")

    return bundle


def prepare(bundle):
    objects = bundle.get("objects")

    if not isinstance(objects, list):
        raise ValueError("Lista STIX inválida")

    active = [
        obj for obj in objects
        if isinstance(obj, dict)
        and not obj.get("revoked", False)
        and not obj.get("x_mitre_deprecated", False)
    ]

    techniques = {}
    mitigations = {}

    for obj in active:
        kind = obj.get("type")
        code = attack_id(obj)
        stix_id = obj.get("id")

        if not code or not stix_id:
            continue

        if kind == "attack-pattern" and code.startswith("T"):
            techniques[stix_id] = obj

        elif kind == "course-of-action" and code.startswith("M"):
            mitigations[stix_id] = obj

    relations = {}
    pairs = set()

    for obj in active:
        if (
            obj.get("type") != "relationship"
            or obj.get("relationship_type") != "mitigates"
        ):
            continue

        source = obj.get("source_ref")
        target = obj.get("target_ref")
        stix_id = obj.get("id")

        if source not in mitigations or target not in techniques:
            continue

        pair = (source, target)

        if pair in pairs or not stix_id:
            continue

        pairs.add(pair)
        relations[stix_id] = obj

    if not techniques or not mitigations or not relations:
        raise ValueError("Datos MITRE incompletos")

    return techniques, mitigations, relations


def main():
    print("=== CYBERSHIELD MITRE ATT&CK ===")

    bundle = fetch_bundle()
    techniques, mitigations, relations = prepare(bundle)

    print("Técnicas válidas:", len(techniques))
    print("Mitigaciones válidas:", len(mitigations))
    print("Relaciones válidas:", len(relations))

    for obj in techniques.values():
        if attack_id(obj) == "T1110":
            print("T1110:", obj.get("name"))
            break

    print("\n[APROBADO] Validación previa")
    print("Modo: SIMULACIÓN")
    print("PostgreSQL modificado: NO")
    print("Defensas ejecutadas: NINGUNA")


if __name__ == "__main__":
    main()
