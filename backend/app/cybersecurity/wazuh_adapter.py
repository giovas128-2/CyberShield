from pathlib import Path


def normalize_wazuh_event(
    raw_event: dict,
    server_id: int | None = None,
) -> dict:
    """
    Convierte una alerta real de Wazuh al formato interno
    utilizado por CyberShield.

    Actualmente se priorizan eventos FIM / syscheck.
    """

    rule = raw_event.get("rule") or {}
    agent = raw_event.get("agent") or {}
    syscheck = raw_event.get("syscheck") or {}
    decoder = raw_event.get("decoder") or {}

    path = syscheck.get("path")

    # ---------------------------------------------------------
    # Determinar tipo de evento CyberShield
    # ---------------------------------------------------------

    if syscheck or decoder.get("name") == "syscheck_integrity_changed":
        event_type = "suspicious_file_change"
    else:
        event_type = "unknown_wazuh_event"

    # ---------------------------------------------------------
    # Archivo señuelo
    #
    # En nuestro laboratorio cualquier modificación al señuelo
    # se considera no autorizada porque precisamente existe
    # para detectar actividad inesperada.
    # ---------------------------------------------------------

    filename = ""

    if path:
        filename = Path(path).name.lower()

    is_decoy = (
        "senuelo" in filename
        or "señuelo" in filename
    )

    # Para otros archivos NO afirmamos automáticamente
    # que el cambio sea malicioso.
    authorized = not is_decoy

    if is_decoy:
        file_criticality = "critical"
    else:
        file_criticality = "common"

    # ---------------------------------------------------------
    # IP del agente
    # ---------------------------------------------------------

    agent_ip = agent.get("ip")

    if agent_ip in ("any", "unknown", ""):
        agent_ip = None

    # ---------------------------------------------------------
    # Details conservados para evidencia
    # ---------------------------------------------------------

    details = {
        "wazuh_rule_id": rule.get("id"),
        "wazuh_level": rule.get("level"),
        "wazuh_description": rule.get("description"),

        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),

        "decoder": decoder.get("name"),

        "path": path,
        "wazuh_event": syscheck.get("event"),

        "authorized": authorized,
        "file_criticality": file_criticality,

        # Si Wazuh reportó "modified",
        # significa que el cambio sí ocurrió.
        "change_applied": (
            syscheck.get("event") == "modified"
        ),

        "size_before": syscheck.get("size_before"),
        "size_after": syscheck.get("size_after"),

        "md5_before": syscheck.get("md5_before"),
        "md5_after": syscheck.get("md5_after"),

        "sha1_before": syscheck.get("sha1_before"),
        "sha1_after": syscheck.get("sha1_after"),

        "sha256_before": syscheck.get("sha256_before"),
        "sha256_after": syscheck.get("sha256_after"),

        "original_timestamp": raw_event.get("timestamp"),
        "raw_location": raw_event.get("location"),

        "integration": "wazuh_real",
    }

    description = (
        f"Wazuh FIM detectó modificación en {path}"
        if path
        else "Evento real recibido desde Wazuh"
    )

    return {
        "event_type": event_type,
        "source": "wazuh",
        "source_ip": agent_ip,
        "server_id": server_id,
        "description": description,
        "details": details,
    }