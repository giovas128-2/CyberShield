"""
CyberShield Intelligence - Importador CISA KEV.

Modo predeterminado: --dry-run
Importación permanente: --apply

No crea reglas Wazuh ni ejecuta defensas.
"""

import argparse
import ast
import importlib
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.services.intelligence.cisa_kev_sync import (
    SOURCE_URL,
    fetch_catalog,
    validate_catalog,
)

SOURCE_NAME = "CISA KEV"
ROOT = Path("backend/app")


def find_engine():
    candidates = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        if path.name == "import_cisa_kev.py":
            continue

        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8")
            )
        except (SyntaxError, OSError):
            continue

        creates_engine = any(
            isinstance(node, ast.Call)
            and (
                getattr(node.func, "id", None)
                == "create_engine"
                or getattr(node.func, "attr", None)
                == "create_engine"
            )
            for node in ast.walk(tree)
        )

        if creates_engine:
            module_name = ".".join(
                ("app",)
                + path.relative_to(ROOT).with_suffix("").parts
            )
            candidates.append(module_name)

    engines = []

    for name in sorted(set(candidates)):
        try:
            module = importlib.import_module(name)
        except Exception:
            continue

        for value in vars(module).values():
            if isinstance(value, Engine):
                engines.append(value)

    engines = list({id(e): e for e in engines}.values())

    if len(engines) != 1:
        raise RuntimeError(
            "No se encontró un motor único de PostgreSQL"
        )

    engine = engines[0]

    if engine.dialect.name != "postgresql":
        raise RuntimeError("Se requiere PostgreSQL")

    return engine


def prepare_records(catalog):
    validated = validate_catalog(catalog)

    if validated["invalid"]:
        raise ValueError(
            "El catálogo contiene registros inválidos"
        )

    if len(validated["valid"]) != len(
        catalog["vulnerabilities"]
    ):
        raise ValueError("La validación no fue completa")

    records = []

    for item in catalog["vulnerabilities"]:
        cve = item["cveID"].strip()
        name = item["vulnerabilityName"].strip()

        description = (
            item.get("shortDescription") or ""
        ).strip()

        required_action = (
            item.get("requiredAction") or ""
        ).strip()

        if len(name) > 250:
            raise ValueError(
                f"Nombre demasiado largo: {cve}"
            )

        combined_description = (
            f"{description}\n\n"
            f"Acción recomendada por CISA: "
            f"{required_action}"
        )

        records.append({
            "external_id": cve,
            "name": name,
            "description": combined_description,
            "category": "CVE",
            "reference_url": SOURCE_URL,
            "source_version": str(
                validated["version"]
            )[:100],
        })

    return records, validated["version"]


def import_records(engine, records, version):
    created = 0
    updated = 0
    unchanged = 0

    # Una sola transacción: éxito completo o rollback.
    with engine.begin() as conn:
        conn.execute(text(
            "SET LOCAL lock_timeout = '5s'"
        ))
        conn.execute(text(
            "SET LOCAL statement_timeout = '60s'"
        ))

        # Evita dos importaciones simultáneas
        # realizadas por este mismo importador.
        conn.execute(text(
            "SELECT pg_advisory_xact_lock(20261119, 5005)"
        ))

        source_id = conn.execute(
            text("""
                INSERT INTO intelligence_sources (
                    name,
                    official_url,
                    source_type,
                    last_checked_at
                )
                VALUES (
                    :name, :url, 'vulnerability', NOW()
                )
                ON CONFLICT (name)
                DO UPDATE SET
                    official_url = EXCLUDED.official_url,
                    source_type = EXCLUDED.source_type,
                    last_checked_at = NOW()
                RETURNING id
            """),
            {
                "name": SOURCE_NAME,
                "url": SOURCE_URL,
            },
        ).scalar_one()

        existing_rows = conn.execute(
            text("""
                SELECT external_id, name,
                       description, source_version
                FROM intelligence_threats
                WHERE source_id = :source_id
            """),
            {"source_id": source_id},
        ).mappings().all()

        existing = {
            row["external_id"]: dict(row)
            for row in existing_rows
        }

        for record in records:
            previous = existing.get(
                record["external_id"]
            )

            params = {
                **record,
                "source_id": source_id,
            }

            if previous is None:
                conn.execute(
                    text("""
                        INSERT INTO intelligence_threats (
                            source_id, external_id,
                            name, description, category,
                            reference_url, source_version,
                            reviewed_at
                        )
                        VALUES (
                            :source_id, :external_id,
                            :name, :description, :category,
                            :reference_url, :source_version,
                            NOW()
                        )
                        ON CONFLICT (source_id, external_id)
                        DO NOTHING
                    """),
                    params,
                )
                created += 1

            elif any(
                previous[field] != record[field]
                for field in (
                    "name",
                    "description",
                    "source_version",
                )
            ):
                conn.execute(
                    text("""
                        UPDATE intelligence_threats
                        SET name = :name,
                            description = :description,
                            category = :category,
                            reference_url = :reference_url,
                            source_version = :source_version,
                            reviewed_at = NOW(),
                            updated_at = NOW()
                        WHERE source_id = :source_id
                          AND external_id = :external_id
                    """),
                    params,
                )
                updated += 1

            else:
                unchanged += 1

        conn.execute(
            text("""
                INSERT INTO intelligence_sync_history (
                    source_id, started_at,
                    finished_at, status,
                    records_created, records_updated
                )
                VALUES (
                    :source_id, NOW(),
                    NOW(), 'success',
                    :created, :updated
                )
            """),
            {
                "source_id": source_id,
                "created": created,
                "updated": updated,
            },
        )

    return created, updated, unchanged


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
    )
    args = parser.parse_args()

    print("=== CYBERSHIELD INTELLIGENCE ===")
    print("Fuente:", SOURCE_NAME)

    catalog = fetch_catalog()
    records, version = prepare_records(catalog)

    print("Versión:", version)
    print("CVE validados:", len(records))

    engine = find_engine()

    required_tables = (
        "intelligence_sources",
        "intelligence_threats",
        "intelligence_sync_history",
    )

    with engine.connect() as conn:
        for table in required_tables:
            exists = conn.execute(
                text("SELECT to_regclass(:name)"),
                {"name": table},
            ).scalar()

            if exists is None:
                raise RuntimeError(
                    f"Falta la tabla {table}"
                )

    print("[APROBADO] Tablas localizadas")

    if not args.apply:
        print("\nMODO: SIMULACIÓN")
        print("Registros preparados:", len(records))
        print("Cambios en PostgreSQL: NINGUNO")
        return

    print("\nMODO: IMPORTACIÓN REAL")

    created, updated, unchanged = import_records(
        engine, records, version
    )

    print("Registros nuevos:", created)
    print("Registros actualizados:", updated)
    print("Registros sin cambios:", unchanged)
    print("Importación confirmada en PostgreSQL")
    print("Defensas activadas: NINGUNA")


if __name__ == "__main__":
    main()
