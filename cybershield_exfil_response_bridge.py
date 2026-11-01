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
        return None


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
            "[EXFIL-BRIDGE] Backend no disponible. "
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
        "[EXFIL-BRIDGE] Inicio desde action_id:",
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
    # Al iniciar solo adoptamos LA ACCIÓN MÁS RECIENTE
    # de cada destino permitido, sin importar si está
    # pending o executed.
    #
    # Esto evita ejecutar acciones históricas antiguas
    # y también evita que un rollback viejo retire una
    # protección perteneciente a una acción más nueva.
    # =========================================================

    latest_by_target = {}

    for action in existing:
        target = str(
            action.get("target") or ""
        )

        if target not in ALLOWED_DESTINATIONS:
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
                "[EXFIL-BRIDGE] Recuperando "
                "acción pendiente:",
                action_id,
                target,
            )

            if apply_restriction(
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
                    "[EXFIL-BRIDGE] Resultado no "
                    "confirmado. Se reintentará:",
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
                    "[EXFIL-BRIDGE] Rollback pendiente "
                    "al recuperar:",
                    action_id,
                )

                rollback_restriction(
                    action
                )

            elif is_blocked(
                target
            ):
                print(
                    "[EXFIL-BRIDGE] Adoptando "
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
                "[EXFIL-BRIDGE] No se pudo consultar "
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

                retry_pending.discard(
                    action_id
                )

            else:
                print(
                    "[EXFIL-BRIDGE] Resultado no "
                    "confirmado. Se reintentará:",
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
                "[EXFIL-BRIDGE] No se pudo consultar "
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
            # Puede ocurrir que el backend sí haya recibido
            # execution-result y cambiado la acción a
            # "executed", pero la respuesta HTTP se haya
            # perdido. En ese caso ya no aparecerá en
            # PENDING, aunque localmente la protección exista.
            # =================================================

            if action_id in retry_pending:
                target = str(
                    action.get("target") or ""
                )

                if (
                    target in ALLOWED_DESTINATIONS
                    and is_blocked(target)
                ):
                    print(
                        "[EXFIL-BRIDGE] Acción reconciliada "
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
                        "[EXFIL-BRIDGE] AVISO: backend marca "
                        "EXECUTED pero no se verificó la "
                        "protección local:",
                        action_id,
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
