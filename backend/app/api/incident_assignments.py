from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_roles
from app.database.connection import get_db
from app.models.user import User


router = APIRouter(
    prefix="/incidents",
    tags=["Incident Assignments"],
)


def change_assignment(
    incident_id: int,
    action: str,
    db: Session,
    current_user: User,
):
    try:
        incident = db.execute(
            text("""
                SELECT id, status, assigned_to,
                       workflow_status
                FROM public.incidents
                WHERE id = :incident_id
                FOR UPDATE
            """),
            {"incident_id": incident_id},
        ).mappings().first()

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incidente no encontrado",
            )

        if incident["workflow_status"] is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Incidente histórico sin flujo inicializado"
                ),
            )

        if action == "claim":
            if incident["status"] == "resolved":
                raise HTTPException(
                    status_code=409,
                    detail="No se puede reclamar un incidente resuelto",
                )

            if (
                incident["assigned_to"] is not None
                or incident["workflow_status"] != "unassigned"
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Incidente no disponible para asignación",
                )

        elif action == "release":
            if incident["assigned_to"] != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="El incidente no está asignado a tu usuario",
                )

        result = db.execute(
            text("""
                SELECT *
                FROM public.cs_change_assignment(
                    :incident_id,
                    :user_id,
                    :action
                )
            """),
            {
                "incident_id": incident_id,
                "user_id": current_user.id,
                "action": action,
            },
        ).mappings().first()

        if result is None:
            raise HTTPException(
                status_code=409,
                detail="Transición de asignación no permitida",
            )

        response = dict(result)
        db.commit()
        return response

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflicto de integridad en la asignación",
        )

    except Exception:
        db.rollback()
        raise


@router.post("/{incident_id}/claim")
def claim_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("admin", "engineer")
    ),
):
    return change_assignment(
        incident_id, "claim", db, current_user
    )


@router.post("/{incident_id}/release")
def release_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("admin", "engineer")
    ),
):
    return change_assignment(
        incident_id, "release", db, current_user
    )
