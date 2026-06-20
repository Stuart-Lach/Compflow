"""
Compliance Engine - FastAPI Application

API-first payroll compliance engine for South Africa.
Validates and computes statutory payroll outputs (PAYE, UIF, SDL) before SARS submission.
"""

import logging
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.responses import Response

from app.api.v1 import routes_exports, routes_health, routes_rulesets, routes_runs
from app.config import settings
from app.logging_config import setup_logging
from app.rulesets.registry import get_current_ruleset
from app.storage.db import engine, init_db

audit_logger = logging.getLogger("app.audit")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.APP_NAME,
    description="API-first payroll compliance engine for South Africa",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def audit_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log request metadata without recording payroll payloads or API keys."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        audit_logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s "
            "duration_ms=%s company_id=%s key_fingerprint=%s client_ip=%s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            getattr(request.state, "company_id", None),
            getattr(request.state, "key_fingerprint", None),
            request.client.host if request.client else None,
        )


# Include routers
app.include_router(routes_health.router, prefix=settings.API_V1_PREFIX, tags=["Health"])
app.include_router(routes_rulesets.router, prefix=settings.API_V1_PREFIX, tags=["Rulesets"])
app.include_router(routes_runs.router, prefix=settings.API_V1_PREFIX, tags=["Runs"])
app.include_router(routes_exports.router, prefix=settings.API_V1_PREFIX, tags=["Exports"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Render-compatible health endpoint."""
    return {"status": "ok"}


@app.get("/ready")
async def readiness() -> JSONResponse:
    """Verify database connectivity and a currently active statutory ruleset."""
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    try:
        checks["ruleset"] = get_current_ruleset().ruleset_version_id
    except Exception:
        checks["ruleset"] = "unavailable"

    ready = checks["database"] == "ok" and checks["ruleset"] != "unavailable"
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )
