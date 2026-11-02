#!/usr/bin/env python3

import argparse
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


API = "http://127.0.0.1:8000"

SCENARIOS = {
    "brute": "sc1",
    "device": "sc2",
    "file": "sc3",
    "privilege": "sc4",
    "network": "sc5",
    "exfil": "sc6",
    "ransomware": "sc7",
    "lateral": "sc8",
}


def get_json(url):
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode())


def post_json(url):
    request = Request(
        url,
        method="POST",
        headers={
            "Content-Type": "application/json"
        },
        data=b"{}",
    )

    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode())


def show(title, value):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    print(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Lanzador de escenarios de laboratorio CyberShield"
    )

    parser.add_argument(
        "scenario",
        choices=SCENARIOS.keys(),
        help="Escenario que se desea ejecutar",
    )

    args = parser.parse_args()

    scenario_id = SCENARIOS[args.scenario]

    print()
    print("🛡️ CYBERSHIELD LAB")
    print(f"Escenario: {args.scenario}")
    print(f"ID: {scenario_id}")
    print()

    try:
        result = post_json(
            f"{API}/lab/scenarios/{scenario_id}/run"
        )

    except HTTPError as exc:
        print("❌ Error HTTP:", exc.code)
        print(exc.read().decode())
        return

    except URLError as exc:
        print("❌ Backend no disponible:", exc)
        return

    show("RESULTADO DEL EVENTO", result)

    event = result.get("event") or {}
    analysis = result.get("analysis") or {}
    incident = result.get("incident")
    mitre = result.get("mitre")
    action = result.get("response_action")

    print()
    print("===== RESUMEN =====")
    print(
        "Evento:",
        event.get("event_type")
    )
    print(
        "Severidad:",
        analysis.get("risk_level")
    )
    print(
        "Detectado:",
        analysis.get("detected")
    )
    print(
        "Scope:",
        analysis.get("scope")
    )

    if incident:
        print(
            "✅ Incidente:",
            incident.get("id")
        )
    else:
        print(
            "ℹ️ Sin incidente"
        )

    if mitre:
        print(
            "✅ MITRE:",
            mitre.get("technique_id"),
            "-",
            mitre.get("technique_name")
        )
    else:
        print(
            "ℹ️ Sin MITRE automático"
        )

    if action:
        print(
            "🛡️ Acción:",
            action.get("action_type"),
            "->",
            action.get("target")
        )

        incident_id = incident.get("id")

        print()
        print(
            "Esperando resultado defensivo..."
        )

        for _ in range(10):
            time.sleep(1)

            actions = get_json(
                f"{API}/response-actions?"
                f"incident_id={incident_id}"
            )

            if not actions:
                continue

            current = actions[0]

            print(
                "Estado:",
                current.get("status")
            )

            if current.get("status") in (
                "executed",
                "failed",
                "rolled_back",
            ):
                show(
                    "RESPUESTA DEFENSIVA",
                    current
                )
                break

    print()
    print("✅ Escenario terminado.")


if __name__ == "__main__":
    main()
