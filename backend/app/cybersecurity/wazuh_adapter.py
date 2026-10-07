def normalize_wazuh_event(raw_event: dict) -> dict:
    return {
        "event_type": raw_event.get("event_type", "unknown_wazuh_event"),
        "source": "wazuh",
        "source_ip": raw_event.get("source_ip", "127.0.0.1"),
        "description": raw_event.get(
            "description",
            "Evento recibido desde Wazuh"
        ),
        "details": raw_event.get("details", {})
    }