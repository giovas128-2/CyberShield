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
    "possible_data_exfiltration": {
        "technique_id": "T1041",
        "technique_name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
        "reference_url": (
            "https://attack.mitre.org/techniques/T1041/"
        ),
        "notes": (
            "Asociación candidata de laboratorio para una "
            "posible exfiltración de datos. No confirma por "
            "sí sola una exfiltración real."
        ),
    },

    "possible_ransomware_behavior": {
        "technique_id": "T1486",
        "technique_name": "Data Encrypted for Impact",
        "tactic": "Impact",
        "reference_url": (
            "https://attack.mitre.org/techniques/T1486/"
        ),
        "notes": (
            "Asociación candidata de laboratorio para "
            "comportamiento compatible con impacto sobre "
            "archivos. CyberShield no ejecuta ransomware "
            "ni cifrado malicioso real."
        ),
    },

    "possible_lateral_movement": {
        "technique_id": "T1021.004",
        "technique_name": "SSH",
        "tactic": "Lateral Movement",
        "reference_url": (
            "https://attack.mitre.org/techniques/T1021/004/"
        ),
        "notes": (
            "Asociación candidata cuando existe SSH exitoso "
            "entre un par no autorizado o no habitual."
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
    mapping = None

    # Para ransomware-like conservamos primero la clasificación
    # MITRE REAL entregada por el sensor.
    #
    # Un cambio FIM no implica automáticamente cifrado,
    # por lo que NO debemos forzar T1486.
    if event_type == "possible_ransomware_behavior":
        mitre_ids = details.get("mitre_ids") or []
        mitre_tactics = details.get("mitre_tactics") or []
        mitre_techniques = details.get("mitre_techniques") or []

        if "T1565.001" in mitre_ids:
            mapping = {
                "technique_id": "T1565.001",
                "technique_name": (
                    mitre_techniques[0]
                    if mitre_techniques
                    else "Stored Data Manipulation"
                ),
                "tactic": (
                    mitre_tactics[0]
                    if mitre_tactics
                    else "Impact"
                ),
                "reference_url": (
                    "https://attack.mitre.org/"
                    "techniques/T1565/001/"
                ),
                "notes": (
                    "Wazuh FIM confirmó manipulación de datos "
                    "almacenados dentro del laboratorio "
                    "ransomware-demo. No se afirma cifrado real."
                ),
            }

        elif details.get(
            "encryption_behavior_confirmed",
            False,
        ):
            mapping = MITRE_MAPPING.get(
                "possible_ransomware_behavior"
            )

        else:
            return None

    # T1021.004 solo para SSH exitoso entre un par
    # no autorizado/no habitual.
    if event_type == "possible_lateral_movement":
        protocol = str(
            details.get("protocol", "")
        ).lower()

        login_successful = bool(
            details.get("login_successful", False)
        )

        pair_authorized = bool(
            details.get("pair_authorized", False)
        )

        if (
            protocol != "ssh"
            or not login_successful
            or pair_authorized
        ):
            return None
    if mapping is None:
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
