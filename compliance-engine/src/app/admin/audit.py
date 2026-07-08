"""Administrator audit logging."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import AdminSession
from app.storage.db import AdminAuditRecord

logger = logging.getLogger(__name__)


async def record_admin_event(
    session: AsyncSession,
    *,
    event_type: str,
    status: str,
    request: Request,
    admin: AdminSession | None = None,
    username: str | None = None,
    detail: str | None = None,
) -> None:
    """Persist an administrator audit event."""
    try:
        event = AdminAuditRecord(
            id=uuid.uuid4().hex,
            event_type=event_type,
            admin_username=admin.username if admin else username,
            admin_role=admin.role if admin else None,
            status=status,
            request_id=getattr(request.state, "request_id", None),
            client_ip=request.client.host if request.client else None,
            detail=detail,
            created_at=datetime.now(UTC),
        )
        session.add(event)
        await session.flush()
    except Exception:
        logger.warning("failed_to_record_admin_audit_event", exc_info=True)


async def recent_admin_events(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict[str, str | None]]:
    """Return recent administrator audit events for the dashboard."""
    query = select(AdminAuditRecord).order_by(AdminAuditRecord.created_at.desc()).limit(limit)
    try:
        result = await session.execute(query)
    except Exception:
        return []

    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "admin_username": event.admin_username,
            "admin_role": event.admin_role,
            "status": event.status,
            "request_id": event.request_id,
            "client_ip": event.client_ip,
            "detail": event.detail,
            "created_at": event.created_at.isoformat(),
        }
        for event in result.scalars().all()
    ]
