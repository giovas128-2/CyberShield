import subprocess
import time
from datetime import datetime, timedelta, timezone

import httpx

API = "http://127.0.0.1:8000"

ALLOWED_DESTINATIONS = {
    "172.25.176.1",
}

PORT = "8765"


def get_actions(status):
    try:
        response = httpx.get(
            f"{API}/response-actions",
            params={
                "status": status,
                "action_type": "RESTRICT_DATA_FLOW",
            },
            timeout=5,
        )

        response.raise_for_status()
        return response.json()

    except Exception as exc:
        print(
            "[EXFIL-BRIDGE] Error API:",
            exc,
        )
        return []


def patch_action(
    action_id,
    endpoint,
    success,
    result,
):
    try:
        response = httpx.patch(
            f"{API}/response-actions/{action_id}/{endpoint}",
            json={
                "success": success,
                "result": result,
            },
            timeout=10,
        )

        print(
            "[EXFIL-BRIDGE] API ->",
            response.status_code,
            response.text,
        )

        return response.status_code < 400

    except Exception as exc:
        print(
            "[EXFIL-BRIDGE] Error reportando:",
            exc,
        )
        return False


def run(args):
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def firewall_rule(ip):
    return [
        "-d", ip,
        "-p", "tcp",
        "--dport", PORT,
        "-j", "REJECT",
    ]


def is_blocked(ip):
    result = run(
        ["iptables", "-C", "OUTPUT"]
        + firewall_rule(ip)
    )

    return result.returncode == 0


def apply_restriction(action):
    action_id = int(
        action["id"]
    )

    ip = str(
        action.get("target") or ""
    )

    if ip not in ALLOWED_DESTINATIONS:
        return patch_action(
            action_id,
            "execution-result",
            False,
            "Destino fuera de la allowlist del laboratorio.",
        )

    if not is_blocked(ip):
        result = run(
            [
                "iptables",
                "-I",
                "OUTPUT",
                "1",
            ]
            + firewall_rule(ip)
        )

        if result.returncode != 0:
            return patch_action(
                action_id,
                "execution-result",
                False,
                (
                    "No se pudo aplicar "
                    "RESTRICT_DATA_FLOW: "
                    + result.stderr
                ),
            )

    if not is_blocked(ip):
        return patch_action(
            action_id,
            "execution-result",
            False,
            "No se pudo verificar el bloqueo.",
        )

    return patch_action(
        action_id,
        "execution-result",
        True,
        (
            "RESTRICT_DATA_FLOW aplicado. "
            f"Tráfico TCP hacia {ip}:{PORT} "
            "quedó temporalmente bloqueado "
            "y verificado."
        ),
    )


def parse_timestamp(value):
    if not value:
        return None

    dt = datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt


def rollback_due(action):
    executed_at = parse_timestamp(
        action.get("executed_at")
    )

    if not executed_at:
        return False

    duration = int(
        action.get(
            "duration_seconds"
        )
        or 0
    )

    return (
        datetime.now(
            timezone.utc
        )
        >= executed_at
        + timedelta(
            seconds=duration
        )
    )


def rollback_restriction(action):
    action_id = int(
        action["id"]
    )

    ip = str(
        action.get("target") or ""
    )

    if ip not in ALLOWED_DESTINATIONS:
        return False

    if is_blocked(ip):
        result = run(
            [
                "iptables",
                "-D",
                "OUTPUT",
            ]
            + firewall_rule(ip)
        )

        if result.returncode != 0:
            return patch_action(
                action_id,
                "rollback-result",
                False,
                (
                    "No se pudo retirar "
                    "RESTRICT_DATA_FLOW: "
                    + result.stderr
                ),
            )

    if is_blocked(ip):
        return patch_action(
            action_id,
            "rollback-result",
            False,
            "La restricción continúa activa.",
        )

    return patch_action(
        action_id,
        "rollback-result",
        True,
        (
            f"Restricción hacia {ip}:{PORT} retirada. "
            "Flujo del laboratorio recuperado."
        ),
    )


def main():
    print(
        "CyberShield Exfil Response Bridge iniciado"
    )

    existing = (
        get_actions("pending")
        + get_actions("executed")
    )

    floor = max(
        (
            int(action["id"])
            for action in existing
        ),
        default=0,
    )

    print(
        "[EXFIL-BRIDGE] Inicio limpio desde action_id:",
        floor,
    )

    cursor = floor
    owned = set()

    while True:
        pending = get_actions(
            "pending"
        )

        new_actions = sorted(
            (
                action
                for action in pending
                if int(action["id"]) > cursor
            ),
            key=lambda action: int(
                action["id"]
            ),
        )

        for action in new_actions:
            action_id = int(
                action["id"]
            )

            print(
                "[EXFIL-BRIDGE] NUEVA acción:",
                action_id,
                action.get("target"),
            )

            if apply_restriction(
                action
            ):
                owned.add(
                    action_id
                )

            cursor = max(
                cursor,
                action_id,
            )

        executed = get_actions(
            "executed"
        )

        for action in executed:
            action_id = int(
                action["id"]
            )

            if action_id not in owned:
                continue

            if rollback_due(
                action
            ):
                print(
                    "[EXFIL-BRIDGE] Rollback:",
                    action_id,
                )

                if rollback_restriction(
                    action
                ):
                    owned.discard(
                        action_id
                    )

        time.sleep(1)


if __name__ == "__main__":
    main()
