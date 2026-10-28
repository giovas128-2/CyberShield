import json
import time
import requests

WAZUH_ALERTS = "/var/ossec/logs/alerts/alerts.json"

API_URL = (
    "http://127.0.0.1:8000"
    "/integrations/wazuh?server_id=2"
)


def send_event(event):
    try:
        response = requests.post(
            API_URL,
            json=event,
            timeout=10,
        )

        print(
            "WAZUH ->",
            response.status_code,
            response.text,
        )

    except Exception as exc:
        print("Error enviando Wazuh:", exc)


def follow(path):
    with open(path, "r", encoding="utf-8") as file:
        file.seek(0, 2)

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.5)
                continue

            yield line


print("CyberShield Wazuh Forwarder iniciado")

for line in follow(WAZUH_ALERTS):
    try:
        event = json.loads(line)

        decoder = event.get("decoder") or {}
        syscheck = event.get("syscheck") or {}

        is_fim = (
            decoder.get("name")
            == "syscheck_integrity_changed"
            or bool(syscheck)
        )

        if not is_fim:
            continue

        send_event(event)

    except json.JSONDecodeError:
        print("JSON inválido recibido de Wazuh")