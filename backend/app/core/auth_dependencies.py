from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.jwt_security import verify_access_token
from app.core.service_auth import require_service_key
from app.database.connection import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = verify_access_token(credentials.credentials)

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_or_service(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        optional_bearer_scheme
    ),
    x_cybershield_service_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    # Los procesos automáticos usan su clave de servicio.
    if x_cybershield_service_key is not None:
        require_service_key(x_cybershield_service_key)
        return "service"

    # Los ingenieros utilizan su JWT.
    if credentials is not None:
        return get_current_user(
            credentials=credentials,
            db=db,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida",
        headers={"WWW-Authenticate": "Bearer"},
    )