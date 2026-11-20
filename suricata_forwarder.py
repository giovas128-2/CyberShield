"""Suricata EVE forwarder con cursor persistente y entrega al menos una vez.

No ejecuta ataques ni respuestas. En primer inicio arranca al EOF para no
recrear incidentes históricos. Solo envía los eventos que antes eran relevantes.
"""
import json
import logging
import os
import time
from pathlib import Path

import httpx
from cybershield_service_client import get_service_headers

LOG = logging.getLogger(__name__)
EVE_FILE = Path(os.environ.get("CYBERSHIELD_SURICATA_EVE", "/var/log/suricata/eve.json"))
CURSOR_FILE = Path(os.environ.get(
    "CYBERSHIELD_SURICATA_CURSOR",
    "/var/lib/cybershield/suricata-forwarder.cursor.json",
))
API_URL = "http://127.0.0.1:8000/integrations/suricata?server_id=2"
POLL_SECONDS = 0.5
RETRY_SECONDS = 5


def relevant(event):
    event_type = event.get("event_type")
    alert = event.get("alert") or {}
    flow = event.get("flow") or {}
    try:
        dest_port = int(event.get("dest_port") or 0)
        sid = int(alert.get("signature_id") or 0)
        bytes_up = int(flow.get("bytes_toserver") or 0)
    except (TypeError, ValueError):
        return False

    lab_exfil = (
        event_type == "alert" and sid == 1000002
        and event.get("dest_ip") == "172.25.176.1" and dest_port == 8765
    )
    sc5 = event_type == "alert" and sid == 1000003
    lab_flow = (
        event_type == "flow" and event.get("dest_ip") == "172.25.176.1"
        and dest_port == 8765 and bytes_up >= 10_000_000
    )
    return lab_exfil or sc5 or lab_flow


def cursor_for(file):
    stat = os.fstat(file.fileno())
    return {"device": stat.st_dev, "inode": stat.st_ino, "offset": file.tell()}


def load_cursor(path=CURSOR_FILE):
    try:
        cursor = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if (
        not isinstance(cursor, dict)
        or not all(isinstance(cursor.get(k), int) for k in ("device", "inode", "offset"))
        or cursor["offset"] < 0
    ):
        raise ValueError("Cursor Suricata inválido; no se hará replay")
    return cursor


def save_cursor(cursor, path=CURSOR_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(cursor, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)


def send_event(event, client, headers):
    response = client.post(API_URL, json=event, headers=headers, timeout=10.0)
    response.raise_for_status()
    LOG.info("Suricata entregado: event_type=%s sid=%s status=%s duplicate=%s",
             event.get("event_type"), (event.get("alert") or {}).get("signature_id"),
             response.status_code, response.json().get("duplicate", False))


def follow_eve(
    path=EVE_FILE, cursor_path=CURSOR_FILE,
    client=None, stop=None, sleep=time.sleep,
):
    """Avanza el cursor solo tras un HTTP 2xx o un evento no relevante.

    Rotación mientras se ejecuta: termina el archivo anterior y abre el nuevo
    desde inicio. Rotación mientras estaba apagado: evita replay y avisa.
    """
    client = client or httpx.Client()
    try:
        headers = get_service_headers()
        cursor = load_cursor(cursor_path)
        file = None
        while stop is None or not stop():
            if file is None:
                try:
                    file = path.open("rb")
                except FileNotFoundError:
                    LOG.warning("EVE no existe todavía: %s", path)
                    sleep(RETRY_SECONDS)
                    continue
                stat = os.fstat(file.fileno())
                if cursor is None:
                    file.seek(0, os.SEEK_END)
                    LOG.warning("Primera ejecución: omitiendo historial; offset=%s", file.tell())
                elif (stat.st_dev, stat.st_ino) != (cursor["device"], cursor["inode"]):
                    file.seek(0, os.SEEK_END)
                    LOG.warning("EVE rotó mientras estaba apagado: se omite historial del nuevo archivo")
                elif cursor["offset"] > stat.st_size:
                    file.seek(0, os.SEEK_END)
                    LOG.warning("EVE truncado fuera de ejecución; evitando replay del histórico")
                else:
                    file.seek(cursor["offset"])
                save_cursor(cursor_for(file), cursor_path)

            start = file.tell()
            line = file.readline()
            if line.endswith(b"\n"):
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("Not object")
                except (UnicodeDecodeError, ValueError):
                    LOG.warning("Línea EVE inválida: offset=%s", start)
                    save_cursor(cursor_for(file), cursor_path)
                    continue

                if relevant(event):
                    try:
                        send_event(event, client, headers)
                    except (httpx.HTTPError, ValueError) as exc:
                        LOG.error("Fallo de envío, se reintentará sin avanzar cursor: %s", exc)
                        file.seek(start)
                        sleep(RETRY_SECONDS)
                        continue

                save_cursor(cursor_for(file), cursor_path)
                continue

            if line:
                file.seek(start)  # JSON parcial no debe descartarse

            try:
                current = path.stat()
            except FileNotFoundError:
                current = None
            previous = os.fstat(file.fileno())
            if current and (current.st_dev, current.st_ino) != (
                previous.st_dev, previous.st_ino
            ):
                file.close()
                file = None
                # Importante: en rotación EN VIVO, iniciar nuevo archivo en offset 0.
                with path.open("rb") as new_file:
                    save_cursor(cursor_for(new_file), cursor_path)
                cursor = load_cursor(cursor_path)
                continue
            if current and current.st_size < start:
                LOG.warning("EVE truncado en ejecución: se omite contenido existente")
                file.close()
                file = None
                with path.open("rb") as new_file:
                    new_file.seek(0, os.SEEK_END)
                    save_cursor(cursor_for(new_file), cursor_path)
                cursor = load_cursor(cursor_path)
                continue
            sleep(POLL_SECONDS)
    finally:
        if "file" in locals() and file is not None:
            file.close()
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG.info("CyberShield Suricata Forwarder iniciado; sin replay histórico")
    follow_eve()
