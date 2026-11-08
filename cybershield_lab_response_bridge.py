import json
import os
import signal
import stat
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from cybershield_service_client import get_service_headers


API_BASE = "http://127.0.0.1:8000"

LAB_ROOT = Path(
    "/opt/cybershield-lab/ransomware-demo"
).resolve()

STATE_DIR = Path(
    "/opt/cybershield-lab/evidence"
).resolve()

RUNTIME_DIR = Path(
    "/opt/cybershield-lab/runtime"
).resolve()

PID_FILE = (
    RUNTIME_DIR / "ransomware_demo.pid"
)

LOCK_MARKER = (
    STATE_DIR / ".cybershield_lockdown_ransomware"
)

ALLOWED_TARGETS = {
    "srv-cyber-01",
    "127.0.0.1",
}


def api_get_actions(status):
    try:
        response = httpx.get(
            f"{API_BASE}/response-actions",
            params={
                "status": status,
                "action_type": "CONTAIN_HOST",
            },
            headers=get_service_headers(),
            timeout=5.0,
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:
        print(
            "[LAB-BRIDGE] Error consultando acciones:",
            exc,
        )
        return None


def api_patch(action_id, endpoint, success, result):
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
            headers=get_service_headers(),
            timeout=10.0,
        )

        print(
            "[LAB-BRIDGE] API ->",
            response.status_code,
            response.text,
        )

        return response.status_code < 400

    except Exception as exc:
        print(
            "[LAB-BRIDGE] Error reportando resultado:",
            exc,
        )
        return False


def state_file(action_id):
    return (
        STATE_DIR
        / f"contain_host_action_{action_id}.json"
    )


def process_matches_simulator(pid):
    """
    Solo permite detener un proceso cuyo comando
    contenga explícitamente ransomware_demo.py.
    """

    cmdline_path = Path(
        f"/proc/{pid}/cmdline"
    )

    if not cmdline_path.exists():
        return False

    try:
        raw = cmdline_path.read_bytes()
        cmdline = raw.replace(
            b"\x00",
            b" ",
        ).decode(
            "utf-8",
            errors="replace",
        )

    except Exception:
        return False

    return (
        "ransomware_demo.py"
        in cmdline
    )


def stop_simulator():
    """
    Detiene únicamente el simulador autorizado
    si existe un PID file válido.
    """

    if not PID_FILE.exists():
        return (
            True,
            "No había proceso ransomware_demo.py "
            "registrado para detener.",
        )

    try:
        pid = int(
            PID_FILE.read_text(
                encoding="utf-8"
            ).strip()
        )

    except Exception:
        return (
            False,
            "PID file del simulador inválido.",
        )

    if not process_matches_simulator(pid):
        return (
            False,
            (
                "El PID registrado no corresponde "
                "a ransomware_demo.py; por seguridad "
                "no se detuvo ningún proceso."
            ),
        )

    try:
        os.kill(
            pid,
            signal.SIGTERM,
        )

    except ProcessLookupError:
        return (
            True,
            "El simulador ya no estaba en ejecución.",
        )

    except Exception as exc:
        return (
            False,
            f"No se pudo detener el simulador: {exc}",
        )

    deadline = time.time() + 3

    while time.time() < deadline:
        if not Path(
            f"/proc/{pid}"
        ).exists():
            return (
                True,
                (
                    "ransomware_demo.py detenido "
                    "correctamente con SIGTERM."
                ),
            )

        time.sleep(0.2)

    # Solo forzamos la terminación si todavía
    # verificamos que ES el simulador permitido.
    if process_matches_simulator(pid):
        try:
            os.kill(
                pid,
                signal.SIGKILL,
            )

            return (
                True,
                (
                    "ransomware_demo.py requirió "
                    "terminación forzada controlada."
                ),
            )

        except Exception as exc:
            return (
                False,
                (
                    "No se pudo finalizar el "
                    f"simulador: {exc}"
                ),
            )

    return (
        True,
        "El simulador dejó de estar activo.",
    )


def snapshot_permissions():
    """
    Guarda únicamente permisos del laboratorio.
    No ejecuta comandos del sistema.
    """

    entries = []

    paths = [LAB_ROOT]

    paths.extend(
        sorted(
            LAB_ROOT.rglob("*"),
            key=lambda p: len(p.parts),
        )
    )

    for path in paths:
        if path.is_symlink():
            continue

        try:
            mode = stat.S_IMODE(
                path.stat().st_mode
            )

        except FileNotFoundError:
            continue

        relative = (
            "."
            if path == LAB_ROOT
            else str(
                path.relative_to(
                    LAB_ROOT
                )
            )
        )

        entries.append(
            {
                "path": relative,
                "mode": mode,
            }
        )

    return entries


def apply_read_only():
    """
    Quita bits de escritura únicamente dentro
    de /opt/cybershield-lab/ransomware-demo.
    """

    paths = list(
        LAB_ROOT.rglob("*")
    )

    # Archivos primero.
    for path in paths:
        if (
            path.is_symlink()
            or not path.is_file()
        ):
            continue

        current = stat.S_IMODE(
            path.stat().st_mode
        )

        path.chmod(
            current & ~0o222
        )

    # Directorios de mayor profundidad primero.
    directories = [
        p
        for p in paths
        if p.is_dir()
        and not p.is_symlink()
    ]

    directories.sort(
        key=lambda p: len(p.parts),
        reverse=True,
    )

    for path in directories:
        current = stat.S_IMODE(
            path.stat().st_mode
        )

        path.chmod(
            current & ~0o222
        )

    current = stat.S_IMODE(
        LAB_ROOT.stat().st_mode
    )

    LAB_ROOT.chmod(
        current & ~0o222
    )


def verify_containment():
    """
    Verifica que no queden permisos de escritura
    en el recurso demo.
    """

    paths = [LAB_ROOT]
    paths.extend(
        LAB_ROOT.rglob("*")
    )

    writable = []

    for path in paths:
        if path.is_symlink():
            continue

        try:
            mode = stat.S_IMODE(
                path.stat().st_mode
            )
        except FileNotFoundError:
            continue

        if mode & 0o222:
            writable.append(
                str(path)
            )

    if writable:
        return (
            False,
            "Persisten recursos escribibles: "
            + ", ".join(
                writable[:5]
            ),
        )

    return (
        True,
        (
            "El recurso ransomware-demo quedó "
            "sin permisos de escritura."
        ),
    )


def restore_permissions(entries):
    """
    Restaura exactamente los permisos guardados.
    """

    # Restauramos primero directorios poco profundos
    # para garantizar acceso al árbol.
    ordered = sorted(
        entries,
        key=lambda e: (
            str(e["path"]).count("/")
        ),
    )

    for entry in ordered:
        relative = entry["path"]

        path = (
            LAB_ROOT
            if relative == "."
            else (
                LAB_ROOT
                / relative
            )
        )

        try:
            resolved = path.resolve()

            if (
                resolved != LAB_ROOT
                and LAB_ROOT
                not in resolved.parents
            ):
                continue

            if resolved.exists():
                resolved.chmod(
                    int(entry["mode"])
                )

        except Exception as exc:
            print(
                "[LAB-BRIDGE] No se pudo restaurar",
                path,
                exc,
            )


def apply_containment(action):
    action_id = action["id"]
    target = action.get("target")

    if target not in ALLOWED_TARGETS:
        return api_patch(
            action_id,
            "execution-result",
            False,
            (
                "Target fuera de la allowlist "
                "del laboratorio."
            ),
        )

    if not LAB_ROOT.exists():
        return api_patch(
            action_id,
            "execution-result",
            False,
            (
                "No existe el directorio autorizado "
                f"{LAB_ROOT}."
            ),
        )

    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sf = state_file(
        action_id
    )

    # Si ya aplicamos la contención localmente
    # pero falló el reporte HTTP, no repetimos chmod.
    if sf.exists():
        verified, verification = (
            verify_containment()
        )

        return api_patch(
            action_id,
            "execution-result",
            verified,
            (
                "Contención previamente aplicada. "
                + verification
            ),
        )

    permissions = (
        snapshot_permissions()
    )

    stopped, stop_result = (
        stop_simulator()
    )

    if not stopped:
        return api_patch(
            action_id,
            "execution-result",
            False,
            stop_result,
        )

    state = {
        "action_id": action_id,
        "target": target,
        "root": str(LAB_ROOT),
        "created_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "permissions": permissions,
    }

    sf.write_text(
        json.dumps(
            state,
            indent=2,
        ),
        encoding="utf-8",
    )

    LOCK_MARKER.write_text(
        (
            "CyberShield containment active\n"
            f"action_id={action_id}\n"
        ),
        encoding="utf-8",
    )

    apply_read_only()

    verified, verification = (
        verify_containment()
    )

    if not verified:
        restore_permissions(
            permissions
        )

        try:
            LOCK_MARKER.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        return api_patch(
            action_id,
            "execution-result",
            False,
            (
                "La verificación de contención falló. "
                + verification
            ),
        )

    result = (
        "CONTAIN_HOST aplicado sobre el laboratorio. "
        f"{stop_result} "
        f"{verification} "
        "LOCKDOWN local activo."
    )

    return api_patch(
        action_id,
        "execution-result",
        True,
        result,
    )


def parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return None


def rollback_due(action):
    executed_at = parse_timestamp(
        action.get("executed_at")
    )

    duration = (
        action.get(
            "duration_seconds"
        )
        or 0
    )

    if not executed_at:
        return False

    if executed_at.tzinfo is None:
        executed_at = (
            executed_at.replace(
                tzinfo=timezone.utc
            )
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


def rollback_containment(action):
    action_id = int(
        action["id"]
    )

    sf = state_file(
        action_id
    )

    if not sf.exists():
        return api_patch(
            action_id,
            "rollback-result",
            False,
            (
                "No existe estado local para "
                "restaurar la contención."
            ),
        )

    try:
        state = json.loads(
            sf.read_text(
                encoding="utf-8"
            )
        )

        # =====================================================
        # RESTAURACIÓN LOCAL
        #
        # Restaurar permisos es idempotente: si el PATCH al
        # backend falla, podemos volver a ejecutar este bloque
        # utilizando el mismo state file.
        # =====================================================

        restore_permissions(
            state["permissions"]
        )

        LOCK_MARKER.unlink(
            missing_ok=True
        )

        message = (
            "Permisos del laboratorio restaurados. "
            "LOCKDOWN local retirado. "
            "El simulador NO se reinició."
        )

        # =====================================================
        # CONFIRMACIÓN DEL ROLLBACK
        #
        # NO eliminamos el state file antes de confirmar
        # rollback-result. Si la API falla, la evidencia
        # necesaria para reintentar permanece disponible.
        # =====================================================

        reported = api_patch(
            action_id,
            "rollback-result",
            True,
            message,
        )

        if reported:
            sf.unlink(
                missing_ok=True
            )
        else:
            print(
                "[LAB-BRIDGE] Rollback local aplicado "
                "pero no confirmado por backend. "
                "Se conserva state file:",
                action_id,
            )

        return reported

    except Exception as exc:
        return api_patch(
            action_id,
            "rollback-result",
            False,
            (
                "Error restaurando contención: "
                f"{exc}"
            ),
        )


CURSOR_FILE = (
    STATE_DIR / ".lab_bridge_cursor"
)


def save_cursor(value):
    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CURSOR_FILE.write_text(
        str(value),
        encoding="utf-8",
    )


def load_cursor():
    if CURSOR_FILE.exists():
        try:
            return int(
                CURSOR_FILE.read_text(
                    encoding="utf-8"
                ).strip()
            )
        except Exception:
            pass

    # Primera ejecución:
    # no inicializamos el cursor hasta obtener
    # una lectura REAL y completa del backend.
    while True:
        pending = api_get_actions(
            "pending"
        )

        executed = api_get_actions(
            "executed"
        )

        if (
            pending is not None
            and executed is not None
        ):
            actions = (
                pending
                + executed
            )
            break

        print(
            "[LAB-BRIDGE] Backend no disponible "
            "al inicializar cursor. Reintentando..."
        )

        time.sleep(2)

    cursor = max(
        (
            int(action["id"])
            for action in actions
        ),
        default=0,
    )

    save_cursor(cursor)

    print(
        "[LAB-BRIDGE] Cursor inicial:",
        cursor,
    )

    return cursor


def cleanup_historical_state_files(max_action_id):
    """
    Elimina estados locales de pruebas anteriores.
    Antes de llamar esta función el laboratorio debe
    haberse restaurado manualmente.
    """

    for path in STATE_DIR.glob(
        "contain_host_action_*.json"
    ):
        try:
            action_id = int(
                path.stem.rsplit("_", 1)[-1]
            )
        except ValueError:
            continue

        if action_id <= max_action_id:
            path.unlink(
                missing_ok=True
            )


def main():
    print(
        "CyberShield Lab Response Bridge iniciado"
    )

    print(
        "Directorio permitido:",
        LAB_ROOT,
    )

    cursor = load_cursor()

    # Esperamos una lectura válida del backend antes
    # de reconstruir el estado de recuperación.
    while True:
        pending_existing = api_get_actions(
            "pending"
        )

        executed_existing = api_get_actions(
            "executed"
        )

        if (
            pending_existing is not None
            and executed_existing is not None
        ):
            break

        print(
            "[LAB-BRIDGE] Backend no disponible. "
            "Esperando antes de recuperar acciones..."
        )

        time.sleep(2)

    existing = (
        pending_existing
        + executed_existing
    )

    existing_ids = [
        int(action["id"])
        for action in existing
    ]

    floor = max(
        [cursor, *existing_ids],
        default=0,
    )

    cursor = floor

    save_cursor(
        cursor
    )

    owned = set()

    # IDs cuya contención local pudo aplicarse pero cuyo
    # resultado todavía no pudo confirmarse al backend.
    retry_pending = set()

    print(
        "[LAB-BRIDGE] Inicio desde action_id:",
        floor,
    )

    # =========================================================
    # RECUPERACIÓN SEGURA
    #
    # No eliminamos archivos de estado al arrancar.
    # Esos archivos contienen los permisos originales
    # necesarios para restaurar el laboratorio.
    #
    # Solo consideramos LA ACCIÓN MÁS RECIENTE
    # de cada target permitido.
    # =========================================================

    latest_by_target = {}

    for action in existing:
        target = str(
            action.get("target") or ""
        )

        if target not in ALLOWED_TARGETS:
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
                "[LAB-BRIDGE] Recuperando "
                "acción pendiente:",
                action_id,
                target,
            )

            if apply_containment(
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
                    "[LAB-BRIDGE] Resultado no "
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

            # Una acción ejecutada solo se adopta
            # si existe evidencia local de que este
            # bridge aplicó realmente la contención.
            if not sf.exists():
                continue

            if rollback_due(
                action
            ):
                print(
                    "[LAB-BRIDGE] Rollback pendiente "
                    "al recuperar:",
                    action_id,
                )

                rollback_containment(
                    action
                )

            else:
                verified, verification = (
                    verify_containment()
                )

                if verified:
                    print(
                        "[LAB-BRIDGE] Adoptando "
                        "contención activa:",
                        action_id,
                        target,
                    )

                    owned.add(
                        action_id
                    )

                else:
                    print(
                        "[LAB-BRIDGE] AVISO: existe "
                        "estado local pero la contención "
                        "no está activa:",
                        action_id,
                        verification,
                    )

    while True:
        pending = api_get_actions(
            "pending"
        )

        if pending is None:
            print(
                "[LAB-BRIDGE] No se pudo consultar "
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
                "[LAB-BRIDGE] NUEVA acción:",
                action_id,
                action.get("target"),
            )

            if apply_containment(
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
                    "[LAB-BRIDGE] Resultado no "
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

            save_cursor(
                cursor
            )

        executed = api_get_actions(
            "executed"
        )

        if executed is None:
            print(
                "[LAB-BRIDGE] No se pudo consultar "
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
            # El backend pudo recibir execution-result y
            # marcar la acción como executed aunque la
            # respuesta HTTP al bridge se haya perdido.
            # =================================================

            if action_id in retry_pending:
                target = str(
                    action.get("target") or ""
                )

                sf = state_file(
                    action_id
                )

                verified = False
                verification = (
                    "Sin evidencia local de contención."
                )

                if (
                    target in ALLOWED_TARGETS
                    and sf.exists()
                ):
                    verified, verification = (
                        verify_containment()
                    )

                if verified:
                    print(
                        "[LAB-BRIDGE] Acción reconciliada "
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
                        "[LAB-BRIDGE] AVISO: backend marca "
                        "EXECUTED pero no se verificó "
                        "la contención local:",
                        action_id,
                        verification,
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
                    "[LAB-BRIDGE] Rollback:",
                    action_id,
                )

                if rollback_containment(
                    action
                ):
                    owned.discard(
                        action_id
                    )

        time.sleep(1)


if __name__ == "__main__":
    main()
