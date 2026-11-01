import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx


API_BASE = "http://127.0.0.1:8000"

STATE_DIR = Path(
    "/opt/cybershield-lab/evidence"
)

ALLOWED_USERS = {
    "priv_demo",
}


def get_actions(status):
    try:
        response = httpx.get(
            f"{API_BASE}/response-actions",
            params={
                "status": status,
                "action_type": "TEMPORARY_ACCOUNT_LOCK",
            },
            timeout=5.0,
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:
        print(
            "[PRIV-BRIDGE] Error consultando API:",
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
            (
                f"{API_BASE}/response-actions/"
                f"{action_id}/{endpoint}"
            ),
            json={
                "success": success,
                "result": result,
            },
            timeout=10.0,
        )

        print(
            "[PRIV-BRIDGE] API ->",
            response.status_code,
            response.text,
        )

        return response.status_code < 400

    except Exception as exc:
        print(
            "[PRIV-BRIDGE] Error reportando:",
            exc,
        )

        return False


def state_file(action_id):
    return (
        STATE_DIR
        / f"privilege_action_{action_id}.json"
    )


def run_command(args):
    """
    Ejecuta únicamente argumentos explícitos.
    Nunca utiliza shell=True.
    """

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    return (
        result.returncode,
        result.stdout.strip(),
        result.stderr.strip(),
    )


def account_status(username):
    code, stdout, stderr = run_command(
        [
            "passwd",
            "-S",
            username,
        ]
    )

    if code != 0:
        return None, stderr

    fields = stdout.split()

    if len(fields) < 2:
        return None, stdout

    return fields[1], stdout


def lock_account(action):
    action_id = int(
        action["id"]
    )

    username = str(
        action.get("target") or ""
    )

    if username not in ALLOWED_USERS:
        return patch_action(
            action_id,
            "execution-result",
            False,
            "Cuenta fuera de la allowlist.",
        )

    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sf = state_file(
        action_id
    )

    status_before, raw_before = (
        account_status(username)
    )

    if status_before is None:
        return patch_action(
            action_id,
            "execution-result",
            False,
            (
                "No se pudo consultar la cuenta: "
                + raw_before
            ),
        )

    # =====================================================
    # IDEMPOTENCIA
    #
    # Si ya existe evidencia local de esta misma acción,
    # NO sobrescribimos el estado original de la cuenta.
    # Esto es importante para poder hacer rollback.
    # =====================================================

    state_created_now = False

    if sf.exists():
        if status_before == "L":
            return patch_action(
                action_id,
                "execution-result",
                True,
                (
                    "TEMPORARY_ACCOUNT_LOCK ya estaba "
                    "aplicado localmente. "
                    f"La cuenta {username} continúa "
                    "bloqueada y fue verificada."
                ),
            )

    else:
        sf.write_text(
            json.dumps(
                {
                    "action_id": action_id,
                    "username": username,
                    "status_before": status_before,
                    "created_at": (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    ),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        state_created_now = True

    code, stdout, stderr = run_command(
        [
            "usermod",
            "-L",
            username,
        ]
    )

    if code != 0:
        # Solo borramos el estado si fue creado
        # durante este intento.
        if state_created_now:
            sf.unlink(
                missing_ok=True
            )

        return patch_action(
            action_id,
            "execution-result",
            False,
            (
                "No se pudo bloquear la cuenta: "
                + stderr
            ),
        )

    status_after, raw_after = (
        account_status(username)
    )

    verified = (
        status_after == "L"
    )

    if not verified:
        if state_created_now:
            sf.unlink(
                missing_ok=True
            )

        return patch_action(
            action_id,
            "execution-result",
            False,
            (
                "El comando terminó pero no se pudo "
                f"verificar el bloqueo: {raw_after}"
            ),
        )

    result = (
        "TEMPORARY_ACCOUNT_LOCK aplicado. "
        f"La cuenta {username} quedó bloqueada "
        "temporalmente y el estado fue verificado."
    )

    return patch_action(
        action_id,
        "execution-result",
        True,
        result,
    )


def parse_timestamp(value):
    if not value:
        return None

    try:
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

    except ValueError:
        return None


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
        >= (
            executed_at
            + timedelta(
                seconds=duration
            )
        )
    )


def unlock_account(action):
    action_id = int(
        action["id"]
    )

    sf = state_file(
        action_id
    )

    if not sf.exists():
        return False

    state = json.loads(
        sf.read_text(
            encoding="utf-8"
        )
    )

    username = str(
        state.get("username") or ""
    )

    if username not in ALLOWED_USERS:
        return patch_action(
            action_id,
            "rollback-result",
            False,
            "Cuenta fuera de allowlist.",
        )

    # =====================================================
    # RESTAURAR EL ESTADO ORIGINAL
    #
    # No asumimos que la cuenta estaba desbloqueada antes
    # de la respuesta automática. Si ya estaba bloqueada,
    # CyberShield debe preservar ese estado.
    # =====================================================

    status_before = str(
        state.get("status_before") or ""
    )

    current_status, raw_current = (
        account_status(username)
    )

    if current_status is None:
        return patch_action(
            action_id,
            "rollback-result",
            False,
            (
                "No se pudo consultar el estado actual "
                "de la cuenta: "
                + raw_current
            ),
        )

    if status_before == "L":
        # La cuenta ya estaba bloqueada antes de que
        # CyberShield actuara. El rollback debe dejarla
        # bloqueada.

        if current_status != "L":
            code, stdout, stderr = run_command(
                [
                    "usermod",
                    "-L",
                    username,
                ]
            )

            if code != 0:
                return patch_action(
                    action_id,
                    "rollback-result",
                    False,
                    (
                        "No se pudo restaurar el bloqueo "
                        "original de la cuenta: "
                        + stderr
                    ),
                )

            current_status, raw_current = (
                account_status(username)
            )

            if current_status != "L":
                return patch_action(
                    action_id,
                    "rollback-result",
                    False,
                    (
                        "No se pudo verificar el bloqueo "
                        "original de la cuenta: "
                        + raw_current
                    ),
                )

        message = (
            f"Cuenta {username} restaurada a su "
            "estado original: ya estaba bloqueada "
            "antes de la respuesta CyberShield."
        )

    else:
        # La cuenta no estaba bloqueada antes de la
        # respuesta automática. Solo la desbloqueamos
        # si actualmente continúa bloqueada.

        if current_status == "L":
            code, stdout, stderr = run_command(
                [
                    "usermod",
                    "-U",
                    username,
                ]
            )

            if code != 0:
                return patch_action(
                    action_id,
                    "rollback-result",
                    False,
                    (
                        "No se pudo desbloquear la cuenta: "
                        + stderr
                    ),
                )

            current_status, raw_current = (
                account_status(username)
            )

            if current_status == "L":
                return patch_action(
                    action_id,
                    "rollback-result",
                    False,
                    (
                        "La cuenta continúa bloqueada: "
                        + raw_current
                    ),
                )

        message = (
            f"Cuenta {username} restaurada a su "
            "estado anterior. Protección temporal "
            "retirada."
        )

    # =====================================================
    # CONFIRMACIÓN DEL ROLLBACK
    #
    # El estado local NO se elimina antes de confirmar
    # que el backend recibió rollback-result.
    #
    # Si el PATCH falla, el siguiente ciclo puede volver
    # a intentar el reporte sin perder la evidencia del
    # estado original.
    # =====================================================

    reported = patch_action(
        action_id,
        "rollback-result",
        True,
        message,
    )

    if reported:
        sf.unlink(
            missing_ok=True
        )

    return reported


def main():
    print(
        "CyberShield Privilege Response Bridge iniciado"
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
            "[PRIV-BRIDGE] Backend no disponible. "
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
        "[PRIV-BRIDGE] Inicio desde action_id:",
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
    # Solo consideramos LA ACCIÓN MÁS RECIENTE
    # de cada usuario permitido.
    #
    # Nunca ejecutamos múltiples acciones históricas
    # sobre una misma cuenta al reiniciar el bridge.
    # =========================================================

    latest_by_target = {}

    for action in existing:
        target = str(
            action.get("target") or ""
        )

        if target not in ALLOWED_USERS:
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
                "[PRIV-BRIDGE] Recuperando "
                "acción pendiente:",
                action_id,
                target,
            )

            if lock_account(
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
                    "[PRIV-BRIDGE] Resultado no "
                    "confirmado. Se reintentará:",
                    action_id,
                )

                retry_pending.add(
                    action_id
                )

        elif status == "executed":
            sf = state_file(
                action_id
            )

            # Solo adoptamos una acción ejecutada
            # si este equipo conserva evidencia local
            # de haber aplicado ese bloqueo.
            if not sf.exists():
                continue

            if rollback_due(
                action
            ):
                print(
                    "[PRIV-BRIDGE] Rollback pendiente "
                    "al recuperar:",
                    action_id,
                )

                unlock_account(
                    action
                )

            else:
                current_status, _ = (
                    account_status(
                        target
                    )
                )

                if current_status == "L":
                    print(
                        "[PRIV-BRIDGE] Adoptando "
                        "bloqueo activo:",
                        action_id,
                        target,
                    )

                    owned.add(
                        action_id
                    )

                else:
                    print(
                        "[PRIV-BRIDGE] AVISO: existe "
                        "estado local pero la cuenta "
                        "no está bloqueada:",
                        action_id,
                        target,
                    )

    while True:
        pending = get_actions(
            "pending"
        )

        if pending is None:
            print(
                "[PRIV-BRIDGE] No se pudo consultar "
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
            key=lambda item: int(
                item["id"]
            ),
        )

        for action in new_actions:
            action_id = int(
                action["id"]
            )

            print(
                "[PRIV-BRIDGE] NUEVA acción:",
                action_id,
                action.get("target"),
            )

            if lock_account(
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
                    "[PRIV-BRIDGE] Resultado no "
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
                "[PRIV-BRIDGE] No se pudo consultar "
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

                sf = state_file(
                    action_id
                )

                current_status, _ = (
                    account_status(
                        target
                    )
                )

                if (
                    target in ALLOWED_USERS
                    and sf.exists()
                    and current_status == "L"
                ):
                    print(
                        "[PRIV-BRIDGE] Acción reconciliada "
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
                        "[PRIV-BRIDGE] AVISO: backend marca "
                        "EXECUTED pero no se verificó "
                        "el bloqueo local:",
                        action_id,
                        target,
                    )

            if action_id not in owned:
                continue

            if not state_file(
                action_id
            ).exists():
                owned.discard(
                    action_id
                )
                continue

            if rollback_due(
                action
            ):
                print(
                    "[PRIV-BRIDGE] Rollback:",
                    action_id,
                )

                if unlock_account(
                    action
                ):
                    owned.discard(
                        action_id
                    )

        time.sleep(1)


if __name__ == "__main__":
    main()
