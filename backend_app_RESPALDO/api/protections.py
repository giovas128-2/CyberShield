from fastapi import APIRouter

router = APIRouter(
    prefix="/protections",
    tags=["Protections"],
)


@router.get("")
def list_protections():
    return [
        {
            "id": "c1",
            "name": "Fuerza bruta",
            "sensor": "Wazuh",
            "description": "Monitoreo con respuesta segura y reversible en el laboratorio.",
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
            "id": "c2",
            "name": "Dispositivo no autorizado",
            "sensor": "Aplicación",
            "description": "Device Trust validado con backend, PostgreSQL y frontend.",
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
            "id": "c3",
            "name": "Cambio de archivo crítico",
            "sensor": "Wazuh FIM",
            "description": "Detección FIM validada de extremo a extremo en el laboratorio.",
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
            "id": "c4",
            "name": "Abuso de privilegios",
            "sensor": "Wazuh",
            "description": "Caso validado mediante evento controlado de elevación de privilegios.",
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
            "id": "c5",
            "name": "Conexión externa sospechosa",
            "sensor": "Suricata",
            "description": "Telemetría y alerta real de Suricata integradas con FastAPI y PostgreSQL.",
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
            "id": "c6",
            "name": "Posible exfiltración de datos",
            "sensor": "Suricata + App",
            "description": "Escenario defensivo con datos ficticios; no implica exfiltración confirmada.",
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
            "id": "c7",
            "name": "Comportamiento tipo ransomware",
            "sensor": "Wazuh",
            "description": "Patrón benigno de modificaciones masivas; no utiliza malware ni cifrado real.",
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
            "id": "c8",
            "name": "Posible movimiento lateral",
            "sensor": "Wazuh + Suricata",
            "description": "Conexión SSH autorizada entre hosts del laboratorio; clasificación contextual.",
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