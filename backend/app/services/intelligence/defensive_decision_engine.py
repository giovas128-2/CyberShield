"""CyberShield 2.0 - decisión defensiva de solo lectura (fase 2).

Este módulo NO modifica servidores, no crea acciones y no ejecuta comandos.
Las recomendaciones MITRE nunca son comandos ejecutables. El catálogo necesita
un playbook implementado y validado antes de autorizar la ejecución.

Escenario inicial: fuerza bruta SSH, MITRE T1110, Wazuh regla 5763.
"""
from dataclasses import asdict, dataclass
from ipaddress import ip_address
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

TECHNIQUE = "T1110"
CONTROL_ID = "c1"
RESPONSE = "BLOCK_SOURCE_IP"


@dataclass(frozen=True)
class Decision:
    status: str
    technique_id: str
    control_id: str
    recommended_action: str | None
    target: str | None
    reason: str
    execution_allowed: bool = False
    executed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def assess_ssh_bruteforce(
    event: Mapping[str, Any],
    *,
    technique_exists: bool,
    control: Mapping[str, Any] | None,
) -> Decision:
    """Clasifica un evento sin efectos secundarios; falla de forma segura."""
    base = {
        "technique_id": TECHNIQUE,
        "control_id": CONTROL_ID,
        "recommended_action": None,
        "target": None,
        "execution_allowed": False,
        "executed": False,
    }

    if event.get("event_type") not in {
        "authentication_burst",
        "authentication_failure",
        "multiple_login_attempts",
    }:
        return Decision(
            status="not_applicable",
            reason="El evento no pertenece a la familia de autenticación SSH.",
            **base,
        )

    details = event.get("details")
    if not isinstance(details, dict):
        details = {}

    if (
        event.get("severity") not in {"high", "critical"}
        or event.get("source") != "wazuh"
        or details.get("sensor_confirmed_bruteforce") is not True
        or str(details.get("wazuh_rule_id")) != "5763"
    ):
        return Decision(
            status="needs_investigation",
            reason="Falta evidencia corroborada de Wazuh regla 5763.",
            **base,
        )

    if (
        details.get("allowlisted") is True
        or details.get("admin_protected") is True
    ):
        return Decision(
            status="excluded",
            reason="Origen excluido por lista de confianza o protección administrativa.",
            **base,
        )

    source_ip = event.get("source_ip")
    try:
        address = ip_address(source_ip)
        if (
            address.is_unspecified or address.is_multicast
            or address.is_loopback or address.is_link_local
        ):
            raise ValueError("Origen reservado")
    except (TypeError, ValueError):
        return Decision(
            status="needs_investigation",
            reason="No se proporcionó una IP de origen válida para bloqueo.",
            **base,
        )

    if not technique_exists:
        return Decision(
            status="knowledge_missing",
            reason="T1110 no existe en la base de conocimiento MITRE.",
            **base,
        )

    if control is None or control.get("mode") != "integrated":
        return Decision(
            status="control_unavailable",
            reason="No existe un control integrado para T1110.",
            **base,
        )

    # IMPORTANTE: el catálogo 007 contiene indicadores de validación, pero NO
    # representa por sí solo un playbook de ejecución revisado. Incluso si
    # alguien modifica esos indicadores, este módulo solo puede recomendar.
    return Decision(
        status="recommendation_only",
        technique_id=TECHNIQUE,
        control_id=CONTROL_ID,
        recommended_action=RESPONSE,
        target=str(address),
        reason=(
            "Wazuh confirmó T1110 y existe un control integrado. "
            "Se propone bloqueo temporal; falta conectar y verificar "
            "el ejecutor autorizado antes de habilitar automatización."
        ),
        execution_allowed=False,
        executed=False,
    )


def assess_from_database(db: Session, event: Mapping[str, Any]) -> Decision:
    """Obtiene el catálogo MITRE y la protección actual; SOLO SELECT."""
    technique_exists = bool(db.execute(text("""
        SELECT EXISTS(
            SELECT 1 FROM intelligence_mitre_techniques
            WHERE attack_id = :attack_id
        )
    """), {"attack_id": TECHNIQUE}).scalar_one())

    row = db.execute(text("""
        SELECT mode, execution_enabled, execution_verified
        FROM cybershield_protection_catalog
        WHERE control_id = :control_id
          AND origin = 'builtin'
          AND mitre_techniques @> CAST(:technique AS jsonb)
        LIMIT 1
    """), {
        "control_id": CONTROL_ID,
        "technique": '[{"technique_id":"T1110"}]',
    }).mappings().first()
    return assess_ssh_bruteforce(
        event,
        technique_exists=technique_exists,
        control=dict(row) if row else None,
    )
