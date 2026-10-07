import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "CyberShield")
APP_ENV = os.getenv("APP_ENV", "development")

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-secret-key"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
)


FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)