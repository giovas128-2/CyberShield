"""
CyberShield - Verificación de contención defensiva.

No ejecuta comandos ni modifica servidores.
Evalúa evidencias aportadas por componentes confiables.

IMPORTANTE:
La ausencia de nuevos ataques NO demuestra,
por sí sola, que una amenaza fue contenida.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ContainmentEvidence:
    execution_success: Optional[bool] = None
    enforcement_confirmed: bool = False
    mitigation_effective: bool = False
    observation_complete: bool = False
    verification_expired: bool = False


@dataclass(frozen=True)
class ContainmentResult:
    status: str
    notify_engineer: bool
    reason: str


def verify_containment(
    evidence: ContainmentEvidence,
) -> ContainmentResult:

    if evidence.execution_success is False:
        return ContainmentResult(
            status="failed",
            notify_engineer=True,
            reason="El ejecutor reportó un fallo defensivo.",
        )

    if evidence.execution_success is None:
        return ContainmentResult(
            status="unverified",
            notify_engineer=evidence.verification_expired,
            reason=(
                "No existe confirmación confiable "
                "de ejecución."
            ),
        )

    if (
        evidence.enforcement_confirmed
        and evidence.mitigation_effective
        and evidence.observation_complete
    ):
        return ContainmentResult(
            status="contained",
            notify_engineer=False,
            reason=(
                "La ejecución, la aplicación de la "
                "medida y su eficacia fueron verificadas."
            ),
        )

    if evidence.verification_expired:
        return ContainmentResult(
            status="unverified",
            notify_engineer=True,
            reason=(
                "El plazo de verificación terminó "
                "sin evidencia suficiente de contención."
            ),
        )

    return ContainmentResult(
        status="executed",
        notify_engineer=False,
        reason=(
            "La ejecución fue reportada como exitosa, "
            "pero la contención aún no está demostrada."
        ),
    )
