"""Actualización controlada de inteligencia CyberShield.

Ejecutar desde la raíz del repositorio:
    PYTHONPATH=backend backend/venv-wsl/bin/python -m app.services.intelligence.scheduled_sync --dry-run
    PYTHONPATH=backend backend/venv-wsl/bin/python -m app.services.intelligence.scheduled_sync --apply

No ejecuta, activa ni crea protecciones. Automatiza únicamente los catálogos
documentales de CISA KEV y MITRE ATT&CK, con validación previa.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

LOG = logging.getLogger("cybershield.intelligence.sync")


def prepare_environment() -> None:
    # systemd normalmente utiliza su propio EnvironmentFile. Para uso manual,
    # cargamos el .env local sin sobrescribir las variables del servicio.
    root = Path(__file__).resolve().parents[4]
    load_dotenv(root / "backend" / ".env", override=False)
    if not os.getenv("DATABASE_URL", "").strip():
        raise RuntimeError(
            "DATABASE_URL no está disponible para este proceso; "
            "no se intentó modificar PostgreSQL."
        )


def existing_count(engine, table: str) -> int:
    # Solo se permiten identificadores de tabla internos y fijos.
    allowed = {
        "intelligence_threats",
        "intelligence_mitre_techniques",
        "intelligence_mitre_mitigations",
        "intelligence_mitre_relationships",
    }
    if table not in allowed:
        raise ValueError("Tabla no autorizada")
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())


def validate_volume(label: str, new_count: int, previous_count: int) -> None:
    if new_count <= 0:
        raise RuntimeError(f"{label}: feed vacío")
    if previous_count >= 100:
        # La fuente puede cambiar, pero una variación brusca merece revisión
        # humana antes de modificar la base de conocimiento.
        minimum = max(1, int(previous_count * 0.80))
        maximum = max(previous_count + 1000, previous_count * 3)
        if not (minimum <= new_count <= maximum):
            raise RuntimeError(
                f"{label}: volumen anómalo ({new_count}); "
                f"referencia de PostgreSQL: {previous_count}. Sin aplicar."
            )


def run(*, apply: bool) -> int:
    prepare_environment()
    from app.database.connection import engine
    from app.services.intelligence.cisa_kev_sync import fetch_catalog
    from app.services.intelligence.import_cisa_kev import (
        import_records,
        prepare_records,
    )
    from app.services.intelligence.persist_mitre_attack import (
        apply as apply_mitre,
        get_rows,
    )

    failures = 0
    sources = [
        ("CISA KEV", "intelligence_threats"),
        ("MITRE ATT&CK", "intelligence_mitre_techniques"),
    ]
    for source, table in sources:
        LOG.info("Validando %s (modo=%s)", source, "apply" if apply else "dry-run")
        try:
            previous = existing_count(engine, table)
            if source == "CISA KEV":
                catalog = fetch_catalog()
                records, version = prepare_records(catalog)
                validate_volume(source, len(records), previous)
                LOG.info("%s: %s registros validados", source, len(records))
                if apply:
                    created, updated, unchanged = import_records(
                        engine, records, version
                    )
                    LOG.info(
                        "%s guardado: nuevos=%s modificados=%s sin_cambios=%s",
                        source, created, updated, unchanged,
                    )
            else:
                techniques, mitigations, relationships = get_rows()
                validate_volume(source, len(techniques), previous)
                validate_volume(
                    "MITRE mitigaciones", len(mitigations),
                    existing_count(engine, "intelligence_mitre_mitigations"),
                )
                validate_volume(
                    "MITRE relaciones", len(relationships),
                    existing_count(engine, "intelligence_mitre_relationships"),
                )
                LOG.info(
                    "MITRE validado: técnicas=%s mitigaciones=%s relaciones=%s",
                    len(techniques), len(mitigations), len(relationships),
                )
                if apply:
                    after, created = apply_mitre(
                        engine, techniques, mitigations, relationships
                    )
                    LOG.info("MITRE guardado: %s; nuevos=%s", after, created)
        except Exception:
            failures += 1
            LOG.exception("No se pudo actualizar %s", source)
    # Revisión de marcos y catálogos oficiales: se suma al temporizador diario
    # existente, solo cuando la migración opcional 013 está instalada.
    # No cambia configuraciones, reglas, respuestas ni catálogo de protecciones.
    if apply:
        try:
            from app.database.connection import SessionLocal
            from app.services.intelligence.official_frameworks import (
                table_exists, check_official_sources,
            )
            with SessionLocal() as session:
                if table_exists(session):
                    official = check_official_sources(session)
                    if official["failed_sources"]:
                        LOG.warning(
                            "Fuentes oficiales no disponibles: %s. Verificar en Protecciones.",
                            ", ".join(official["failed_sources"]),
                        )
                    else:
                        LOG.info("Fuentes oficiales MITRE/NIST/CIS/CISA verificadas")
                else:
                    LOG.info("Revisión de marcos pendiente: falta migración 013")
        except Exception:
            # No anular la sincronización CISA/MITRE previa por un error
            # del monitor documental opcional.
            LOG.exception("No se pudo completar la revisión oficial de marcos")

    LOG.info(
        "Finalizado: fuentes_fallidas=%s defensas_ejecutadas=0", failures
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    return run(apply=args.apply)


if __name__ == "__main__":
    sys.exit(main())
