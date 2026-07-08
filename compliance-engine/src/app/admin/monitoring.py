"""Operational monitoring summaries for the administrator dashboard."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import recent_admin_events
from app.config import settings
from app.rulesets.registry import get_current_ruleset
from app.storage.db import IssueRecord, RunRecord


async def build_admin_overview(session: AsyncSession) -> dict[str, Any]:
    """Build a safe administrator overview without exposing payroll row contents."""
    generated_at = datetime.now(UTC)
    database_status = await _database_status(session)
    ruleset_status = _ruleset_status()

    total_runs = await _count_runs(session)
    completed_runs = await _count_runs(session, status="completed")
    failed_runs = await _count_runs(session, status="failed")
    failed_runs_24h = await _count_runs(
        session,
        status="failed",
        since=generated_at - timedelta(hours=24),
    )
    validation_errors = await _count_issues(session, severity="error")
    validation_warnings = await _count_issues(session, severity="warning")
    recent_runs = await _recent_runs(session)
    audit_events = await recent_admin_events(session)
    alerts = _build_alerts(
        database_status=database_status,
        ruleset_status=ruleset_status,
        failed_runs_24h=failed_runs_24h,
        validation_errors=validation_errors,
    )

    return {
        "admin_only": True,
        "generated_at": generated_at.isoformat(),
        "network": {
            "required": True,
            "mode": "online_admin_console",
            "message": "Administrator tools require an active network session.",
        },
        "system": {
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "database": database_status,
            "current_ruleset": ruleset_status,
            "file_storage_backend": settings.FILE_STORAGE_BACKEND,
            "api_prefix": settings.API_V1_PREFIX,
            "alert_delivery": "configured"
            if settings.alert_delivery_configured
            else "not_configured",
        },
        "metrics": {
            "runs_total": total_runs,
            "runs_completed": completed_runs,
            "runs_failed": failed_runs,
            "failed_runs_24h": failed_runs_24h,
            "validation_errors": validation_errors,
            "validation_warnings": validation_warnings,
        },
        "alerts": alerts,
        "recent_runs": recent_runs,
        "admin_audit_events": audit_events,
        "maintenance": {
            "readiness_endpoint": "/ready",
            "rate_limit_reset_endpoint": "/admin/api/maintenance/rate-limit/reset",
            "test_alert_endpoint": "/admin/api/maintenance/alerts/test",
        },
    }


async def _database_status(session: AsyncSession) -> str:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        return "unavailable"
    return "ok"


def _ruleset_status() -> str:
    try:
        return get_current_ruleset().ruleset_version_id
    except Exception:
        return "unavailable"


async def _count_runs(
    session: AsyncSession,
    status: str | None = None,
    since: datetime | None = None,
) -> int:
    query = select(func.count()).select_from(RunRecord)
    if status is not None:
        query = query.where(RunRecord.status == status)
    if since is not None:
        query = query.where(RunRecord.created_at >= since)

    try:
        return int((await session.execute(query)).scalar_one())
    except Exception:
        return 0


async def _count_issues(session: AsyncSession, severity: str) -> int:
    query = select(func.count()).select_from(IssueRecord).where(IssueRecord.severity == severity)
    try:
        return int((await session.execute(query)).scalar_one())
    except Exception:
        return 0


async def _recent_runs(session: AsyncSession) -> list[dict[str, Any]]:
    query = select(RunRecord).order_by(RunRecord.created_at.desc()).limit(10)
    try:
        result = await session.execute(query)
    except Exception:
        return []

    runs = list(result.scalars().all())
    if not runs:
        return []

    issue_counts = await _issue_counts_for_runs(session, [run.id for run in runs])
    return [
        {
            "run_id": run.id,
            "payroll_run_id": run.payroll_run_id,
            "company_id": run.company_id,
            "status": run.status,
            "tax_year": run.tax_year,
            "ruleset_version_used": run.ruleset_version_used,
            "created_at": run.created_at.isoformat(),
            "errors": issue_counts.get(run.id, {}).get("error", 0),
            "warnings": issue_counts.get(run.id, {}).get("warning", 0),
            "employee_count": run.employee_count or 0,
        }
        for run in runs
    ]


async def _issue_counts_for_runs(
    session: AsyncSession,
    run_ids: list[str],
) -> dict[str, dict[str, int]]:
    query = (
        select(IssueRecord.run_id, IssueRecord.severity, func.count())
        .where(IssueRecord.run_id.in_(run_ids))
        .group_by(IssueRecord.run_id, IssueRecord.severity)
    )
    try:
        result = await session.execute(query)
    except Exception:
        return {}

    counts: dict[str, dict[str, int]] = {}
    for run_id, severity, count in result.all():
        if not isinstance(run_id, str) or not isinstance(severity, str):
            continue
        counts.setdefault(run_id, {})[severity] = int(count)
    return counts


def _build_alerts(
    *,
    database_status: str,
    ruleset_status: str,
    failed_runs_24h: int,
    validation_errors: int,
) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []

    if database_status != "ok":
        alerts.append(
            {
                "severity": "critical",
                "title": "Database unavailable",
                "message": "The admin console cannot confirm database connectivity.",
            }
        )

    if ruleset_status == "unavailable":
        alerts.append(
            {
                "severity": "critical",
                "title": "Ruleset unavailable",
                "message": "No current statutory ruleset could be loaded.",
            }
        )

    if failed_runs_24h > 0:
        alerts.append(
            {
                "severity": "warning",
                "title": "Failed payroll runs",
                "message": f"{failed_runs_24h} run(s) failed in the last 24 hours.",
            }
        )

    if validation_errors > 0:
        alerts.append(
            {
                "severity": "warning",
                "title": "Validation errors detected",
                "message": f"{validation_errors} validation error(s) exist across stored runs.",
            }
        )

    if not settings.api_key_bindings:
        alerts.append(
            {
                "severity": "info",
                "title": "Company API keys not configured",
                "message": "Configure API_KEY_BINDINGS before exposing payroll endpoints.",
            }
        )

    if settings.APP_ENV != "production":
        alerts.append(
            {
                "severity": "info",
                "title": "Non-production environment",
                "message": f"The service is currently running in {settings.APP_ENV}.",
            }
        )

    if not settings.alert_delivery_configured:
        alerts.append(
            {
                "severity": "info",
                "title": "Alert delivery not configured",
                "message": "Set ALERT_WEBHOOK_URL before production cutover.",
            }
        )

    return alerts
