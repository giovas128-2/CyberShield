from app.api.servers import router as servers_router
from app.api.integrations import router as integrations_router
from app.api.events import router as events_router
from app.api.incidents import router as incidents_router
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CyberShield API",
    description="Backend principal del sistema CyberShield",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(events_router)
app.include_router(incidents_router)
app.include_router(integrations_router)
app.include_router(servers_router)

@app.get("/")
def root():
    return {
        "message": "CyberShield API funcionando"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CyberShield Backend"
    }