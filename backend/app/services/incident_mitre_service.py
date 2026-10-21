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
}


def create_automatic_incident_mitre(
    db: Session,
    incident_id: int,
    event_type: str,
):
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
