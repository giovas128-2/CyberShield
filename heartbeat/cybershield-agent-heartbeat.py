#!/usr/bin/env python3
"""CyberShield: heartbeat con token individual."""

import os
import socket
import sys
import time
from urllib.parse import urlsplit
from uuid import UUID

import httpx


def main():
    api = os.getenv(
        "CYBERSHIELD_AGENT_API",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    agent_id = os.getenv("CYBERSHIELD_AGENT_ID", "")
    token = os.getenv("CYBERSHIELD_AGENT_TOKEN", "")
    expected_host = os.getenv(
        "CYBERSHIELD_AGENT_HOSTNAME",
        "",
    )

    if expected_host and socket.gethostname() != expected_host:
        print("Hostname no autorizado. Heartbeat cancelado.")
        return 1

    try:
        agent_id = str(UUID(agent_id))
    except (ValueError, AttributeError):
        print("ID de agente no configurado o inválido.")
        return 1

    if not token:
        print("Token individual no configurado.")
        return 1

    parsed = urlsplit(api)

    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        print("URL de API inválida.")
        return 1

    local_hosts = {"127.0.0.1", "localhost", "::1"}

    if parsed.scheme not in ("http", "https"):
        print("Protocolo no admitido.")
        return 1

    if (
        parsed.scheme == "http"
        and parsed.hostname not in local_hosts
    ):
        print("HTTP remoto rechazado. Utiliza HTTPS.")
        return 1

    url = (
        f"{api}/api/v1/agents/"
        f"{agent_id}/heartbeat"
    )

    try:
        with httpx.Client(
            timeout=10,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        print("HTTP:", response.status_code)

        if response.status_code == 200:
            data = response.json()

            if data.get("heartbeat") != "accepted":
                print("Respuesta de heartbeat inesperada.")
                return 1

            print("Heartbeat individual: ACEPTADO")
            print("Servidor ID:", data.get("server_id"))
            print("Última conexión:", data.get("last_seen"))
            return 0

        if response.status_code == 401:
            print("Credencial rechazada o revocada.")
        elif response.status_code == 404:
            print("Endpoint o agente no encontrado.")
        else:
            print("Heartbeat rechazado por CyberShield.")

        return 1

    except httpx.HTTPError as exc:
        print(
            "Error de comunicación:",
            type(exc).__name__,
        )
        return 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--watch"]:
        print("CyberShield Agent: enviando heartbeat cada 30 segundos.")
        print("Para detener, pulsa Ctrl+C.")
        try:
            while True:
                main()
                time.sleep(30)
        except KeyboardInterrupt:
            print("Agente detenido.")
            sys.exit(0)
    elif not sys.argv[1:]:
        sys.exit(main())
    else:
        print("Uso: python cybershield-agent-heartbeat.py [--watch]")
        sys.exit(2)
