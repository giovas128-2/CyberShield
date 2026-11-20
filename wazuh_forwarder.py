"""Reenvío de alertas Wazuh a CyberShield con cursor persistente.

Inicio sin cursor: comienza al FINAL del archivo (no reenvía históricos).
Confirma el desplazamiento sólo después de un POST HTTP 2xx.
No ejecuta acciones defensivas ni modifica la configuración de Wazuh.
"""
import json
import logging
import os
import time
from pathlib import Path

import requests
from cybershield_service_client import get_service_headers

WAZUH_ALERTS = Path("/var/ossec/logs/alerts/alerts.json")
API_URL = "http://127.0.0.1:8000/integrations/wazuh?server_id=1"
CURSOR_FILE = Path(os.getenv(
    "CYBERSHIELD_WAZUH_CURSOR",
    "/var/lib/cybershield/wazuh-forwarder.cursor.json",
))
POLL_SECONDS = 0.5
RETRY_SECONDS = 5
LOG = logging.getLogger("cybershield.wazuh_forwarder")


def is_relevant_event(event):
    rule = event.get("rule") or {}
    decoder = event.get("decoder") or {}
    syscheck = event.get("syscheck") or {}
    rule_id = str(rule.get("id") or "")
    mitre_ids = (rule.get("mitre") or {}).get("id") or []

    is_fim = bool(syscheck) or decoder.get("name") == "syscheck_integrity_changed"
    if is_fim:
        filename = str(syscheck.get("path") or "").rsplit("/", 1)[-1].lower()
        if filename == ".cybershield_lockdown" or filename.startswith(".ransomware_demo"):
            is_fim = False

    return (
        rule_id in ("5763", "5402", "100210")
        or is_fim
        or "T1548.003" in mitre_ids
        or "T1021.004" in mitre_ids
    )


def load_cursor(path=CURSOR_FILE):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if (
            isinstance(data, dict)
            and isinstance(data.get("device"), int)
            and isinstance(data.get("inode"), int)
            and isinstance(data.get("offset"), int)
            and data["offset"] >= 0
        ):
            return data
    except FileNotFoundError:
        return None
    except (ValueError, OSError, TypeError):
        LOG.exception("Cursor inválido o inaccesible; se detiene para evitar reprocesamiento")
        raise
    raise ValueError("Cursor inválido: %s" % path)


def save_cursor(cursor, path=CURSOR_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as file:
            os.fchmod(file.fileno(), 0o600)
            json.dump(cursor, file, sort_keys=True)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        # Asegurar durabilidad también del rename.
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def cursor_for(file):
    st = os.fstat(file.fileno())
    return {"device": st.st_dev, "inode": st.st_ino, "offset": file.tell()}


def send_event(event, session, headers):
    response = session.post(API_URL, json=event, headers=headers, timeout=10)
    response.raise_for_status()
    LOG.info("Wazuh reenviado: regla=%s HTTP=%s",
             (event.get("rule") or {}).get("id"), response.status_code)


def follow_alerts(path=WAZUH_ALERTS, cursor_path=CURSOR_FILE,
                  session=None, stop=None, sleep=time.sleep):
    """Sigue el archivo y su rotación. stop() opcional para pruebas."""
    session = session or requests.Session()
    headers = get_service_headers()  # Si no hay clave, no consumir alertas.
    cursor = load_cursor(cursor_path)
    file = None
    try:
        while stop is None or not stop():
            if file is None:
                try:
                    file = path.open("rb")
                except FileNotFoundError:
                    LOG.warning("Wazuh aún no creó %s", path)
                    sleep(RETRY_SECONDS)
                    continue
                st = os.fstat(file.fileno())
                if cursor is None:
                    # Primera ejecución: no recrear incidentes históricos.
                    file.seek(0, os.SEEK_END)
                    cursor = cursor_for(file)
                    save_cursor(cursor, cursor_path)
                    LOG.info("Primer inicio: cursor al final; offset=%s", cursor["offset"])
                elif (cursor["device"], cursor["inode"]) == (st.st_dev, st.st_ino):
                    if cursor["offset"] > st.st_size:
                        LOG.warning("Archivo truncado: reinicio de cursor a 0")
                        file.seek(0)
                    else:
                        file.seek(cursor["offset"])
                else:
                    LOG.warning("Archivo rotado mientras el forwarder estaba parado; "
                                "se empieza al final del archivo nuevo, sin históricos")
                    file.seek(0, os.SEEK_END)
                cursor = cursor_for(file)
                save_cursor(cursor, cursor_path)

            start = file.tell()
            line = file.readline()
            if line and line.endswith(b"\n"):
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("La alerta no es un objeto JSON")
                except (UnicodeDecodeError, ValueError):
                    LOG.warning("Alerta inválida en offset %s; se omite", start)
                    save_cursor(cursor_for(file), cursor_path)
                    continue

                if is_relevant_event(event):
                    try:
                        send_event(event, session, headers)
                    except requests.RequestException as exc:
                        LOG.error("Error HTTP Wazuh (sin avanzar cursor): %s", exc)
                        file.seek(start)
                        sleep(RETRY_SECONDS)
                        continue

                save_cursor(cursor_for(file), cursor_path)
                continue

            if line:
                # Línea parcial: nunca confirmar ni enviar JSON incompleto.
                file.seek(start)

            try:
                current = path.stat()
            except FileNotFoundError:
                current = None

            old = os.fstat(file.fileno())
            if current and (
                current.st_dev == old.st_dev
                and current.st_ino == old.st_ino
                and current.st_size < file.tell()
            ):
                LOG.warning("Truncado en ejecución: se reanuda desde offset 0")
                file.seek(0)
                save_cursor(cursor_for(file), cursor_path)
                continue
            if current and (current.st_dev, current.st_ino) != (old.st_dev, old.st_ino):
                # Se agotó el archivo anterior; abrir el rotado.
                file.close()
                file = None
                # El nuevo archivo se lee desde 0 si hubo rotación
                # mientras el proceso estaba activo.
                with path.open("rb") as new_file:
                    new_cursor = cursor_for(new_file)
                cursor = new_cursor
                save_cursor(cursor, cursor_path)
                LOG.info("Rotación detectada; nuevo archivo desde offset 0")
                continue

            sleep(POLL_SECONDS)
    finally:
        if file is not None:
            file.close()
        session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    LOG.info("CyberShield Wazuh Forwarder iniciado; modo lectura de alertas")
    follow_alerts()
