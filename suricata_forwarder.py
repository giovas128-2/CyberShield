import json
import time

import httpx


EVE_FILE = "/var/log/suricata/eve.json"

API_URL = (
    "http://127.0.0.1:8000"
    "/integrations/suricata?server_id=2"
)


def relevant(event):
    event_type = event.get(
        "event_type"
    )

    # Para esta integración E2E solo reenviamos
    # el flujo controlado de exfiltración.
    # Las alertas generales de Suricata permanecen
    # en eve.json pero no saturan CyberShield.
    if event_type != "flow":
        return False

    flow = event.get("flow") or {}

    dest_ip = event.get("dest_ip")
    dest_port = int(
        event.get("dest_port") or 0
    )

    bytes_up = int(
        flow.get("bytes_toserver") or 0
    )

    # Solo reenviamos flujos grandes del
    # receptor de exfiltración del laboratorio.
    return (
        dest_ip == "172.25.176.1"
        and dest_port == 8765
        and bytes_up >= 10_000_000
    )


def send(event):
    try:
        response = httpx.post(
            API_URL,
            json=event,
            timeout=10.0,
        )

        print(
            "SURICATA ->",
            response.status_code,
            response.text[:600],
        )

    except Exception as exc:
        print(
            "Error enviando Suricata:",
            exc,
        )


def follow(path):
    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:

        file.seek(0, 2)

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.25)
                continue

            yield line


print(
    "CyberShield Suricata Forwarder iniciado"
)

for line in follow(EVE_FILE):
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue

    if relevant(event):
        print(
            "EVENTO SURICATA RELEVANTE:",
            event.get("event_type"),
            event.get("src_ip"),
            "->",
            event.get("dest_ip"),
            event.get("dest_port"),
        )

        send(event)
