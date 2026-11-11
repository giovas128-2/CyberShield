#!/usr/bin/env python3

import socket
import subprocess
import sys
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from cybershield_service_client import get_service_headers

API = "http://127.0.0.1:8000"
SERVER_NAME = "srv-cyber-01"
SERVER_IP = "100.77.51.7"

# Comprobar que estamos en el servidor correcto.
if socket.gethostname() != SERVER_NAME:
    raise SystemExit(
        "Hostname diferente. No se envía heartbeat."
    )

# Comprobar que la IP del laboratorio sigue asignada.
result = subprocess.run(
    ["tailscale", "ip", "-4"],
    capture_output=True,
    text=True,
    check=True,
    timeout=8,
)

ips = result.stdout.strip().splitlines()

if SERVER_IP not in ips:
    raise SystemExit(
        "IP de Tailscale diferente o no disponible."
    )

with httpx.Client(timeout=10) as client:

    health = client.get(f"{API}/health")
    health.raise_for_status()

    if health.json().get("status") != "ok":
        raise RuntimeError("Backend no saludable.")

    response = client.post(
        f"{API}/servers/heartbeat",
        json={
            "name": SERVER_NAME,
            "ip_address": SERVER_IP,
            "agent": "suricata",
        },
        headers=get_service_headers(),
    )

    response.raise_for_status()

    print(
        "Heartbeat OK:",
        response.json()["server"]["last_seen"]
    )
