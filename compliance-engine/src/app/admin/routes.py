"""Administrator dashboard routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.monitoring import build_admin_overview
from app.admin.security import (
    ADMIN_COOKIE_NAME,
    AdminSession,
    create_admin_session_token,
    get_admin_session,
    require_admin_session,
    verify_admin_credentials,
)
from app.admin.views import dashboard_page, login_page
from app.config import settings
from app.rulesets.registry import get_current_ruleset
from app.security import reset_rate_limiter
from app.storage.db import get_session

router = APIRouter(include_in_schema=False)


@router.get("/admin")
async def admin_root(request: Request) -> RedirectResponse:
    """Send administrators to the console or login page."""
    destination = "/admin/dashboard" if get_admin_session(request) else "/admin/login"
    return RedirectResponse(destination, status_code=303)


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request) -> Response:
    """Render the administrator login form."""
    if get_admin_session(request):
        return RedirectResponse("/admin/dashboard", status_code=303)
    return HTMLResponse(login_page())


@router.post("/admin/login")
async def admin_login(request: Request) -> Response:
    """Authenticate an administrator and establish a secure session cookie."""
    form = await request.form()
    username = str(form.get("username") or "")
    password = str(form.get("password") or "")

    if not settings.admin_dashboard_configured:
        return HTMLResponse(
            login_page("Administrator login is not configured."),
            status_code=503,
        )

    if not verify_admin_credentials(username, password):
        return HTMLResponse(
            login_page("Invalid administrator username or password."),
            status_code=401,
        )

    response = RedirectResponse("/admin/dashboard", status_code=303)
    response.set_cookie(
        ADMIN_COOKIE_NAME,
        create_admin_session_token(username),
        max_age=settings.ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        secure=settings.ADMIN_COOKIE_SECURE,
        samesite="strict",
        path="/admin",
    )
    return response


@router.post("/admin/logout")
async def admin_logout() -> RedirectResponse:
    """Clear the administrator session cookie."""
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(ADMIN_COOKIE_NAME, path="/admin")
    return response


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> Response:
    """Render the protected desktop operations console."""
    if not get_admin_session(request):
        return RedirectResponse("/admin/login", status_code=303)
    return HTMLResponse(dashboard_page())


@router.get("/admin/api/overview")
async def admin_overview(
    _admin: Annotated[AdminSession, Depends(require_admin_session)],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Return system monitoring information for the administrator dashboard."""
    return await build_admin_overview(session)


@router.get("/admin/api/maintenance/readiness")
async def admin_readiness(
    _admin: Annotated[AdminSession, Depends(require_admin_session)],
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Run a readiness check from the admin console."""
    checks: dict[str, str] = {}
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    try:
        checks["ruleset"] = get_current_ruleset().ruleset_version_id
    except Exception:
        checks["ruleset"] = "unavailable"

    ready = checks["database"] == "ok" and checks["ruleset"] != "unavailable"
    return JSONResponse(
        status_code=200,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )


@router.post("/admin/api/maintenance/rate-limit/reset")
async def admin_reset_rate_limit(
    _admin: Annotated[AdminSession, Depends(require_admin_session)],
) -> dict[str, str]:
    """Reset in-process API rate-limit counters."""
    reset_rate_limiter()
    return {"status": "ok", "message": "Rate limiter counters reset"}
