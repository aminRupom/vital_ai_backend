import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import Response

from app.config import settings
from app.limiter import limiter
from app.routes import auth, consent, health, intake, llm, routing, triage

logger = logging.getLogger(__name__)

app = FastAPI(
    title=f"{settings.app_name} — Phase One API",
    description=("Backend for administrative intake, consent, triage, and routing. "),
    version=settings.app_version,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid4())
    request.state.request_id = request_id
    logger.info("request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

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
