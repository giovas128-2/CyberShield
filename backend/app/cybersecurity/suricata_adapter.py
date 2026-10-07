def normalize_suricata_event(raw_event: dict) -> dict:
    return {
        "event_type": raw_event.get(
            "event_type",
            "suspicious_network_traffic"
        ),
        "source": "suricata",
        "source_ip": raw_event.get("source_ip", "127.0.0.1"),
        "description": raw_event.get(
            "description",
            "Evento recibido desde Suricata"
        ),
        "details": raw_event.get("details", {})
    }