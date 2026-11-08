
import os
import secrets

from fastapi import Header, HTTPException, status
from dotenv import load_dotenv
from pathlib import Path

# Cargar el .env del backend
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


def require_service_key(
    x_cybershield_service_key: str | None = Header(default=None),
):
    expected_key = os.getenv("CYBERSHIELD_SERVICE_KEY", "")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticación de servicios no configurada",
        )

    if not x_cybershield_service_key or not secrets.compare_digest(
        x_cybershield_service_key,
        expected_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de servicio inválida",
        )

    return True
