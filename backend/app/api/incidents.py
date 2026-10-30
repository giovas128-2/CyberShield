from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.incident import Incident
from app.models.event import Event
from app.models.incident_mitre import IncidentMitre
from app.models.response_action import ResponseAction
from app.schemas.incident import IncidentStatusUpdate
from app.cybersecurity.investigation import get_investigation_guide


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.get("")
def list_incidents(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Incident, Event)
        .join(
            Event,
            Event.id == Incident.event_id,
        )
        .order_by(Incident.id.desc())
        .all()
    )

    result = []

    for incident, event in rows:
        guide = get_investigation_guide(
            event.event_type
        )

        mitre = (
            db.query(IncidentMitre)
            .filter(
                IncidentMitre.incident_id
                == incident.id
            )
            .order_by(
                IncidentMitre.is_primary.desc(),
                IncidentMitre.id.asc(),
            )
            .first()
        )

        response_action = (
            db.query(ResponseAction)
            .filter(
                ResponseAction.incident_id
                == incident.id
            )
            .order_by(
                ResponseAction.id.desc()
            )
            .first()
        )

        result.append({
            "id": incident.id,
            "event_id": incident.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "source_ip": (
                str(event.source_ip)
                if event.source_ip
                else None
            ),
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,

            "mitre": {
                "id": mitre.id,
                "technique_id": mitre.technique_id,
                "technique_name": mitre.technique_name,
                "tactic": mitre.tactic,
                "reference_url": mitre.reference_url,
                "is_primary": mitre.is_primary,
                "notes": mitre.notes,
            }
            if mitre
            else None,

            "response_action": {
                "id": response_action.id,
                "action_type": response_action.action_type,
                "target": response_action.target,
                "status": response_action.status,
                "reversible": response_action.reversible,
                "duration_seconds": (
                    response_action.duration_seconds
                ),
                "reason": response_action.reason,
                "result": response_action.result,
                "created_at": response_action.created_at,
                "executed_at": response_action.executed_at,
                "rolled_back_at": (
                    response_action.rolled_back_at
                ),
            }
            if response_action
            else None,

            "recommendation": guide[
                "recommendation"
            ],

            "investigation_steps": guide[
                "investigation_steps"
            ],

            "resolution_criteria": guide[
                "resolution_criteria"
            ],
        })

    return result


@router.patch("/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incidente no encontrado",
        )

    incident.status = data.status

    try:
        db.commit()
        db.refresh(incident)

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": (
            "Estado del incidente actualizado"
        ),
        "incident": {
            "id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "status": incident.status,
            "created_at": incident.created_at,
        },
    }
@router.get("/{incident_id}/evidence")
def get_incident_evidence(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incidente no encontrado",
        )

    event = (
        db.query(Event)
        .filter(
            Event.id == incident.event_id
        )
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Evento asociado no encontrado",
        )

    mitre = (
        db.query(IncidentMitre)
        .filter(
            IncidentMitre.incident_id
            == incident.id
        )
        .order_by(
            IncidentMitre.is_primary.desc(),
            IncidentMitre.id.asc(),
        )
        .first()
    )

    response_action = (
        db.query(ResponseAction)
        .filter(
            ResponseAction.incident_id
            == incident.id
        )
        .order_by(
            ResponseAction.id.desc()
        )
        .first()
    )

    details = event.details or {}

    # =========================================================
    # ESTADO VISUAL PARA FRONTEND
    # =========================================================

    if incident.status == "resolved":
        evidence_status = "CONTAINED"

    elif incident.status == "escalated":
        evidence_status = "FAILED"

    elif (
        response_action
        and response_action.status
        in (
            "pending",
            "approved",
        )
    ):
        evidence_status = "RESPONDING"

    elif (
        response_action
        and response_action.status == "failed"
    ):
        evidence_status = "FAILED"

    else:
        evidence_status = "DETECTED"

    # =========================================================
    # TIMELINE
    # =========================================================

    timeline = [
        {
            "stage": "DETECTED",
            "timestamp": incident.created_at,
            "completed": True,
        }
    ]

    if response_action:
        timeline.append({
            "stage": "RESPONDING",
            "timestamp": response_action.created_at,
            "completed": True,
        })

        if response_action.status in (
            "executed",
            "rolled_back",
        ):
            timeline.append({
                "stage": "CONTAINED",
                "timestamp": (
                    response_action.executed_at
                    or response_action.created_at
                ),
                "completed": True,
            })

        elif response_action.status == "failed":
            timeline.append({
                "stage": "FAILED",
                "timestamp": (
                    response_action.executed_at
                    or response_action.created_at
                ),
                "completed": True,
            })

    # =========================================================
    # RESPUESTA DEFENSIVA
    # =========================================================

    response_payload = None

    if response_action:
        action_type = (
            response_action.action_type
        )

        target = str(
            response_action.target or ""
        )

        tool = "CyberShield"

        command_display = None
        verification_command = None
        rollback_command = None

        # -----------------------------------------------------
        # Fuerza bruta SSH
        # La ejecución real la realiza Wazuh Active Response.
        # -----------------------------------------------------
        if action_type == "BLOCK_SOURCE_IP":
            tool = (
                "Wazuh Active Response / firewall-drop"
            )

            command_display = (
                "Wazuh Active Response: "
                f"firewall-drop ADD {target}"
            )

            rollback_command = (
                "Wazuh Active Response: "
                f"firewall-drop DELETE {target}"
            )

        # -----------------------------------------------------
        # Abuso / escalación de privilegios
        # Bridge ejecutado con privilegios root.
        # -----------------------------------------------------
        elif action_type == "TEMPORARY_ACCOUNT_LOCK":
            tool = (
                "CyberShield Privilege Response Bridge"
            )

            command_display = (
                f"usermod -L {target}"
            )

            verification_command = (
                f"passwd -S {target}"
            )

        # -----------------------------------------------------
        # Movimiento lateral SSH
        # -----------------------------------------------------
        elif (
            action_type
            == "RESTRICT_LATERAL_COMMUNICATION"
        ):
            tool = (
                "CyberShield Lateral Response Bridge / iptables"
            )

            command_display = (
                "iptables -I INPUT 1 "
                f"-s {target} "
                "-p tcp --dport 22 -j DROP"
            )

            verification_command = (
                "iptables -C INPUT "
                f"-s {target} "
                "-p tcp --dport 22 -j DROP"
            )

            rollback_command = (
                "iptables -D INPUT "
                f"-s {target} "
                "-p tcp --dport 22 -j DROP"
            )

        # -----------------------------------------------------
        # Exfiltración de datos
        # -----------------------------------------------------
        elif action_type == "RESTRICT_DATA_FLOW":
            tool = (
                "CyberShield Exfil Response Bridge / iptables"
            )

            command_display = (
                "iptables -I OUTPUT 1 "
                f"-d {target} "
                "-p tcp --dport 8765 -j REJECT"
            )

            verification_command = (
                "iptables -C OUTPUT "
                f"-d {target} "
                "-p tcp --dport 8765 -j REJECT"
            )

            rollback_command = (
                "iptables -D OUTPUT "
                f"-d {target} "
                "-p tcp --dport 8765 -j REJECT"
            )

        # -----------------------------------------------------
        # Ransomware-like de laboratorio
        # No se inventa un comando shell:
        # la defensa real se ejecuta desde Python.
        # -----------------------------------------------------
        elif action_type == "CONTAIN_HOST":
            tool = (
                "CyberShield Lab Response Bridge / Python"
            )

            command_display = (
                "Python: os.kill("
                "PID verificado de ransomware_demo.py, "
                "signal.SIGTERM)"
            )

            verification_command = (
                "Python: verify_containment() "
                "y Path.chmod(mode & ~0o222) "
                "sobre ransomware-demo"
            )

        # -----------------------------------------------------
        # Construcción de terminal de evidencia
        # -----------------------------------------------------
        terminal_lines = []

        if command_display:
            terminal_lines.append({
                "kind": "command",
                "level": "INFO",
                "text": command_display,
            })

        if verification_command:
            terminal_lines.append({
                "kind": "command",
                "level": "INFO",
                "text": verification_command,
            })

        result_text = (
            response_action.result or ""
        )

        for result_line in result_text.splitlines():
            clean_line = result_line.strip()

            if not clean_line:
                continue

            is_rollback = (
                clean_line.startswith(
                    "ROLLBACK:"
                )
            )

            if (
                is_rollback
                and rollback_command
            ):
                terminal_lines.append({
                    "kind": "command",
                    "level": "INFO",
                    "text": rollback_command,
                })

            terminal_lines.append({
                "kind": "output",
                "level": (
                    "INFO"
                    if is_rollback
                    else (
                        "ERROR"
                        if response_action.status
                        == "failed"
                        else "OK"
                    )
                ),
                "text": clean_line,
            })

        response_payload = {
            "id": response_action.id,
            "action_type": action_type,
            "target": response_action.target,
            "status": response_action.status,
            "reversible": (
                response_action.reversible
            ),
            "duration_seconds": (
                response_action.duration_seconds
            ),
            "tool": tool,
            "command_display": (
                command_display
            ),
            "verification_command": (
                verification_command
            ),
            "rollback_command": (
                rollback_command
            ),
            "terminal_lines": (
                terminal_lines
            ),
            "reason": response_action.reason,
            "result": response_action.result,
            "created_at": (
                response_action.created_at
            ),
            "executed_at": (
                response_action.executed_at
            ),
            "rolled_back_at": (
                response_action.rolled_back_at
            ),
            "failure_reason": (
                response_action.result
                if response_action.status
                == "failed"
                else None
            ),
        }

    # =========================================================
    # RESPUESTA FINAL
    # =========================================================

    return {
        "incident_id": incident.id,
        "event_id": event.id,

        "status": evidence_status,
        "incident_status": incident.status,

        "severity": incident.severity,

        "event_type": event.event_type,
        "source": event.source,

        "source_ip": (
            str(event.source_ip)
            if event.source_ip
            else None
        ),

        "server_id": event.server_id,

        "description": event.description,

        "detection": {
            "rule_id": details.get(
                "wazuh_rule_id"
            ),
            "wazuh_level": details.get(
                "wazuh_level"
            ),
            "attempts": details.get(
                "attempts"
            ),
            "user": details.get(
                "destination_user",
                details.get("user"),
            ),
            "sensor_confirmed": any(
                bool(details.get(flag, False))
                for flag in (
                    "sensor_confirmed_bruteforce",
                    "sensor_confirmed_ransomware_like",
                    "sensor_confirmed_privilege",
                    "sensor_confirmed_lateral",
                    "sensor_confirmed_exfiltration",
                )
            ),
            "timestamp": (
                details.get(
                    "original_timestamp"
                )
                or event.created_at
            ),
        },

        "mitre": {
            "technique_id": (
                mitre.technique_id
            ),
            "technique_name": (
                mitre.technique_name
            ),
            "tactic": mitre.tactic,
            "reference_url": (
                mitre.reference_url
            ),
        }
        if mitre
        else None,

        "response": response_payload,

        "timeline": timeline,
    }