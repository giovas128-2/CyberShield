from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_roles
from app.database.connection import get_db

router = APIRouter(
    prefix="/protections",
    tags=["Protections"],
)


def builtin_protections():
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

# El catálogo persistente solo se habilita cuando se aplica la migración 007.
# Mantener los ocho controles históricos como respaldo de solo lectura protege
# las interfaces del laboratorio durante una actualización gradual.
CATALOG_TABLE = "cybershield_protection_catalog"


class ProtectionProposal(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=1000)
    sensor: str = Field(min_length=2, max_length=120)
    technique_id: str = Field(pattern=r"^T\d{4}(?:\.\d{3})?$")


def catalog_exists(db: Session) -> bool:
    return db.execute(
        text("SELECT to_regclass('public.cybershield_protection_catalog')")
    ).scalar_one() is not None


def read_catalog(db: Session):
    rows = db.execute(text("""
        SELECT control_id, name, sensor, description, mode,
               mitre_techniques, origin, execution_enabled,
               execution_verified
          FROM cybershield_protection_catalog
         ORDER BY sort_order, control_id
    """)).mappings().all()
    return [
        {
            "id": row["control_id"],
            "name": row["name"],
            "sensor": row["sensor"],
            "description": row["description"],
            "mode": row["mode"],
            "mitre_techniques": row["mitre_techniques"],
            "origin": row["origin"],
            "execution_enabled": row["execution_enabled"],
            "execution_verified": row["execution_verified"],
        }
        for row in rows
    ]


@router.get("")
def list_protections(db: Session = Depends(get_db)):
    if not catalog_exists(db):
        return builtin_protections()
    catalog = read_catalog(db)
    return catalog if catalog else builtin_protections()


@router.post(
    "/catalog",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "engineer"))],
)
def propose_protection(
    proposal: ProtectionProposal,
    db: Session = Depends(get_db),
):
    """Solo registra una propuesta pendiente. Nunca instala sensores ni defensas."""
    if not catalog_exists(db):
        raise HTTPException(
            status_code=503,
            detail="Aplica la migracion 007 antes de crear propuestas",
        )

    import json

    # No aceptamos parametros de modo ni comandos del cliente.
    mitre = [{
        "technique_id": proposal.technique_id,
        "technique_name": "Pendiente de validar",
        "tactic": "Pendiente de validar",
        "is_primary": True,
    }]
    row = db.execute(text("""
        INSERT INTO cybershield_protection_catalog
            (control_id, name, sensor, description, mode, origin,
             mitre_techniques, execution_enabled, execution_verified)
        VALUES
            ('proposal-' || replace(gen_random_uuid()::text, '-', ''),
             :name, :sensor, :description, 'pending', 'proposal',
             CAST(:mitre AS jsonb), FALSE, FALSE)
        RETURNING control_id
    """), {
        "name": proposal.name.strip(),
        "sensor": proposal.sensor.strip(),
        "description": proposal.description.strip(),
        "mitre": json.dumps(mitre),
    })
    control_id = row.scalar_one()
    db.commit()
    return {
        "id": control_id,
        "mode": "pending",
        "execution_enabled": False,
        "execution_verified": False,
        "message": "Propuesta registrada para validacion; no ejecuta defensas.",
    }
