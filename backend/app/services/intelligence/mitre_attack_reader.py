"""
CyberShield Intelligence - MITRE ATT&CK Enterprise.

Descarga y valida información STIX 2.1.
No modifica PostgreSQL ni ejecuta defensas.
"""

import json
import re
import urllib.request
from collections import Counter

URL = (
    "https://raw.githubusercontent.com/"
    "mitre-attack/attack-stix-data/"
    "master/enterprise-attack/enterprise-attack.json"
)

MAX_BYTES = 100 * 1024 * 1024
ID_PATTERN = re.compile(r"^(T\d{4}(?:\.\d{3})?|M\d{4})$")


def attack_id(item):
    for ref in item.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            value = ref.get("external_id")
            if isinstance(value, str) and ID_PATTERN.fullmatch(value):
                return value
    return None


def main():
    print("=== CYBERSHIELD - MITRE ATT&CK ===")

    request = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "CyberShield-Academic/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        if not response.geturl().startswith(
            "https://raw.githubusercontent.com/"
        ):
            raise ValueError("Redirección no autorizada")

        content = response.read(MAX_BYTES + 1)

    if len(content) > MAX_BYTES:
        raise ValueError("Archivo mayor al límite permitido")

    data = json.loads(content.decode("utf-8"))

    if data.get("type") != "bundle":
        raise ValueError("No es un STIX Bundle")

    objects = data.get("objects")

    if not isinstance(objects, list) or not objects:
        raise ValueError("STIX sin objetos válidos")

    active = [
        obj for obj in objects
        if isinstance(obj, dict)
        and not obj.get("revoked", False)
        and not obj.get("x_mitre_deprecated", False)
    ]

    techniques = {
        attack_id(obj): obj
        for obj in active
        if obj.get("type") == "attack-pattern"
        and attack_id(obj)
        and attack_id(obj).startswith("T")
    }

    mitigations = {
        attack_id(obj): obj
        for obj in active
        if obj.get("type") == "course-of-action"
        and attack_id(obj)
        and attack_id(obj).startswith("M")
    }

    relationships = Counter(
        obj.get("relationship_type")
        for obj in active
        if obj.get("type") == "relationship"
    )

    print("Objetos STIX:", len(objects))
    print("Técnicas y subtécnicas:", len(techniques))
    print("Mitigaciones:", len(mitigations))
    print(
        "Relaciones mitigates:",
        relationships.get("mitigates", 0),
    )

    example = techniques.get("T1110")
    if example:
        print("\nEjemplo de técnica:")
        print("Código: T1110")
        print("Nombre:", example.get("name"))

    assert techniques, "No se encontraron técnicas"
    assert mitigations, "No se encontraron mitigaciones"

    print("\n[APROBADO] Catálogo STIX validado")
    print("PostgreSQL modificado: NO")
    print("Reglas defensivas activadas: NINGUNA")


if __name__ == "__main__":
    main()
