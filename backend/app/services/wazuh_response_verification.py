"""
CyberShield - Adaptador de resultados Wazuh.

Este módulo interpreta resultados de ejecución.
No ejecuta defensas ni modifica servidores.
"""

from app.services.containment_verification_service import (
    ContainmentEvidence,
    ContainmentResult,
    verify_containment,
)


def evaluate_wazuh_execution(
    operation: str,
    success: bool,
) -> ContainmentResult:
    """
    Convierte un resultado de ejecución Wazuh
    en una evaluación de CyberShield.

    Solo procesa operaciones add.
    Las operaciones delete corresponden a reversión.
    """

    if operation != "add":
        raise ValueError(
            "Esta operación no corresponde "
            "a una ejecución defensiva."
        )

    if type(success) is not bool:
        raise ValueError(
            "El resultado de ejecución "
            "debe ser booleano."
        )

    evidence = ContainmentEvidence(
        execution_success=success,
        enforcement_confirmed=False,
        mitigation_effective=False,
        observation_complete=False,
    )

    return verify_containment(evidence)
