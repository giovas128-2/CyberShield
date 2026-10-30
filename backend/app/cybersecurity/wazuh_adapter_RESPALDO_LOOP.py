from pathlib import Path


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_wazuh_event(
    raw_event: dict,
    server_id: int | None = None,
) -> dict:
    """
    Convierte una alerta real de Wazuh al formato interno
    utilizado por CyberShield.

    Soporta:
    - Regla 5763: fuerza bruta SSH confirmada.
    - Wazuh FIM / syscheck.
    - FIM del laboratorio ransomware-demo.
    """

    rule = raw_event.get("rule") or {}
    agent = raw_event.get("agent") or {}
    syscheck = raw_event.get("syscheck") or {}
    decoder = raw_event.get("decoder") or {}
    data = raw_event.get("data") or {}

    rule_id = str(rule.get("id") or "")
    rule_groups = rule.get("groups") or []

    mitre = rule.get("mitre") or {}
    mitre_ids = mitre.get("id") or []

    path = syscheck.get("path")

    # =========================================================
    # 1. FUERZA BRUTA SSH CONFIRMADA POR WAZUH
    # =========================================================

    is_ssh_bruteforce = (
        rule_id == "5763"
        or (
            "T1110" in mitre_ids
            and "authentication_failures" in rule_groups
        )
    )

    if is_ssh_bruteforce:
        source_ip = data.get("srcip")

        attempts = _safe_int(
            rule.get("frequency"),
            default=1,
        )

        details = {
            "wazuh_rule_id": rule_id,
            "wazuh_level": rule.get("level"),
            "wazuh_description": rule.get("description"),
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "decoder": decoder.get("name"),
            "srcip": source_ip,
            "srcport": data.get("srcport"),
            "destination_user": data.get("dstuser"),
            "attempts": attempts,
            "sensor_confirmed_bruteforce": True,
            "successful_login": False,
            "unauthorized_access": False,
            "privilege_escalation": False,
            "mitre_ids": mitre_ids,
            "mitre_tactics": mitre.get("tactic") or [],
            "mitre_techniques": mitre.get("technique") or [],
            "groups": rule_groups,
            "firedtimes": rule.get("firedtimes"),
            "full_log": raw_event.get("full_log"),
            "previous_output": raw_event.get("previous_output"),
            "original_timestamp": raw_event.get("timestamp"),
            "raw_location": raw_event.get("location"),
            "integration": "wazuh_real",
        }

        user = data.get("dstuser")

        description = (
            "Wazuh detectó fuerza bruta SSH"
            + (f" contra el usuario {user}" if user else "")
            + (f" desde {source_ip}" if source_ip else "")
        )

        return {
            "event_type": "multiple_login_attempts",
            "source": "wazuh",
            "source_ip": source_ip,
            "server_id": server_id,
            "user": user,
            "description": description,
            "scope": "REACHED",
            "details": details,
        }

    # =========================================================
    # 2. WAZUH FIM / SYSCHECK
    # =========================================================

    is_fim = (
        bool(syscheck)
        or decoder.get("name")
        in (
            "syscheck_integrity_changed",
            "syscheck_new_entry",
        )
    )

    if not is_fim:
        return {
            "event_type": "unknown_wazuh_event",
            "source": "wazuh",
            "source_ip": agent.get("ip"),
            "server_id": server_id,
            "description": (
                rule.get("description")
                or "Evento real recibido desde Wazuh"
            ),
            "details": {
                "wazuh_rule_id": rule_id,
                "wazuh_level": rule.get("level"),
                "agent_id": agent.get("id"),
                "agent_name": agent.get("name"),
                "original_timestamp": raw_event.get("timestamp"),
                "integration": "wazuh_real",
            },
        }

    normalized_path = str(path or "")
    event_name = str(syscheck.get("event") or "").lower()

    change_applied = event_name in (
        "modified",
        "added",
        "deleted",
    )

    # Solo se considera señal ransomware-like automática
    # dentro de las carpetas EXCLUSIVAS del laboratorio.
    lab_ransomware_paths = (
        "/opt/cybershield-lab/ransomware-demo/",
        "/lab/simulators/data/documentos_demo/",
    )

    in_ransomware_lab = any(
        marker in normalized_path
        for marker in lab_ransomware_paths
    )

    sensor_confirmed_ransomware_like = (
        in_ransomware_lab
        and change_applied
    )

    filename = ""

    if path:
        filename = Path(path).name.lower()

    is_decoy = (
        "senuelo" in filename
        or "señuelo" in filename
    )

    if sensor_confirmed_ransomware_like:
        event_type = "possible_ransomware_behavior"
        authorized = False
        file_criticality = "important"
    else:
        event_type = "suspicious_file_change"
        authorized = not is_decoy
        file_criticality = (
            "critical"
            if is_decoy
            else "common"
        )

    agent_ip = agent.get("ip")

    if agent_ip in (
        "any",
        "unknown",
        "",
    ):
        agent_ip = None

    suspicious_extension = filename.endswith(
        (
            ".locked",
            ".encrypted",
            ".enc",
        )
    )

    details = {
        "wazuh_rule_id": rule_id,
        "wazuh_level": rule.get("level"),
        "wazuh_description": rule.get("description"),
        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),
        "decoder": decoder.get("name"),
        "path": path,
        "wazuh_event": syscheck.get("event"),
        "authorized": authorized,
        "file_criticality": file_criticality,
        "change_applied": change_applied,

        "sensor_confirmed_ransomware_like": (
            sensor_confirmed_ransomware_like
        ),

        "lab_ransomware_signal": in_ransomware_lab,

        # No fingimos que hubo 50 o 100 archivos.
        # Cada alerta FIM representa al menos un cambio real.
        "modified_files": 1 if change_applied else 0,
        "renamed_files": 0,

        "suspicious_extension": suspicious_extension,
        "maintenance_mode": False,

        "size_before": syscheck.get("size_before"),
        "size_after": syscheck.get("size_after"),

        "md5_before": syscheck.get("md5_before"),
        "md5_after": syscheck.get("md5_after"),

        "sha1_before": syscheck.get("sha1_before"),
        "sha1_after": syscheck.get("sha1_after"),

        "sha256_before": syscheck.get("sha256_before"),
        "sha256_after": syscheck.get("sha256_after"),

        "mitre_ids": mitre_ids,
        "mitre_tactics": mitre.get("tactic") or [],
        "mitre_techniques": mitre.get("technique") or [],
        "groups": rule_groups,

        "original_timestamp": raw_event.get("timestamp"),
        "raw_location": raw_event.get("location"),

        "integration": "wazuh_real",
    }

    if sensor_confirmed_ransomware_like:
        description = (
            "Wazuh FIM detectó cambios dentro del laboratorio "
            f"ransomware-demo: {path}"
        )

        scope = "IMPACT"

    else:
        description = (
            f"Wazuh FIM detectó actividad en {path}"
            if path
            else "Evento real recibido desde Wazuh"
        )

        scope = None

    return {
        "event_type": event_type,
        "source": "wazuh",
        "source_ip": agent_ip,
        "server_id": server_id,
        "description": description,
        "scope": scope,
        "details": details,
    }
