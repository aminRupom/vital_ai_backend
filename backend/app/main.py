from fastapi import FastAPI

from app.config import settings
from app.routes import auth, consent, health, intake, llm, routing, triage

app = FastAPI(
    title=f"{settings.app_name} — Phase One API",
    description=(
        "Backend for administrative intake, consent, triage, and routing. "
    ),
    version=settings.app_version,
)

# Public
app.include_router(health.router)

# Authenticated
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(intake.router, prefix=API_PREFIX)
app.include_router(consent.router, prefix=API_PREFIX)
app.include_router(triage.router, prefix=API_PREFIX)
app.include_router(routing.router, prefix=API_PREFIX)
app.include_router(llm.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
