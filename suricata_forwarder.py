import json
import time

import httpx

from cybershield_service_client import get_service_headers

EVE_FILE = "/var/log/suricata/eve.json"

API_URL = (
    "http://127.0.0.1:8000"
    "/integrations/suricata?server_id=2"
)

# Evita enviar cientos de alertas del mismo flujo TCP.
# Cada flow_id se recuerda temporalmente durante 5 minutos.
FLOW_DEDUP_SECONDS = 300
seen_flow_ids = {}


def already_forwarded_flow(event):
    flow_id = event.get("flow_id")

    if flow_id is None:
        return False

    now = time.monotonic()

    expired = [
        saved_flow_id
        for saved_flow_id, timestamp in seen_flow_ids.items()
        if now - timestamp > FLOW_DEDUP_SECONDS
    ]

    for saved_flow_id in expired:
        seen_flow_ids.pop(saved_flow_id, None)

    if flow_id in seen_flow_ids:
        return True

    seen_flow_ids[flow_id] = now
    return False


def relevant(event):
    event_type = event.get(
        "event_type"
    )

    flow = event.get("flow") or {}
    alert = event.get("alert") or {}

    dest_ip = event.get("dest_ip")
    dest_port = int(
        event.get("dest_port") or 0
    )

    # Alerta específica del laboratorio:
    # CYBERSHIELD LAB Possible Data Exfiltration.
    lab_exfil_alert = (
        event_type == "alert"
        and int(alert.get("signature_id") or 0) == 1000002
        and dest_ip == "172.25.176.1"
        and dest_port == 8765
    )

    if lab_exfil_alert:
        return True

    # Alerta específica del laboratorio para SC5:
    # conexión saliente sospechosa.
    lab_suspicious_outbound_alert = (
        event_type == "alert"
        and int(alert.get("signature_id") or 0) == 1000003
    )

    if lab_suspicious_outbound_alert:
        return True

    # Conservamos la detección E2E anterior por volumen
    # como señal secundaria del laboratorio.
    if event_type != "flow":
        return False

    bytes_up = int(
        flow.get("bytes_toserver") or 0
    )

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
	    headers=get_service_headers(),
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
        if already_forwarded_flow(event):
            continue

        print(
            "EVENTO SURICATA RELEVANTE:",
            event.get("event_type"),
            event.get("src_ip"),
            "->",
            event.get("dest_ip"),
            event.get("dest_port"),
            "flow_id=",
            event.get("flow_id"),
        )

        send(event)
