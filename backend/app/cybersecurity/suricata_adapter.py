def normalize_suricata_event(
    raw_event: dict,
    server_id: int | None = None,
) -> dict:
    """
    Convierte eventos reales de Suricata EVE JSON
    al formato interno de CyberShield.
    """

    suricata_event_type = raw_event.get(
        "event_type",
        "unknown",
    )

    alert = raw_event.get("alert") or {}
    flow = raw_event.get("flow") or {}

    src_ip = raw_event.get("src_ip")
    src_port = raw_event.get("src_port")

    dest_ip = raw_event.get("dest_ip")
    dest_port = raw_event.get("dest_port")

    proto = raw_event.get("proto")

    bytes_toserver = int(
        flow.get("bytes_toserver") or 0
    )

    bytes_toclient = int(
        flow.get("bytes_toclient") or 0
    )

    # =========================================================
    # EXFILTRACIÓN CONTROLADA DEL LABORATORIO
    # =========================================================
    #
    # Flujo:
    # srv-cyber-01 -> Windows host
    # puerto 8765
    #
    # Solo esta ruta explícita del laboratorio puede
    # convertirse automáticamente en exfiltración.
    #
    lab_exfil_flow = (
        suricata_event_type == "flow"
        and dest_ip == "172.25.176.1"
        and int(dest_port or 0) == 8765
        and bytes_toserver >= 10_000_000
    )

    if lab_exfil_flow:
        return {
            "event_type": "possible_data_exfiltration",
            "source": "suricata",
            "source_ip": src_ip,
            "server_id": server_id,
            "description": (
                "Suricata detectó transferencia saliente "
                "de datos sintéticos hacia el receptor "
                "externo controlado del laboratorio."
            ),
            "scope": "REACHED",
            "details": {
                "suricata_event_type": (
                    suricata_event_type
                ),
                "src_ip": src_ip,
                "src_port": src_port,
                "dest_ip": dest_ip,
                "dest_port": dest_port,
                "proto": proto,

                "bytes_toserver": bytes_toserver,
                "bytes_toclient": bytes_toclient,

                "bytes_toserver_total": (
                    bytes_toserver
                ),
                "bytes_toclient_total": (
                    bytes_toclient
                ),

                "dest_class": "external",
                "bulk_data_access": True,
                "prior_open_incident": False,
                "untrusted_session_device": False,
                "off_hours": False,

                "sensor_confirmed_exfiltration": True,
                "lab_exfiltration_signal": True,

                "destination_ip": dest_ip,
                "destination_port": dest_port,

                "original_timestamp": (
                    raw_event.get("timestamp")
                ),

                "integration": "suricata_real",
            },
        }

    # =========================================================
    # TELEMETRÍA GENERAL DE SURICATA
    # =========================================================

    if suricata_event_type in (
        "alert",
        "flow",
    ):
        event_type = "suspicious_network_traffic"
    else:
        event_type = "suricata_telemetry"

    is_alert = (
        suricata_event_type == "alert"
    )

    details = {
        "suricata_event_type": suricata_event_type,

        "src_ip": src_ip,
        "src_port": src_port,

        "dest_ip": dest_ip,
        "dest_port": dest_port,

        "proto": proto,

        "signature": alert.get("signature"),
        "signature_id": alert.get(
            "signature_id"
        ),
        "category": alert.get("category"),
        "suricata_severity": alert.get(
            "severity"
        ),

        "flow_pkts_toserver": flow.get(
            "pkts_toserver"
        ),
        "flow_pkts_toclient": flow.get(
            "pkts_toclient"
        ),
        "flow_bytes_toserver": (
            bytes_toserver
        ),
        "flow_bytes_toclient": (
            bytes_toclient
        ),

        "requests": 1,
        "time_window_seconds": 60,

        "destination_allowed": not is_alert,

        "impact_confirmed": False,

        "original_timestamp": raw_event.get(
            "timestamp"
        ),

        "integration": "suricata_real",
    }

    if is_alert:
        signature = alert.get("signature")

        if signature:
            description = (
                f"Suricata detectó alerta: {signature}"
            )
        else:
            description = (
                "Suricata detectó tráfico sospechoso "
                f"{src_ip}:{src_port} -> "
                f"{dest_ip}:{dest_port} {proto}"
            )
    else:
        description = (
            "Suricata registró flujo "
            f"{src_ip}:{src_port} -> "
            f"{dest_ip}:{dest_port} {proto}"
        )

    return {
        "event_type": event_type,
        "source": "suricata",
        "source_ip": src_ip,
        "server_id": server_id,
        "description": description,
        "details": details,
    }
