import os

from dotenv import load_dotenv


load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "CyberShield",
)


APP_ENV = os.getenv(
    "APP_ENV",
    "development",
)


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-secret-key",
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)


# ============================================================
# TELEGRAM
# ============================================================
# Es opcional.
#
# Si no existe token o chat_id:
# CyberShield seguirá funcionando normalmente.
#
# NUNCA colocar el token real directamente en este archivo.
# NUNCA subirlo a GitHub, capturas, PDFs o ZIPs.
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "",
).strip()


TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    "",
).strip()