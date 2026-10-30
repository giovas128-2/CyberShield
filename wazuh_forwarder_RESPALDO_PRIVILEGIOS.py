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

        rule = event.get("rule") or {}

        print(
            "WAZUH ->",
            f"rule={rule.get('id')}",
            response.status_code,
            response.text[:500],
        )

    except Exception as exc:
        print("Error enviando Wazuh:", exc)


def follow_json(path):
    """
    Sigue alerts.json sin intentar procesar
    una línea mientras Wazuh todavía la escribe.
    """

    with open(path, "r", encoding="utf-8") as file:
        file.seek(0, 2)

        buffer = ""

        while True:
            chunk = file.readline()

            if not chunk:
                time.sleep(0.2)
                continue

            buffer += chunk

            # Si todavía no llegó el salto de línea,
            # Wazuh puede seguir escribiendo el JSON.
            if not buffer.endswith("\n"):
                time.sleep(0.05)
                continue

            raw = buffer.strip()
            buffer = ""

            if not raw:
                continue

            try:
                yield json.loads(raw)

            except json.JSONDecodeError as exc:
                print(
                    "JSON no procesado:",
                    exc,
                    raw[:120],
                )


def is_relevant_event(event):
    rule = event.get("rule") or {}
    decoder = event.get("decoder") or {}
    syscheck = event.get("syscheck") or {}

    rule_id = str(rule.get("id") or "")

    # OLA 2: fuerza bruta SSH real
    is_bruteforce = rule_id == "5763"

    # OLA 3: dejamos preparado FIM
    is_fim = (
        decoder.get("name") == "syscheck_integrity_changed"
        or bool(syscheck)
    )

    if is_fim:
        fim_path = str(
            syscheck.get("path") or ""
        )

        filename = (
            fim_path.rsplit("/", 1)[-1]
            .lower()
        )

        # No reenviamos a CyberShield sus propios
        # archivos internos de control.
        if (
            filename == ".cybershield_lockdown"
            or filename.startswith(".ransomware_demo")
        ):
            is_fim = False

    return is_bruteforce or is_fim


print("CyberShield Wazuh Forwarder iniciado")

for event in follow_json(WAZUH_ALERTS):
    if not is_relevant_event(event):
        continue

    rule = event.get("rule") or {}

    print(
        "EVENTO RELEVANTE:",
        f"rule={rule.get('id')}",
        f"description={rule.get('description')}",
    )

    send_event(event)
