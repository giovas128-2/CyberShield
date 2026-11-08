
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(
    BASE_DIR / "backend" / ".env"
)


def get_service_headers() -> dict[str, str]:
    key = os.getenv(
        "CYBERSHIELD_SERVICE_KEY",
        ""
    ).strip()

    if not key:
        raise RuntimeError(
            "CYBERSHIELD_SERVICE_KEY no está configurada"
        )

    return {
        "X-CyberShield-Service-Key": key,
    }
