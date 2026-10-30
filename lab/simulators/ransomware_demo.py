import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


LAB_ROOT = Path(
    "/opt/cybershield-lab/ransomware-demo"
).resolve()

DEMO_DIR = (
    LAB_ROOT / "d3_lab"
).resolve()

RUNTIME_DIR = Path(
    "/opt/cybershield-lab/runtime"
).resolve()

BASELINE_FILE = (
    RUNTIME_DIR / "ransomware_demo_baseline.json"
)

PID_FILE = (
    RUNTIME_DIR / "ransomware_demo.pid"
)

STATE_FILE = (
    RUNTIME_DIR / "ransomware_demo_state.json"
)

AUTHORIZED_ROOT = Path(
    "/opt/cybershield-lab"
).resolve()

RUNNING = True


def log(message):
    print(
        f"[SIMULATOR] {message}",
        flush=True,
    )


def validate_environment():
    """
    Seguridad:
    este simulador SOLO puede trabajar dentro de
    /opt/cybershield-lab/ransomware-demo.
    """

    if (
        LAB_ROOT != AUTHORIZED_ROOT / "ransomware-demo"
        or AUTHORIZED_ROOT not in LAB_ROOT.parents
    ):
        raise RuntimeError(
            "Ruta de laboratorio no autorizada."
        )

    DEMO_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RUNTIME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def save_state(status, **extra):
    data = {
        "scenario": "ransomware_like",
        "status": status,
        "updated_at": now(),
        **extra,
    }

    STATE_FILE.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def prepare():
    validate_environment()

    baseline = {}

    for number in range(1, 13):
        path = (
            DEMO_DIR
            / f"archivo_{number}.txt"
        )

        content = (
            "CYBERSHIELD DEMO FILE\n"
            f"Archivo sintético #{number}\n"
            "Contenido original del laboratorio.\n"
        )

        path.write_text(
            content,
            encoding="utf-8",
        )

        baseline[
            str(path)
        ] = content

    BASELINE_FILE.write_text(
        json.dumps(
            baseline,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    save_state(
        "prepared",
        files=len(baseline),
    )

    log(
        f"Laboratorio preparado con {len(baseline)} archivos."
    )

    log(
        f"Ruta autorizada: {DEMO_DIR}"
    )


def signal_handler(signum, frame):
    global RUNNING

    RUNNING = False

    log(
        "Señal defensiva recibida. "
        "Finalizando simulador de forma segura."
    )


def start():
    global RUNNING

    validate_environment()

    if not BASELINE_FILE.exists():
        log(
            "El laboratorio no está preparado."
        )

        log(
            "Ejecuta primero: "
            "python ransomware_demo.py --prepare"
        )

        sys.exit(1)

    if PID_FILE.exists():
        try:
            old_pid = int(
                PID_FILE.read_text().strip()
            )

            if Path(
                f"/proc/{old_pid}"
            ).exists():
                log(
                    "Ya existe un simulador ejecutándose."
                )
                sys.exit(1)

        except Exception:
            pass

    PID_FILE.write_text(
        str(os.getpid()),
        encoding="utf-8",
    )

    signal.signal(
        signal.SIGTERM,
        signal_handler,
    )

    signal.signal(
        signal.SIGINT,
        signal_handler,
    )

    run_id = (
        "RANSOM-"
        + datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
    )

    save_state(
        "running",
        run_id=run_id,
        pid=os.getpid(),
        started_at=now(),
    )

    log(
        "Escenario ransomware-like iniciado."
    )

    log(
        f"Run ID: {run_id}"
    )

    log(
        f"PID: {os.getpid()}"
    )

    log(
        "IMPORTANTE: no existe cifrado ni eliminación real."
    )

    log(
        "Solo se modificarán archivos sintéticos."
    )

    files = sorted(
        DEMO_DIR.glob(
            "archivo_*.txt"
        )
    )

    modification_count = 0

    try:
        # El simulador permanece activo durante un máximo
        # de 60 segundos o hasta que CyberShield lo detenga.
        deadline = time.time() + 60

        while (
            RUNNING
            and time.time() < deadline
        ):
            for path in files:
                if not RUNNING:
                    break

                if not path.exists():
                    continue

                marker = (
                    "\n[DEMO-RANSOMWARE-LIKE] "
                    f"modificación controlada "
                    f"{modification_count + 1} "
                    f"{now()}\n"
                )

                try:
                    with path.open(
                        "a",
                        encoding="utf-8",
                    ) as file:
                        file.write(marker)

                except PermissionError:
                    log(
                        "CyberShield bloqueó la escritura. "
                        "Contención detectada."
                    )

                    RUNNING = False
                    break

                modification_count += 1

                log(
                    f"Modificado: {path.name}"
                )

                save_state(
                    "running",
                    run_id=run_id,
                    pid=os.getpid(),
                    modifications=modification_count,
                )

                time.sleep(0.5)

            time.sleep(0.5)

    finally:
        PID_FILE.unlink(
            missing_ok=True
        )

        save_state(
            "stopped",
            run_id=run_id,
            modifications=modification_count,
            stopped_at=now(),
        )

        log(
            "Simulador detenido."
        )

        log(
            f"Modificaciones realizadas: {modification_count}"
        )


def status():
    validate_environment()

    if not STATE_FILE.exists():
        print(
            json.dumps(
                {
                    "status": "not_prepared"
                },
                indent=2,
            )
        )
        return

    print(
        STATE_FILE.read_text(
            encoding="utf-8"
        )
    )

    if PID_FILE.exists():
        try:
            pid = int(
                PID_FILE.read_text().strip()
            )

            print(
                f"[SIMULATOR] PID registrado: {pid}"
            )

            print(
                "[SIMULATOR] Proceso activo:",
                Path(
                    f"/proc/{pid}"
                ).exists(),
            )

        except Exception:
            pass


def restore():
    validate_environment()

    if not BASELINE_FILE.exists():
        log(
            "No existe baseline para restaurar."
        )
        return

    baseline = json.loads(
        BASELINE_FILE.read_text(
            encoding="utf-8"
        )
    )

    restored = 0

    for raw_path, content in baseline.items():
        path = Path(
            raw_path
        ).resolve()

        # Segunda barrera de seguridad.
        if (
            path != DEMO_DIR
            and DEMO_DIR not in path.parents
        ):
            log(
                f"Ruta rechazada: {path}"
            )
            continue

        try:
            path.write_text(
                content,
                encoding="utf-8",
            )

            restored += 1

        except PermissionError:
            log(
                "CyberShield mantiene el recurso "
                "en modo solo lectura."
            )

            log(
                "Espera al rollback antes de restaurar."
            )

            return

    PID_FILE.unlink(
        missing_ok=True
    )

    save_state(
        "restored",
        restored_files=restored,
    )

    log(
        f"Restaurados {restored} archivos sintéticos."
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Simulador benigno ransomware-like "
            "para CyberShield."
        )
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--prepare",
        action="store_true",
    )

    group.add_argument(
        "--start",
        action="store_true",
    )

    group.add_argument(
        "--status",
        action="store_true",
    )

    group.add_argument(
        "--restore",
        action="store_true",
    )

    args = parser.parse_args()

    if args.prepare:
        prepare()

    elif args.start:
        start()

    elif args.status:
        status()

    elif args.restore:
        restore()


if __name__ == "__main__":
    main()
