"""Reproduce decisiones T1110 contra eventos históricos, sin efectos secundarios.

Comando (desde la raíz del proyecto):
  PYTHONPATH=backend backend/venv-wsl/bin/python -m app.services.intelligence.replay_ssh_history --limit 10

Solo lectura: no se crean alertas, incidentes, acciones ni reglas firewall.
Las IP de origen NO se imprimen en consola.
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.intelligence.defensive_decision_engine import assess_from_database


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit debe estar entre 1 y 100")

    root = Path(__file__).resolve().parents[4]
    load_dotenv(root / "backend" / ".env", override=False)

    if not os.getenv("DATABASE_URL", "").strip():
        print("[DETENIDO] DATABASE_URL no configurada; sin cambios.", file=sys.stderr)
        return 2

    from app.database.connection import engine

    print("=== CYBERSHIELD 2.0 — REPLAY T1110 SOLO LECTURA ===")
    print("No se generan eventos ni se ejecutan defensas.")

    with engine.connect() as connection:
        # Barrera adicional: cualquier escritura accidental en esta transacción
        # fallará a nivel PostgreSQL.
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        with Session(bind=connection) as db:
            events = db.execute(text("""
                SELECT e.id, e.event_type, e.severity, e.source,
                       e.source_ip::text AS source_ip, e.details,
                       e.created_at,
                       (SELECT ra.status
                          FROM incidents i
                          JOIN response_actions ra ON ra.incident_id = i.id
                         WHERE i.event_id = e.id
                           AND ra.action_type = 'BLOCK_SOURCE_IP'
                         ORDER BY ra.id DESC LIMIT 1) AS previous_action_status
                  FROM events e
                 WHERE e.source = 'wazuh'
                   AND e.details ->> 'wazuh_rule_id' = '5763'
                 ORDER BY e.id DESC
                 LIMIT :limit
            """), {"limit": args.limit}).mappings().all()

            counts: dict[str, int] = {}
            for row in events:
                event = {
                    "event_type": row["event_type"],
                    "severity": row["severity"],
                    "source": row["source"],
                    "source_ip": row["source_ip"],
                    "details": row["details"] or {},
                }
                decision = assess_from_database(db, event)
                counts[decision.status] = counts.get(decision.status, 0) + 1
                print(
                    f"Evento #{row['id']} | "
                    f"decisión={decision.status} | "
                    f"propuesta={decision.recommended_action or 'ninguna'} | "
                    f"respuesta_histórica={row['previous_action_status'] or 'no_asociada'} | "
                    f"ejecutado_ahora={decision.executed}"
                )

            print("=== RESUMEN ===")
            print(f"Eventos examinados: {len(events)}")
            for status, count in sorted(counts.items()):
                print(f"{status}: {count}")
            print("Escrituras en PostgreSQL: 0")
            print("Acciones ejecutadas: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
