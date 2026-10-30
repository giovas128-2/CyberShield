import subprocess
import time
from datetime import datetime, timedelta, timezone

import httpx


API = "http://127.0.0.1:8000"

ALLOWED_IPS = {
    "172.25.176.1",      # Windows actual
    "100.125.119.56",    # srv-yahir-01 para demo posterior
}


def get_actions(status):
    try:
        response = httpx.get(
            f"{API}/response-actions",
            params={
                "status": status,
                "action_type": "RESTRICT_LATERAL_COMMUNICATION",
            },
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print("[LATERAL] Error API:", exc)
        return []


def patch_action(action_id, endpoint, success, result):
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
            "[LATERAL] API ->",
            response.status_code,
            response.text,
        )

        return response.status_code < 400

    except Exception as exc:
        print("[LATERAL] Error reportando:", exc)
        return False


def run(args):
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def rule_args(ip):
    return [
        "-s", ip,
        "-p", "tcp",
        "--dport", "22",
        "-j", "DROP",
    ]


def is_blocked(ip):
    result = run(
        ["iptables", "-C", "INPUT"]
        + rule_args(ip)
    )
    return result.returncode == 0


def block_ip(action):
    action_id = int(action["id"])
    ip = str(action.get("target") or "")

    if ip not in ALLOWED_IPS:
        return patch_action(
            action_id,
            "execution-result",
            False,
            "IP fuera de la allowlist del laboratorio.",
        )

    if not is_blocked(ip):
        result = run(
            ["iptables", "-I", "INPUT", "1"]
            + rule_args(ip)
        )

        if result.returncode != 0:
            return patch_action(
                action_id,
                "execution-result",
                False,
                "No se pudo aplicar bloqueo SSH: "
                + result.stderr,
            )

    if not is_blocked(ip):
        return patch_action(
            action_id,
            "execution-result",
            False,
            "No se pudo verificar el bloqueo SSH.",
        )

    return patch_action(
        action_id,
        "execution-result",
        True,
        (
            "RESTRICT_LATERAL_COMMUNICATION aplicado. "
            f"SSH desde {ip} hacia srv-cyber-01 "
            "quedó bloqueado temporalmente y verificado."
        ),
    )


def parse_timestamp(value):
    if not value:
        return None

    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def rollback_due(action):
    executed_at = parse_timestamp(
        action.get("executed_at")
    )

    if not executed_at:
        return False

    duration = int(
        action.get("duration_seconds") or 0
    )

    return (
        datetime.now(timezone.utc)
        >= executed_at + timedelta(seconds=duration)
    )


def unblock_ip(action):
    action_id = int(action["id"])
    ip = str(action.get("target") or "")

    if ip not in ALLOWED_IPS:
        return False

    if is_blocked(ip):
        result = run(
            ["iptables", "-D", "INPUT"]
            + rule_args(ip)
        )

        if result.returncode != 0:
            return patch_action(
                action_id,
                "rollback-result",
                False,
                "No se pudo retirar bloqueo SSH: "
                + result.stderr,
            )

    if is_blocked(ip):
        return patch_action(
            action_id,
            "rollback-result",
            False,
            "El bloqueo SSH continúa activo.",
        )

    return patch_action(
        action_id,
        "rollback-result",
        True,
        (
            f"Restricción SSH para {ip} retirada. "
            "Comunicación restaurada."
        ),
    )


def main():
    print(
        "CyberShield Lateral Response Bridge iniciado"
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
        "[LATERAL] Inicio limpio desde action_id:",
        floor,
    )

    cursor = floor
    owned = set()

    while True:
        pending = get_actions("pending")

        new_actions = sorted(
            (
                action
                for action in pending
                if int(action["id"]) > cursor
            ),
            key=lambda action: int(action["id"]),
        )

        for action in new_actions:
            action_id = int(action["id"])

            print(
                "[LATERAL] NUEVA acción:",
                action_id,
                action.get("target"),
            )

            if block_ip(action):
                owned.add(action_id)

            cursor = max(cursor, action_id)

        for action in get_actions("executed"):
            action_id = int(action["id"])

            if action_id not in owned:
                continue

            if rollback_due(action):
                print(
                    "[LATERAL] Rollback:",
                    action_id,
                )

                if unblock_ip(action):
                    owned.discard(action_id)

        time.sleep(1)


if __name__ == "__main__":
    main()
