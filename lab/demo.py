#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / "backend" / "venv-wsl" / "bin" / "python"

RUN_SCENARIO = ROOT / "lab" / "run_scenario.py"
RANSOMWARE = (
    ROOT
    / "lab"
    / "simulators"
    / "ransomware_demo.py"
)


def run(args, sudo=False):
    command = []

    if sudo:
        command.append("sudo")

    command.extend(
        [
            str(PYTHON),
            *[str(arg) for arg in args],
        ]
    )

    print()
    print("=" * 60)
    print("Ejecutando:")
    print(" ".join(command))
    print("=" * 60)
    print()

    subprocess.run(
        command,
        cwd=ROOT,
        check=False,
    )


def pause():
    input(
        "\nPresiona ENTER para volver al menú..."
    )


def system_status():
    commands = [
        (
            "Backend",
            [
                "curl",
                "-s",
                "http://127.0.0.1:8000/health",
            ],
        ),
        (
            "Wazuh Manager",
            [
                "sudo",
                "systemctl",
                "is-active",
                "wazuh-manager",
            ],
        ),
        (
            "Suricata",
            [
                "sudo",
                "systemctl",
                "is-active",
                "suricata",
            ],
        ),
        (
            "Tailscale",
            [
                "tailscale",
                "ip",
                "-4",
            ],
        ),
    ]

    print()
    print("===== ESTADO CYBERSHIELD =====")

    for name, command in commands:
        print(f"\n{name}:")

        subprocess.run(
            command,
            cwd=ROOT,
            check=False,
        )

    print()
    print("Procesos defensivos:")

    process_names = [
        "wazuh_forwarder.py",
        "suricata_forwarder.py",
        "wazuh_active_response_bridge.py",
        "cybershield_lab_response_bridge.py",
        "cybershield_privilege_response_bridge.py",
        "cybershield_lateral_response_bridge.py",
        "cybershield_exfil_response_bridge.py",
    ]

    for process in process_names:
        result = subprocess.run(
            [
                "pgrep",
                "-f",
                process,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        icon = (
            "✅"
            if result.returncode == 0
            else "❌"
        )

        print(
            f"{icon} {process}"
        )


def ransomware_demo():
    print()
    print(
        "Este escenario utiliza únicamente "
        "12 archivos sintéticos del laboratorio."
    )

    print(
        "Wazuh FIM observará cambios reales "
        "y CyberShield podrá detener el simulador."
    )

    print()

    run(
        [
            RANSOMWARE,
            "--prepare",
        ],
        sudo=True,
    )

    run(
        [
            RANSOMWARE,
            "--start",
        ],
        sudo=True,
    )

    print()
    print(
        "La restauración debe hacerse después "
        "del rollback automático."
    )

    answer = input(
        "¿Deseas intentar restaurar ahora? [s/N]: "
    ).strip().lower()

    if answer == "s":
        run(
            [
                RANSOMWARE,
                "--restore",
            ],
            sudo=True,
        )


def show_menu():
    print()
    print("=" * 60)
    print("           CYBERSHIELD - DEMOSTRACIÓN")
    print("=" * 60)
    print()
    print("1. Fuerza bruta")
    print("2. Abuso de privilegios")
    print("3. Posible exfiltración")
    print("4. Movimiento lateral SSH")
    print("5. Ransomware-like + Wazuh FIM")
    print("6. Estado del sistema")
    print()
    print("0. Salir")
    print()


def main():
    while True:
        show_menu()

        option = input(
            "Selecciona una opción: "
        ).strip()

        if option == "1":
            run(
                [
                    RUN_SCENARIO,
                    "brute",
                ]
            )
            pause()

        elif option == "2":
            run(
                [
                    RUN_SCENARIO,
                    "privilege",
                ]
            )
            pause()

        elif option == "3":
            run(
                [
                    RUN_SCENARIO,
                    "exfil",
                ]
            )
            pause()

        elif option == "4":
            run(
                [
                    RUN_SCENARIO,
                    "lateral",
                ]
            )
            pause()

        elif option == "5":
            ransomware_demo()
            pause()

        elif option == "6":
            system_status()
            pause()

        elif option == "0":
            print()
            print(
                "CyberShield Demo finalizada."
            )
            return

        else:
            print()
            print(
                "Opción inválida."
            )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print()
        print()
        print(
            "Demo interrumpida."
        )
        sys.exit(0)
