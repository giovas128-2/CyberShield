import json
import time

import httpx


ACTIVE_RESPONSE_LOG = (
    "/var/ossec/logs/active-responses.log"
)

API_URL = (
    "http://127.0.0.1:8000"
    "/integrations/wazuh/active-response"
)


def send_report(
    operation: str,
    target: str,
):
    payload = {
        "operation": operation,
        "action_type": "BLOCK_SOURCE_IP",
        "target": target,
        "success": True,
        "result": (
            "Wazuh Active Response registró "
            f"firewall-drop {operation.upper()} "
            f"para la IP {target}."
        ),
    }

    # El ADD puede aparecer casi al mismo tiempo
    # que CyberShield crea la acción pendiente.
    # Reintentamos unos segundos para evitar
    # una condición de carrera.
    max_attempts = (
        6
        if operation == "add"
        else 3
    )

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            response = httpx.post(
                API_URL,
                json=payload,
                timeout=5.0,
            )

            print(
                "ACTIVE RESPONSE ->",
                response.status_code,
                response.text,
            )

            if response.status_code < 400:
                return True

            if response.status_code == 404:
                if attempt < max_attempts:
                    time.sleep(1)
                    continue

            return False

        except Exception as exc:
            print(
                "Error enviando Active Response:",
                exc,
            )

            if attempt < max_attempts:
                time.sleep(1)

    return False


def extract_json(line: str):
    """
    El log tiene este formato:

    fecha firewall-drop: {JSON}

    Tomamos solamente la parte JSON.
    """

    start = line.find("{")

    if start == -1:
        return None

    try:
        return json.loads(
            line[start:]
        )

    except json.JSONDecodeError:
        return None


def process_line(line: str):
    data = extract_json(line)

    if not data:
        return

    command = data.get("command")

    if command not in (
        "add",
        "delete",
    ):
        return

    parameters = (
        data.get("parameters")
        or {}
    )

    alert = (
        parameters.get("alert")
        or {}
    )

    rule = (
        alert.get("rule")
        or {}
    )

    rule_id = str(
        rule.get("id")
        or ""
    )

    # Por ahora automatizamos solamente
    # el escenario controlado de fuerza bruta.
    if rule_id != "5763":
        return

    event_data = (
        alert.get("data")
        or {}
    )

    source_ip = (
        event_data.get("srcip")
    )

    if not source_ip:
        print(
            "Active Response 5763 "
            "sin srcip; se ignora."
        )
        return

    print(
        "Wazuh Active Response detectado:",
        command,
        source_ip,
    )

    send_report(
        operation=command,
        target=source_ip,
    )


def follow(path: str):
    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:

        # Empezamos al final para no procesar
        # acciones históricas.
        file.seek(0, 2)

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.25)
                continue

            yield line


print(
    "CyberShield Active Response Bridge iniciado"
)

for line in follow(
    ACTIVE_RESPONSE_LOG
):
    process_line(line)
