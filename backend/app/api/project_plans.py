"""Bandeja persistente, aislada del catálogo de protecciones y de propuestas MITRE."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.services.intelligence.project_plan_store import (
    PlanConflict, PlanNotFound, PlanStoreMissing,
    create_plan, list_plans, get_plan, review_task,
)

router = APIRouter(
    prefix="/intelligence/project-plans",
    tags=["Project Security Plans"],
    dependencies=[Depends(get_current_user)],
)


class NewPlan(BaseModel):
    project_name: str = Field(min_length=1, max_length=100)
    recommendation_ids: list[str] = Field(min_length=1, max_length=12)


class TaskReview(BaseModel):
    status: Literal["under_review", "planned", "rejected"]
    notes: str = Field(min_length=10, max_length=2000)


def _unavailable(exc: PlanStoreMissing):
    raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project_plan(
    payload: NewPlan,
    db: Session = Depends(get_db),
    reviewer = Depends(require_roles("admin", "engineer")),
):
    try:
        return create_plan(
            db, reviewer.id, payload.project_name,
            payload.recommendation_ids,
        )
    except PlanStoreMissing as exc:
        _unavailable(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
def list_project_plans(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    try:
        return list_plans(db, page, size)
    except PlanStoreMissing as exc:
        _unavailable(exc)


@router.get("/{plan_id}")
def project_plan_detail(
    plan_id: int,
    db: Session = Depends(get_db),
    _reviewer = Depends(require_roles("admin", "engineer")),
):
    if plan_id < 1:
        raise HTTPException(status_code=422, detail="Plan inválido")
    try:
        return get_plan(db, plan_id)
    except PlanStoreMissing as exc:
        _unavailable(exc)
    except PlanNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{plan_id}/tasks/{task_id}/review")
def review_project_plan_task(
    plan_id: int,
    task_id: int,
    payload: TaskReview,
    db: Session = Depends(get_db),
    reviewer = Depends(require_roles("admin", "engineer")),
):
    if plan_id < 1 or task_id < 1:
        raise HTTPException(status_code=422, detail="Identificador inválido")
    try:
        return review_task(
            db, plan_id, task_id, reviewer.id,
            payload.status, payload.notes,
        )
    except PlanStoreMissing as exc:
        _unavailable(exc)
    except PlanNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PlanConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
