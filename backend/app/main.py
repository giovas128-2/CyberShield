from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.servers import router as servers_router
from app.api.integrations import router as integrations_router
from app.api.events import router as events_router
from app.api.incidents import router as incidents_router
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router
from app.api.notifications import router as notifications_router
from app.api.response_actions import router as response_actions_router
from app.api.device_trust import router as device_trust_router
from app.api.protections import router as protections_router
from app.api.lab import router as lab_router

from app.core.config import FRONTEND_URL
from app.database.connection import check_database_connection


app = FastAPI(
    title="CyberShield API",
    description="Backend principal del sistema CyberShield",
    version="0.3.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(events_router)
app.include_router(incidents_router)
app.include_router(integrations_router)
app.include_router(servers_router)
app.include_router(notifications_router)
app.include_router(response_actions_router)
app.include_router(device_trust_router)
app.include_router(protections_router)
app.include_router(lab_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "CyberShield API funcionando"
    }


# ============================================================
# HEALTH CHECK GENERAL
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CyberShield Backend",
        "version": "0.3.0",
    }


# ============================================================
# HEALTH CHECK BASE DE DATOS
# ============================================================

@app.get("/health/db")
def database_health():

    connected = check_database_connection()

    return {
        "status": "ok" if connected else "error",
        "database": (
            "connected"
            if connected
            else "unavailable"
        ),
    }