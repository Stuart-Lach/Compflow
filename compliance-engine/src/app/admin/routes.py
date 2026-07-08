"""Administrator dashboard routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.alerts import deliver_alerts, send_test_alert
from app.admin.audit import record_admin_event
from app.admin.monitoring import build_admin_overview
from app.admin.security import (
    ADMIN_COOKIE_NAME,
    AdminSession,
    create_admin_session_token,
    get_admin_session,
    require_admin_operator_session,
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
async def admin_login(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
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
        await record_admin_event(
            session,
            event_type="admin_login",
            status="failed",
            request=request,
            username=username or None,
            detail="invalid_credentials",
        )
        return HTMLResponse(
            login_page("Invalid administrator username or password."),
            status_code=401,
        )

    role = settings.admin_user_configs[username]["role"]
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
    await record_admin_event(
        session,
        event_type="admin_login",
        status="success",
        request=request,
        admin=AdminSession(
            username=username,
            role=role,
            expires_at=0,
        ),
    )
    return response


@router.post("/admin/logout")
async def admin_logout(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Clear the administrator session cookie."""
    admin = get_admin_session(request)
    if admin is not None:
        await record_admin_event(
            session,
            event_type="admin_logout",
            status="success",
            request=request,
            admin=admin,
        )
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
    admin: Annotated[AdminSession, Depends(require_admin_session)],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Return system monitoring information for the administrator dashboard."""
    overview = await build_admin_overview(session)
    delivery_result = await deliver_alerts(
        overview["alerts"],
        trigger="dashboard_overview",
        admin_username=admin.username,
    )
    overview["session"] = {"username": admin.username, "role": admin.role}
    overview["alert_delivery"] = {
        "status": delivery_result.status,
        "delivered": delivery_result.delivered,
        "suppressed": delivery_result.suppressed,
        "detail": delivery_result.detail,
    }
    return overview


@router.get("/admin/api/maintenance/readiness")
async def admin_readiness(
    request: Request,
    admin: Annotated[AdminSession, Depends(require_admin_operator_session)],
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
    await record_admin_event(
        session,
        event_type="maintenance_readiness_check",
        status="success" if ready else "not_ready",
        request=request,
        admin=admin,
        detail=json_detail(checks),
    )
    return JSONResponse(
        status_code=200,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )


@router.post("/admin/api/maintenance/rate-limit/reset")
async def admin_reset_rate_limit(
    request: Request,
    admin: Annotated[AdminSession, Depends(require_admin_operator_session)],
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Reset in-process API rate-limit counters."""
    reset_rate_limiter()
    await record_admin_event(
        session,
        event_type="maintenance_rate_limit_reset",
        status="success",
        request=request,
        admin=admin,
    )
    return {"status": "ok", "message": "Rate limiter counters reset"}


@router.post("/admin/api/maintenance/alerts/test")
async def admin_test_alert(
    request: Request,
    admin: Annotated[AdminSession, Depends(require_admin_operator_session)],
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | int | None]:
    """Send a test alert through the configured production alert webhook."""
    result = await send_test_alert(admin_username=admin.username)
    await record_admin_event(
        session,
        event_type="maintenance_alert_test",
        status=result.status,
        request=request,
        admin=admin,
        detail=result.detail,
    )
    return {
        "status": result.status,
        "delivered": result.delivered,
        "suppressed": result.suppressed,
        "detail": result.detail,
    }


def json_detail(value: dict[str, str]) -> str:
    """Create compact JSON detail text for audit records."""
    import json

    return json.dumps(value, separators=(",", ":"), sort_keys=True)
