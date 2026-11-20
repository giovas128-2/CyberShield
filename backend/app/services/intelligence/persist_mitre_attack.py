"""
CyberShield Intelligence: persistencia MITRE ATT&CK.

--dry-run: valida sin modificar PostgreSQL.
--apply: guarda datos mediante una transacción.

No modifica reglas Wazuh ni ejecuta defensas.
"""

import argparse
from datetime import datetime
from sqlalchemy import inspect, text

from app.services.intelligence.import_cisa_kev import find_engine
from app.services.intelligence.import_mitre_attack import (
    fetch_bundle,
    prepare,
)
from app.services.intelligence.mitre_attack_reader import (
    URL,
    attack_id,
)

SOURCE = "MITRE ATT&CK Enterprise"


def get_rows():
    bundle = fetch_bundle()
    techniques, mitigations, relationships = prepare(bundle)

    version = str(bundle.get("id", "STIX 2.1"))[:100]

    technique_rows = []
    mitigation_rows = []
    relationship_rows = []

    for stix_id, obj in techniques.items():
        name = obj.get("name")
        code = attack_id(obj)

        if not isinstance(name, str) or len(name) > 250:
            raise ValueError("Nombre de técnica inválido")

        technique_rows.append({
            "stix_id": stix_id,
            "code": code,
            "name": name,
            "description": obj.get("description") or "",
            "subtechnique": bool(
                obj.get("x_mitre_is_subtechnique", False)
            ),
            "version": version,
            "modified": datetime.fromisoformat(
                obj["modified"].replace("Z", "+00:00")
            ) if obj.get("modified") else None,
        })

    for stix_id, obj in mitigations.items():
        name = obj.get("name")
        code = attack_id(obj)

        if not isinstance(name, str) or len(name) > 250:
            raise ValueError("Nombre de mitigación inválido")

        mitigation_rows.append({
            "stix_id": stix_id,
            "code": code,
            "name": name,
            "description": obj.get("description") or "",
            "version": version,
            "modified": datetime.fromisoformat(
                obj["modified"].replace("Z", "+00:00")
            ) if obj.get("modified") else None,
        })

    for stix_id, obj in relationships.items():
        relationship_rows.append({
            "stix_id": stix_id,
            "mitigation_stix": obj["source_ref"],
            "technique_stix": obj["target_ref"],
        })

    if len(technique_rows) != len(techniques):
        raise ValueError("Técnicas incompletas")

    if len(mitigation_rows) != len(mitigations):
        raise ValueError("Mitigaciones incompletas")

    if len(relationship_rows) != len(relationships):
        raise ValueError("Relaciones incompletas")

    if len({r["code"] for r in technique_rows}) != len(technique_rows):
        raise ValueError("Códigos de técnicas duplicados")

    if len({r["code"] for r in mitigation_rows}) != len(mitigation_rows):
        raise ValueError("Códigos de mitigaciones duplicados")

    for r in relationship_rows:
        if (
            r["mitigation_stix"] not in mitigations
            or r["technique_stix"] not in techniques
        ):
            raise ValueError("Relación con referencia inválida")

    return technique_rows, mitigation_rows, relationship_rows


def apply(engine, techniques, mitigations, relationships):
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "SET LOCAL statement_timeout = '180s'"
        )
        conn.exec_driver_sql(
            "SET LOCAL lock_timeout = '5s'"
        )

        conn.execute(text(
            "SELECT pg_advisory_xact_lock(20261119, 6006)"
        ))

        source_id = conn.execute(text("""
            INSERT INTO intelligence_sources
                (name, official_url, source_type, last_checked_at)
            VALUES (:name, :url, 'framework', NOW())
            ON CONFLICT (name) DO UPDATE SET
                official_url = EXCLUDED.official_url,
                last_checked_at = NOW()
            RETURNING id
        """), {
            "name": SOURCE,
            "url": URL,
        }).scalar_one()

        before = {}

        for table in (
            "intelligence_mitre_techniques",
            "intelligence_mitre_mitigations",
            "intelligence_mitre_relationships",
        ):
            before[table] = conn.execute(text(
                f"SELECT COUNT(*) FROM {table}"
            )).scalar_one()

        conn.execute(text("""
            INSERT INTO intelligence_mitre_techniques
                (source_id, stix_id, attack_id, name,
                 description, is_subtechnique,
                 source_version, modified_at)
            VALUES
                (:source_id, :stix_id, :code, :name,
                 :description, :subtechnique,
                 :version, :modified)
            ON CONFLICT (stix_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                is_subtechnique = EXCLUDED.is_subtechnique,
                source_version = EXCLUDED.source_version,
                modified_at = EXCLUDED.modified_at,
                updated_at = NOW()
        """), [
            {**r, "source_id": source_id}
            for r in techniques
        ])

        conn.execute(text("""
            INSERT INTO intelligence_mitre_mitigations
                (source_id, stix_id, mitigation_id, name,
                 description, source_version, modified_at)
            VALUES
                (:source_id, :stix_id, :code, :name,
                 :description, :version, :modified)
            ON CONFLICT (stix_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                source_version = EXCLUDED.source_version,
                modified_at = EXCLUDED.modified_at,
                updated_at = NOW()
        """), [
            {**r, "source_id": source_id}
            for r in mitigations
        ])

        conn.execute(text("""
            INSERT INTO intelligence_mitre_relationships
                (stix_id, technique_id, mitigation_id,
                 relationship_type)
            SELECT :stix_id, t.id, m.id, 'mitigates'
            FROM intelligence_mitre_techniques t
            JOIN intelligence_mitre_mitigations m
              ON m.stix_id = :mitigation_stix
            WHERE t.stix_id = :technique_stix
            ON CONFLICT (stix_id) DO UPDATE SET
                technique_id = EXCLUDED.technique_id,
                mitigation_id = EXCLUDED.mitigation_id
        """), relationships)

        after = {
            table: conn.execute(text(
                f"SELECT COUNT(*) FROM {table}"
            )).scalar_one()
            for table in before
        }

        expected = [
            len(techniques),
            len(mitigations),
            len(relationships),
        ]

        for table, minimum in zip(before, expected):
            if after[table] < minimum:
                raise RuntimeError(
                    f"Importación incompleta: {table}"
                )

        total_new = sum(
            after[table] - before[table]
            for table in before
        )

        conn.execute(text("""
            INSERT INTO intelligence_sync_history
                (source_id, started_at, finished_at,
                 status, records_created, records_updated)
            VALUES
                (:source_id, NOW(), NOW(), 'success',
                 :created, 0)
        """), {
            "source_id": source_id,
            "created": total_new,
        })

    return after, total_new


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=== CYBERSHIELD MITRE ATT&CK ===")

    techniques, mitigations, relationships = get_rows()

    print("Técnicas preparadas:", len(techniques))
    print("Mitigaciones preparadas:", len(mitigations))
    print("Relaciones preparadas:", len(relationships))

    engine = find_engine()

    required = [
        "intelligence_mitre_techniques",
        "intelligence_mitre_mitigations",
        "intelligence_mitre_relationships",
        "intelligence_sources",
        "intelligence_sync_history",
    ]

    inspector = inspect(engine)

    for table in required:
        if not inspector.has_table(table):
            raise RuntimeError(f"Falta la tabla: {table}")

    print("[APROBADO] Esquema disponible")

    if not args.apply:
        print("MODO: SIMULACIÓN")
        print("PostgreSQL modificado: NO")
        return

    after, created = apply(
        engine, techniques, mitigations, relationships
    )

    print("\n=== IMPORTACIÓN COMPLETADA ===")

    for table, count in after.items():
        print(table, ":", count)

    print("Registros adicionales:", created)
    print("Defensas ejecutadas: NINGUNA")


if __name__ == "__main__":
    main()
