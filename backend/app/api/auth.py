from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import register_user, login_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    result = register_user(
        db=db,
        name=data.name,
        email=data.email,
        password=data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    result = login_user(
        db=db,
        email=data.email,
        password=data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail=result["message"]
        )

    return result