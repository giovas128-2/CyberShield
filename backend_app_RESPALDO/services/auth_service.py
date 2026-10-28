from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, verify_password


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str
):
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        return {
            "success": False,
            "message": "El correo ya está registrado"
        }

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password)
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Usuario registrado correctamente",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }


def login_user(
    db: Session,
    email: str,
    password: str
):
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        return {
            "success": False,
            "message": "Correo o contraseña incorrectos"
        }

    try:
        password_is_valid = verify_password(
            password,
            user.password_hash
        )
    except Exception:
        password_is_valid = False

    if not password_is_valid:
        return {
            "success": False,
            "message": "Correo o contraseña incorrectos"
        }

    return {
        "success": True,
        "message": "Inicio de sesión correcto",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }