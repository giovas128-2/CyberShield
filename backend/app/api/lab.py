from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.event import SecurityEventRequest
from app.services.event_service import process_security_event

router = APIRouter(
    prefix="/lab",
    tags=["Laboratory"],
)


@router.get("/scenarios")
def list_lab_scenarios():
    return [
        {
            "id": "sc1",
            "name": "Fuerza bruta",
            "control": "Fuerza bruta",
            "description": "Genera telemetría defensiva de prueba para validar detección, clasificación y respuesta.",
            "event_source": "Wazuh",
            "mode": "integrated",
            "mitre_techniques": [
                {
                    "technique_id": "T1110",
                    "technique_name": "Brute Force",
                    "tactic": "Credential Access",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc2",
            "name": "Dispositivo no autorizado",
            "control": "Dispositivo no autorizado",
            "description": "Valida de forma controlada la decisión de Device Trust ante un dispositivo no registrado.",
            "event_source": "Aplicación",
            "mode": "integrated",
            "mitre_techniques": [
                {
                    "technique_id": "T1078",
                    "technique_name": "Valid Accounts",
                    "tactic": "Defense Evasion",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc3",
            "name": "Cambio de archivo crítico",
            "control": "Cambio de archivo crítico",
            "description": "Valida una señal FIM controlada sobre archivos autorizados del laboratorio.",
            "event_source": "Wazuh FIM",
            "mode": "integrated",
            "mitre_techniques": [
                {
                    "technique_id": "T1565.001",
                    "technique_name": "Stored Data Manipulation",
                    "tactic": "Impact",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc4",
            "name": "Abuso de privilegios",
            "control": "Abuso de privilegios",
            "description": "Valida un evento controlado asociado al uso de privilegios elevados.",
            "event_source": "Wazuh",
            "mode": "integrated",
            "mitre_techniques": [
                {
                    "technique_id": "T1548.003",
                    "technique_name": "Sudo and Sudo Caching",
                    "tactic": "Privilege Escalation",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc5",
            "name": "Conexión externa sospechosa",
            "control": "Conexión externa sospechosa",
            "description": "Valida telemetría y alertas controladas provenientes de Suricata.",
            "event_source": "Suricata",
            "mode": "integrated",
            "mitre_techniques": [
                {
                    "technique_id": "T1041",
                    "technique_name": "Exfiltration Over C2 Channel",
                    "tactic": "Exfiltration",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc6",
            "name": "Posible exfiltración de datos",
            "control": "Posible exfiltración de datos",
            "description": "Escenario defensivo con datos ficticios; no realiza una exfiltración real.",
            "event_source": "Suricata + App",
            "mode": "simulated",
            "mitre_techniques": [
                {
                    "technique_id": "T1041",
                    "technique_name": "Exfiltration Over C2 Channel",
                    "tactic": "Exfiltration",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc7",
            "name": "Comportamiento tipo ransomware",
            "control": "Comportamiento tipo ransomware",
            "description": "Simulación benigna de múltiples modificaciones; no usa malware ni cifrado real.",
            "event_source": "Wazuh",
            "mode": "simulated",
            "mitre_techniques": [
                {
                    "technique_id": "T1486",
                    "technique_name": "Data Encrypted for Impact",
                    "tactic": "Impact",
                    "is_primary": True,
                }
            ],
        },
        {
            "id": "sc8",
            "name": "Posible movimiento lateral",
            "control": "Posible movimiento lateral",
            "description": "Escenario autorizado de laboratorio basado en una conexión SSH controlada.",
            "event_source": "Wazuh + Suricata",
            "mode": "simulated",
            "mitre_techniques": [
                {
                    "technique_id": "T1021.004",
                    "technique_name": "Remote Services: SSH",
                    "tactic": "Lateral Movement",
                    "is_primary": True,
                }
            ],
        },
    ]
@router.post("/scenarios/{scenario_id}/run")
def run_lab_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
):
    if scenario_id == "sc1":
        event = SecurityEventRequest(
            event_type="multiple_login_attempts",
            source="lab",
            source_ip="192.168.56.50",
            server_id=2,
            description=(
                "Simulación controlada de múltiples "
                "intentos de autenticación"
            ),
            details={
                "attempts": 12,
                "time_window_seconds": 60,
                "distinct_users": 3,
                "successful_login": False,
                "simulation": True,
                "lab_scenario": "sc1",
            },
        )
    elif scenario_id == "sc2":
        event = SecurityEventRequest(
            event_type="unauthorized_device_access",
            source="lab",
            source_ip="127.0.0.1",
            server_id=2,
            description=(
                "Simulación controlada de acceso desde "
                "dispositivo no registrado"
            ),
            scope="BLOCKED",
            details={
                "auth_result": "success",
                "device_state": "unregistered",
                "simulation": True,
                "lab_scenario": "sc2",
            },
        )
    elif scenario_id == "sc3":
        event = SecurityEventRequest(
            event_type="suspicious_file_change",
            source="lab",
            source_ip="127.0.0.1",
            server_id=2,
            description=(
                "Simulación controlada de cambio no autorizado "
                "en archivo crítico"
            ),
            scope="IMPACT",
            details={
                "authorized": False,
                "file_criticality": "critical",
                "change_applied": True,
                "compromise_confirmed": False,
                "simulation": True,
                "lab_scenario": "sc3",
            },
        )
    elif scenario_id == "sc4":
        event = SecurityEventRequest(
            event_type="privilege_escalation",
            source="lab",
            source_ip="127.0.0.1",
            server_id=2,
            description=(
                "Simulación controlada de abuso de "
                "privilegios en laboratorio"
            ),
            scope="IMPACT",
            details={
                "sudo_used": True,
                "authorized": False,
                "success": True,
                "compromise_confirmed": False,
                "lab_scenario": "sc4",
                "simulation": True,
            },
        )
    elif scenario_id == "sc5":
        event = SecurityEventRequest(
            event_type="unusual_outbound_connection",
            source="lab",
            source_ip="172.25.181.143",
            server_id=2,
            description=(
                "Simulación controlada de conexión "
                "saliente sospechosa"
            ),
            scope="REACHED",
            details={
                "requests": 120,
                "time_window_seconds": 60,
                "destination_allowed": False,
                "impact_confirmed": False,
                "simulation": True,
                "lab_scenario": "sc5",
            },
        )
    elif scenario_id == "sc6":
        event = SecurityEventRequest(
            event_type="possible_data_exfiltration",
            source="lab",
            source_ip="172.25.181.143",
            server_id=2,
            description=(
                "Simulación controlada de posible "
                "exfiltración de datos"
            ),
            scope="REACHED",
            details={
                "bytes_toserver_total": 60_000_000,
                "bytes_toclient_total": 5_000_000,
                "dest_class": "external",
                "bulk_data_access": True,
                "prior_open_incident": False,
                "untrusted_session_device": False,
                "off_hours": False,
                "simulation": True,
                "lab_scenario": "sc6",
            },
        )
    elif scenario_id == "sc7":
        event = SecurityEventRequest(
            event_type="possible_ransomware_behavior",
            source="lab",
            source_ip="127.0.0.1",
            server_id=2,
            description=(
                "Simulación controlada de comportamiento "
                "tipo ransomware"
            ),
            scope="IMPACT",
            details={
                "modified_files": 60,
                "renamed_files": 20,
                "suspicious_extension": True,
                "maintenance_mode": False,
                "simulation": True,
                "lab_scenario": "sc7",
            },
        )
    elif scenario_id == "sc8":
        event = SecurityEventRequest(
            event_type="possible_lateral_movement",
            source="lab",
            source_ip="100.125.119.56",
            server_id=2,
            description=(
                "Simulación controlada de posible "
                "movimiento lateral"
            ),
            scope="REACHED",
            details={
                "protocol": "ssh",
                "login_successful": True,
                "pair_authorized": False,
                "maintenance_mode": False,
                "prior_open_incident": False,
                "simulation": True,
                "lab_scenario": "sc8",
            },
        )
    else:
        raise HTTPException(
            status_code=501,
            detail=(
                "Este escenario todavía no tiene "
                "ejecución real implementada"
            ),
        )

    return process_security_event(
        db=db,
        data=event,
    )