import os
import stat
import subprocess
import time
from datetime import datetime, timedelta, timezone

import httpx

from cybershield_service_client import get_service_headers


API = "http://127.0.0.1:8000"

ACTION_TYPES = (
    "RESTRICT_DEVICE_ACCESS",
    "PROTECT_CRITICAL_FILE",
    "RESTRICT_OUTBOUND_CONNECTION",
)

ALLOWED_DEVICE_PREFIXES = (
    "PRUEBA-",
)

ALLOWED_FILES = {
    "/opt/cybershield/lab/senuelo_sc3.txt",
}

ALLOWED_NETWORK_TARGETS = {
    "172.25.176.1:8088",
}


def get_actions(status, action_type):
    try:
        response = httpx.get(
            f"{API}/response-actions",
            params={
                "status": status,
                "action_type": action_type,
            },
            headers=get_service_headers(),
            timeout=5,
        )

        response.raise_for_status()
        return response.json()

    except Exception as exc:
        print(
            "[SC235-BRIDGE] Error API:",
            action_type,
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
            headers=get_service_headers(),
            timeout=10,
        )

        print(
            "[SC235-BRIDGE] API ->",
            response.status_code,
            response.text,
        )

        return response.status_code < 400

    except Exception as exc:
        print(
            "[SC235-BRIDGE] Error reportando:",
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


# ============================================================
# SC2 - DEVICE TRUST
# ============================================================

def valid_lab_device(device_uuid):
    return any(
        device_uuid.startswith(prefix)
        for prefix in ALLOWED_DEVICE_PREFIXES
    )


def execute_device_restriction(action):
    action_id = int(action["id"])
    device_uuid = str(
        action.get("target") or ""
    )

    if not valid_lab_device(device_uuid):
        return patch_action(
            action_id,
            "execution-result",
            False,
            (
                "El dispositivo no pertenece a los "
                "identificadores permitidos del laboratorio."
            ),
        )

    return patch_action(
        action_id,
        "execution-result",
        True,
        (
            "RESTRICT_DEVICE_ACCESS verificado. "
            f"El dispositivo {device_uuid} permanece "
            "sin autorización en Device Trust y su acceso "
            "fue rechazado por CyberShield."
        ),
    )


# ============================================================
# SC3 - PROTECCIÓN DE ARCHIVO
# ============================================================

def file_is_protected(path):
    try:
        mode = stat.S_IMODE(
            os.stat(path).st_mode
        )

        return (
            mode & stat.S_IWUSR == 0
            and mode & stat.S_IWGRP == 0
            and mode & stat.S_IWOTH == 0
        )

    except OSError:
        return False


def execute_file_protection(action):
    action_id = int(action["id"])
    path = str(
        action.get("target") or ""
    )

    if path not in ALLOWED_FILES:
        return patch_action(
            action_id,
            "execution-result",
            False,
            "Archivo fuera de la allowlist del laboratorio.",
        )

    if not os.path.isfile(path):
        return patch_action(
            action_id,
            "execution-result",
            False,
            f"El archivo {path} no existe.",
        )

    result = run(
        [
            "chmod",
            "0444",
            path,
        ]
    )

    if result.returncode != 0:
        return patch_action(
            action_id,
            "execution-result",
            False,
            (
                "No se pudo proteger el archivo: "
                + result.stderr
            ),
        )

    if not file_is_protected(path):
        return patch_action(
            action_id,
            "execution-result",
            False,
            "No se pudo verificar la protección del archivo.",
        )

    return patch_action(
        action_id,
        "execution-result",
        True,
        (
            "PROTECT_CRITICAL_FILE aplicado y verificado. "
            f"{path} quedó temporalmente en modo solo lectura "
            "para evitar nuevas modificaciones."
        ),
    )


def rollback_file_protection(action):
    action_id = int(action["id"])
    path = str(
        action.get("target") or ""
    )

    if path not in ALLOWED_FILES:
        return False

    if not os.path.exists(path):
        return patch_action(
            action_id,
            "rollback-result",
            False,
            f"No existe el archivo {path}.",
        )

    result = run(
        [
            "chmod",
            "0644",
            path,
        ]
    )

    if result.returncode != 0:
        return patch_action(
            action_id,
            "rollback-result",
            False,
            (
                "No se pudieron restaurar permisos: "
                + result.stderr
            ),
        )

    if file_is_protected(path):
        return patch_action(
            action_id,
            "rollback-result",
            False,
            "El archivo continúa en modo protegido.",
        )

    return patch_action(
        action_id,
        "rollback-result",
        True,
        (
            f"Protección temporal retirada de {path}. "
            "Permisos del archivo de laboratorio restaurados."
        ),
    )


# ============================================================
# SC5 - RESTRICCIÓN DE CONEXIÓN SALIENTE
# ============================================================

def parse_network_target(target):
    if target not in ALLOWED_NETWORK_TARGETS:
        return None

    ip, port = target.rsplit(
        ":",
        1,
    )

    return ip, port


def outbound_firewall_rule(ip, port):
    return [
        "-d",
        ip,
        "-p",
        "tcp",
        "--dport",
        port,
        "-j",
        "REJECT",
    ]


def outbound_is_blocked(ip, port):
    result = run(
        [
            "iptables",
            "-C",
            "OUTPUT",
        ]
        + outbound_firewall_rule(
            ip,
            port,
        )
    )

    return result.returncode == 0


def execute_outbound_restriction(action):
    action_id = int(action["id"])
    target = str(
        action.get("target") or ""
    )

    parsed = parse_network_target(
        target
    )

    if not parsed:
        return patch_action(
            action_id,
            "execution-result",
            False,
            (
                "Destino fuera de la allowlist "
                "del laboratorio SC5."
            ),
        )

    ip, port = parsed

    if not outbound_is_blocked(
        ip,
        port,
    ):
        result = run(
            [
                "iptables",
                "-I",
                "OUTPUT",
                "1",
            ]
            + outbound_firewall_rule(
                ip,
                port,
            )
        )

        if result.returncode != 0:
            return patch_action(
                action_id,
                "execution-result",
                False,
                (
                    "No se pudo aplicar "
                    "RESTRICT_OUTBOUND_CONNECTION: "
                    + result.stderr
                ),
            )

    if not outbound_is_blocked(
        ip,
        port,
    ):
        return patch_action(
            action_id,
            "execution-result",
            False,
            "No se pudo verificar el bloqueo SC5.",
        )

    return patch_action(
        action_id,
        "execution-result",
        True,
        (
            "RESTRICT_OUTBOUND_CONNECTION aplicado y verificado. "
            f"El tráfico TCP hacia {ip}:{port} quedó "
            "temporalmente bloqueado por CyberShield."
        ),
    )


def rollback_outbound_restriction(action):
    action_id = int(action["id"])
    target = str(
        action.get("target") or ""
    )

    parsed = parse_network_target(
        target
    )

    if not parsed:
        return False

    ip, port = parsed

    if outbound_is_blocked(
        ip,
        port,
    ):
        result = run(
            [
                "iptables",
                "-D",
                "OUTPUT",
            ]
            + outbound_firewall_rule(
                ip,
                port,
            )
        )

        if result.returncode != 0:
            return patch_action(
                action_id,
                "rollback-result",
                False,
                (
                    "No se pudo retirar "
                    "RESTRICT_OUTBOUND_CONNECTION: "
                    + result.stderr
                ),
            )

    if outbound_is_blocked(
        ip,
        port,
    ):
        return patch_action(
            action_id,
            "rollback-result",
            False,
            "La restricción SC5 continúa activa.",
        )

    return patch_action(
        action_id,
        "rollback-result",
        True,
        (
            f"Restricción hacia {ip}:{port} retirada. "
            "Conectividad del laboratorio restaurada."
        ),
    )


# ============================================================
# UTILIDADES
# ============================================================

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
        datetime.now(timezone.utc)
        >= executed_at
        + timedelta(
            seconds=duration
        )
    )


def execute_action(action):
    action_type = str(
        action.get("action_type") or ""
    )

    if action_type == "RESTRICT_DEVICE_ACCESS":
        return execute_device_restriction(
            action
        )

    if action_type == "PROTECT_CRITICAL_FILE":
        return execute_file_protection(
            action
        )

    if action_type == "RESTRICT_OUTBOUND_CONNECTION":
        return execute_outbound_restriction(
            action
        )

    return False


def rollback_action(action):
    action_type = str(
        action.get("action_type") or ""
    )

    if action_type == "PROTECT_CRITICAL_FILE":
        return rollback_file_protection(
            action
        )

    if action_type == "RESTRICT_OUTBOUND_CONNECTION":
        return rollback_outbound_restriction(
            action
        )

    # SC2 no habilita automáticamente un dispositivo
    # que nunca fue registrado.
    return False


def has_local_protection(action):
    action_type = str(
        action.get("action_type") or ""
    )

    target = str(
        action.get("target") or ""
    )

    if action_type == "RESTRICT_DEVICE_ACCESS":
        return valid_lab_device(
            target
        )

    if action_type == "PROTECT_CRITICAL_FILE":
        return (
            target in ALLOWED_FILES
            and file_is_protected(
                target
            )
        )

    if action_type == "RESTRICT_OUTBOUND_CONNECTION":
        parsed = parse_network_target(
            target
        )

        if not parsed:
            return False

        return outbound_is_blocked(
            *parsed
        )

    return False


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "CyberShield SC2/SC3/SC5 Response Bridge iniciado"
    )

    # Solo recuperamos la acción más reciente
    # de cada tipo/objetivo.
    existing = []

    while True:
        complete = True
        existing = []

        for action_type in ACTION_TYPES:
            pending = get_actions(
                "pending",
                action_type,
            )

            executed = get_actions(
                "executed",
                action_type,
            )

            if (
                pending is None
                or executed is None
            ):
                complete = False
                break

            existing.extend(
                pending + executed
            )

        if complete:
            break

        print(
            "[SC235-BRIDGE] Backend no disponible. "
            "Reintentando..."
        )

        time.sleep(2)

    floor = max(
        (
            int(action["id"])
            for action in existing
        ),
        default=0,
    )

    cursor = floor

    print(
        "[SC235-BRIDGE] Inicio desde action_id:",
        floor,
    )

    owned = set()
    retry_pending = set()

    latest_by_key = {}

    for action in existing:
        key = (
            str(
                action.get(
                    "action_type"
                )
                or ""
            ),
            str(
                action.get(
                    "target"
                )
                or ""
            ),
        )

        current = latest_by_key.get(
            key
        )

        if (
            current is None
            or int(action["id"])
            > int(current["id"])
        ):
            latest_by_key[key] = action

    for action in sorted(
        latest_by_key.values(),
        key=lambda item: int(
            item["id"]
        ),
    ):
        action_id = int(
            action["id"]
        )

        status = str(
            action.get(
                "status"
            )
            or ""
        ).lower()

        if status == "pending":
            print(
                "[SC235-BRIDGE] Recuperando PENDING:",
                action_id,
                action.get("action_type"),
                action.get("target"),
            )

            if execute_action(
                action
            ):
                owned.add(
                    action_id
                )
            else:
                retry_pending.add(
                    action_id
                )

        elif (
            status == "executed"
            and has_local_protection(
                action
            )
        ):
            owned.add(
                action_id
            )

    while True:
        all_pending = []

        for action_type in ACTION_TYPES:
            result = get_actions(
                "pending",
                action_type,
            )

            if result is not None:
                all_pending.extend(
                    result
                )

        new_actions = sorted(
            (
                action
                for action in all_pending
                if (
                    int(action["id"])
                    > cursor
                    or int(action["id"])
                    in retry_pending
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
                "[SC235-BRIDGE] NUEVA acción:",
                action_id,
                action.get("action_type"),
                action.get("target"),
            )

            if execute_action(
                action
            ):
                owned.add(
                    action_id
                )

                retry_pending.discard(
                    action_id
                )
            else:
                retry_pending.add(
                    action_id
                )

            cursor = max(
                cursor,
                action_id,
            )

        all_executed = []

        for action_type in ACTION_TYPES:
            result = get_actions(
                "executed",
                action_type,
            )

            if result is not None:
                all_executed.extend(
                    result
                )

        for action in all_executed:
            action_id = int(
                action["id"]
            )

            if (
                action_id in retry_pending
                and has_local_protection(
                    action
                )
            ):
                print(
                    "[SC235-BRIDGE] Acción reconciliada:",
                    action_id,
                )

                owned.add(
                    action_id
                )

                retry_pending.discard(
                    action_id
                )

            if action_id not in owned:
                continue

            action_type = str(
                action.get(
                    "action_type"
                )
                or ""
            )

            # Device Trust no se revierte automáticamente.
            if action_type == "RESTRICT_DEVICE_ACCESS":
                continue

            if rollback_due(
                action
            ):
                print(
                    "[SC235-BRIDGE] Rollback:",
                    action_id,
                    action_type,
                )

                if rollback_action(
                    action
                ):
                    owned.discard(
                        action_id
                    )

        time.sleep(1)


if __name__ == "__main__":
    main()
