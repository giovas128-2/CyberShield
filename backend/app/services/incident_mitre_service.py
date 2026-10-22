from sqlalchemy.orm import Session

from app.models.incident_mitre import IncidentMitre


MITRE_MAPPING = {
    "multiple_login_attempts": {
        "technique_id": "T1110",
        "technique_name": "Brute Force",
        "tactic": "Credential Access",
        "reference_url": "https://attack.mitre.org/techniques/T1110/",
        "notes": (
            "Clasificación MITRE asociada a múltiples "
            "intentos de autenticación."
        ),
    },
    "authentication_failure": {
        "technique_id": "T1110",
        "technique_name": "Brute Force",
        "tactic": "Credential Access",
        "reference_url": "https://attack.mitre.org/techniques/T1110/",
        "notes": (
            "Clasificación MITRE asociada a fallos "
            "repetidos de autenticación."
        ),
    },
    "authentication_burst": {
        "technique_id": "T1110",
        "technique_name": "Brute Force",
        "tactic": "Credential Access",
        "reference_url": "https://attack.mitre.org/techniques/T1110/",
        "notes": (
            "Clasificación MITRE asociada a ráfaga "
            "de intentos de autenticación."
        ),
    },
    "privilege_escalation": {
        "technique_id": "T1548.003",
        "technique_name": "Sudo and Sudo Caching",
        "tactic": "Privilege Escalation",
        "reference_url": (
            "https://attack.mitre.org/"
            "techniques/T1548/003/"
        ),
        "notes": (
            "Clasificación MITRE aplicada cuando "
            "la evidencia confirma uso de sudo."
        ),
    },
    "suspicious_file_change": {
        "technique_id": "T1565.001",
        "technique_name": "Stored Data Manipulation",
        "tactic": "Impact",
        "reference_url": "https://attack.mitre.org/techniques/T1565/001/",
        "notes": (
            "Clasificación MITRE asociada a una modificación "
            "de archivo detectada por Wazuh FIM. En el laboratorio "
            "OLA1 se confirmó sobre un archivo señuelo monitoreado."
        ),
    },
}


def create_automatic_incident_mitre(
    db: Session,
    incident_id: int,
    event_type: str,
    details: dict | None = None,
):
    details = details or {}
    if event_type == "privilege_escalation":
        sudo_used = bool(
            details.get(
                "sudo_used",
                details.get("sudo", False),
            )
        )

        if not sudo_used:
            return None
    mapping = MITRE_MAPPING.get(event_type)

    if not mapping:
        return None

    existing = (
        db.query(IncidentMitre)
        .filter(
            IncidentMitre.incident_id == incident_id,
            IncidentMitre.technique_id
            == mapping["technique_id"],
        )
        .first()
    )

    if existing:
        return existing

    mitre = IncidentMitre(
        incident_id=incident_id,
        technique_id=mapping["technique_id"],
        technique_name=mapping["technique_name"],
        tactic=mapping["tactic"],
        reference_url=mapping["reference_url"],
        is_primary=True,
        notes=mapping["notes"],
    )

    db.add(mitre)
    db.commit()
    db.refresh(mitre)

    return mitre
