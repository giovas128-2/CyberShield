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

        return []


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

    # Guardamos el estado anterior para rollback.
    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sf = state_file(
        action_id
    )

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

    code, stdout, stderr = run_command(
        [
            "usermod",
            "-L",
            username,
        ]
    )

    if code != 0:
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

    # passwd -S devuelve L cuando está bloqueada.
    verified = (
        status_after == "L"
    )

    if not verified:
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

    username = state[
        "username"
    ]

    if username not in ALLOWED_USERS:
        return patch_action(
            action_id,
            "rollback-result",
            False,
            "Cuenta fuera de allowlist.",
        )

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

    status_after, raw_after = (
        account_status(username)
    )

    if status_after == "L":
        return patch_action(
            action_id,
            "rollback-result",
            False,
            (
                "La cuenta continúa bloqueada: "
                + raw_after
            ),
        )

    sf.unlink(
        missing_ok=True
    )

    return patch_action(
        action_id,
        "rollback-result",
        True,
        (
            f"Cuenta {username} desbloqueada. "
            "Protección temporal retirada."
        ),
    )


def main():
    print(
        "CyberShield Privilege Response Bridge iniciado"
    )

    # Todo lo que existía antes de arrancar
    # se considera histórico.
    existing = (
        get_actions("pending")
        + get_actions("executed")
    )

    session_floor = max(
        (
            int(action["id"])
            for action in existing
        ),
        default=0,
    )

    print(
        "[PRIV-BRIDGE] Inicio limpio desde action_id:",
        session_floor,
    )

    cursor = session_floor

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

            lock_account(
                action
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

            if action_id <= session_floor:
                continue

            if not state_file(
                action_id
            ).exists():
                continue

            if rollback_due(
                action
            ):
                print(
                    "[PRIV-BRIDGE] Rollback:",
                    action_id,
                )

                unlock_account(
                    action
                )

        time.sleep(1)


if __name__ == "__main__":
    main()
