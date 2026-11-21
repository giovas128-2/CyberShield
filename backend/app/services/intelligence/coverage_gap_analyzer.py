"""CyberShield 2.0: inventario de brechas MITRE, SOLO LECTURA.

Una asociación en el catálogo no implica detección validada ni capacidad
de ejecución. No genera, habilita ni ejecuta protecciones.
"""
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class CoverageReport:
    total_techniques: int
    catalog_controls: int
    referenced_techniques: int
    referenced_in_mitre: int
    unknown_references: tuple[str, ...]
    uncovered_techniques: int
    integrated_associations: int
    execution_verified_associations: int
    uncovered_preview: tuple[tuple[str, str], ...]


def build_coverage_report(
    techniques: Sequence[Mapping[str, Any]],
    controls: Sequence[Mapping[str, Any]],
    *,
    preview_limit: int = 15,
) -> CoverageReport:
    """Clasifica asociaciones exactas de technique_id, no de nombres.

    En el catálogo puede haber múltiples controles por una misma técnica.
    execution_verified del control no prueba capacidad autónoma; es solo
    una propiedad declarada que debe auditarse por separado.
    """
    if not isinstance(preview_limit, int) or isinstance(preview_limit, bool) or preview_limit < 0:
        raise ValueError("preview_limit inválido")
    known = {}
    for item in techniques:
        attack_id = item.get("attack_id")
        if isinstance(attack_id, str) and attack_id.strip():
            known[attack_id.strip()] = str(item.get("name") or "")

    referenced = set()
    integrated = set()
    verified = set()
    for control in controls:
        entries = control.get("mitre_techniques")
        if not isinstance(entries, list):
            continue
        ids = {
            value.get("technique_id").strip()
            for value in entries
            if isinstance(value, dict)
            and isinstance(value.get("technique_id"), str)
            and value.get("technique_id").strip()
        }
        referenced.update(ids)
        if control.get("mode") == "integrated":
            integrated.update(ids)
        if control.get("execution_verified") is True:
            verified.update(ids)

    known_ids = set(known)
    uncovered = sorted(
        known_ids - referenced, key=lambda code: (code, known[code])
    )
    return CoverageReport(
        total_techniques=len(known_ids),
        catalog_controls=len(controls),
        referenced_techniques=len(referenced),
        referenced_in_mitre=len(referenced & known_ids),
        unknown_references=tuple(sorted(referenced - known_ids)),
        uncovered_techniques=len(uncovered),
        integrated_associations=len(integrated & known_ids),
        execution_verified_associations=len(verified & known_ids),
        uncovered_preview=tuple((code, known[code]) for code in uncovered[:preview_limit]),
    )


def coverage_report_from_database(db: Session, *, preview_limit: int = 15) -> CoverageReport:
    """Solo SELECT. No consulta ni cambia los eventos de seguridad."""
    techniques = db.execute(text("""
        SELECT attack_id, name
        FROM intelligence_mitre_techniques
        WHERE attack_id IS NOT NULL
        ORDER BY attack_id
    """)).mappings().all()
    controls = db.execute(text("""
        SELECT control_id, mode, execution_verified, mitre_techniques
        FROM cybershield_protection_catalog
        ORDER BY sort_order, control_id
    """)).mappings().all()
    return build_coverage_report(
        techniques, controls, preview_limit=preview_limit
    )
