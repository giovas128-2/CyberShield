import subprocess
import time
from datetime import datetime, timedelta, timezone

import httpx

from cybershield_service_client import get_service_headers


API = "http://127.0.0.1:8000"

ALLOWED_IPS = {
    "100.125.119.56",  # Servidor remoto autorizado
}


def get_actions(status):
    try:
        response = httpx.get(
            f"{API}/response-actions",
            params={
                "status": status,
                "action_type": "RESTRICT_LATERAL_COMMUNICATION",
            },
            headers=get_service_headers(),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print("[LATERAL] Error API:", exc)
        return None


def patch_action(action_id, endpoint, success, result):
    try:
        response = httpx.patch(
            f"{API}/response-actions/{action_id}/{endpoint}",
            json={
                "success": success,
                "result": result,
            },
            headers=get_service_headers(),
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

    # No construimos el estado inicial hasta tener
    # una lectura REAL y completa del backend.
    while True:
        pending_existing = get_actions(
            "pending"
        )

        executed_existing = get_actions(
            "executed"
        )

        if (
            pending_existing is not None
            and executed_existing is not None
        ):
            break

        print(
            "[LATERAL] Backend no disponible. "
            "Esperando antes de recuperar acciones..."
        )

        time.sleep(2)

    existing = (
        pending_existing
        + executed_existing
    )

    floor = max(
        (
            int(action["id"])
            for action in existing
        ),
        default=0,
    )

    print(
        "[LATERAL] Inicio desde action_id:",
        floor,
    )

    cursor = floor
    owned = set()

    # IDs cuya acción local pudo ejecutarse pero cuyo
    # resultado todavía no pudo confirmarse al backend.
    retry_pending = set()

    # =========================================================
    # RECUPERACIÓN SEGURA
    #
    # Solo adoptamos la acción MÁS RECIENTE
    # de cada IP permitida.
    #
    # Esto evita que una acción ejecutada antigua
    # haga rollback sobre una protección nueva.
    # =========================================================

    latest_by_target = {}

    for action in existing:
        target = str(
            action.get("target") or ""
        )

        if target not in ALLOWED_IPS:
            continue

        current = latest_by_target.get(
            target
        )

        if (
            current is None
            or int(action["id"])
            > int(current["id"])
        ):
            latest_by_target[target] = action

    for action in sorted(
        latest_by_target.values(),
        key=lambda item: int(item["id"]),
    ):
        action_id = int(
            action["id"]
        )

        target = str(
            action.get("target") or ""
        )

        status = str(
            action.get("status") or ""
        ).lower()

        if status == "pending":
            print(
                "[LATERAL] Recuperando "
                "acción pendiente:",
                action_id,
                target,
            )

            if block_ip(
                action
            ):
                owned.add(
                    action_id
                )

                retry_pending.discard(
                    action_id
                )

            else:
                print(
                    "[LATERAL] Resultado no confirmado. "
                    "Se reintentará:",
                    action_id,
                )

                retry_pending.add(
                    action_id
                )

        elif status == "executed":
            if rollback_due(
                action
            ):
                print(
                    "[LATERAL] Rollback pendiente "
                    "al recuperar:",
                    action_id,
                )

                unblock_ip(
                    action
                )

            elif is_blocked(
                target
            ):
                print(
                    "[LATERAL] Adoptando "
                    "protección activa:",
                    action_id,
                    target,
                )

                owned.add(
                    action_id
                )

    while True:
        pending = get_actions(
            "pending"
        )

        if pending is None:
            print(
                "[LATERAL] No se pudo consultar "
                "PENDING. Reintentando..."
            )

            time.sleep(1)
            continue

        new_actions = sorted(
            (
                action
                for action in pending
                if (
                    int(action["id"]) > cursor
                    or int(action["id"]) in retry_pending
                )
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
                "[LATERAL] NUEVA acción:",
                action_id,
                action.get("target"),
            )

            if block_ip(
                action
            ):
                owned.add(
                    action_id
                )

                retry_pending.discard(
                    action_id
                )

            else:
                print(
                    "[LATERAL] Resultado no confirmado. "
                    "Se reintentará:",
                    action_id,
                )

                retry_pending.add(
                    action_id
                )

            cursor = max(
                cursor,
                action_id,
            )

        executed = get_actions(
            "executed"
        )

        if executed is None:
            print(
                "[LATERAL] No se pudo consultar "
                "EXECUTED. Reintentando..."
            )

            time.sleep(1)
            continue

        for action in executed:
            action_id = int(
                action["id"]
            )

            # =================================================
            # RECONCILIACIÓN DE PATCH
            #
            # El backend pudo recibir execution-result
            # y marcar la acción como executed aunque
            # la respuesta HTTP al bridge se haya perdido.
            # =================================================

            if action_id in retry_pending:
                target = str(
                    action.get("target") or ""
                )

                if (
                    target in ALLOWED_IPS
                    and is_blocked(target)
                ):
                    print(
                        "[LATERAL] Acción reconciliada "
                        "desde EXECUTED:",
                        action_id,
                        target,
                    )

                    owned.add(
                        action_id
                    )

                    retry_pending.discard(
                        action_id
                    )

                else:
                    print(
                        "[LATERAL] AVISO: backend marca "
                        "EXECUTED pero no se verificó "
                        "el bloqueo SSH local:",
                        action_id,
                    )

            if action_id not in owned:
                continue

            if rollback_due(
                action
            ):
                print(
                    "[LATERAL] Rollback:",
                    action_id,
                )

                if unblock_ip(
                    action
                ):
                    owned.discard(
                        action_id
                    )

        time.sleep(1)


if __name__ == "__main__":
    main()
