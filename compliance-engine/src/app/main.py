"""
Compliance Engine - FastAPI Application

API-first payroll compliance engine for South Africa.
Validates and computes statutory payroll outputs (PAYE, UIF, SDL) before SARS submission.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import routes_health, routes_runs, routes_rulesets, routes_exports
from app.config import settings
from app.logging_config import setup_logging
from app.storage.db import init_db


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
    allow_headers=["Authorization", "Content-Type"],
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

