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

    # ---------------------------------------------------------
    # Tipo normalizado
    # ---------------------------------------------------------

    if suricata_event_type in (
        "alert",
        "flow",
    ):
        event_type = "suspicious_network_traffic"
    else:
        event_type = "suricata_telemetry"

    # Un alert de Suricata representa una señal sospechosa,
    # pero NO prueba por sí solo que hubo impacto.
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
        "signature_id": alert.get("signature_id"),
        "category": alert.get("category"),
        "suricata_severity": alert.get("severity"),

        "flow_pkts_toserver": flow.get(
            "pkts_toserver"
        ),
        "flow_pkts_toclient": flow.get(
            "pkts_toclient"
        ),
        "flow_bytes_toserver": flow.get(
            "bytes_toserver"
        ),
        "flow_bytes_toclient": flow.get(
            "bytes_toclient"
        ),

        # Por ahora cada evento recibido cuenta como uno.
        # Después correlacionaremos varios eventos en 60 s.
        "requests": 1,
        "time_window_seconds": 60,

        # Una alerta es sospechosa, pero no significa
        # automáticamente compromiso.
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
                f"Suricata detectó tráfico sospechoso "
                f"{src_ip}:{src_port} -> "
                f"{dest_ip}:{dest_port} {proto}"
            )

    else:
        description = (
            f"Suricata registró flujo "
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