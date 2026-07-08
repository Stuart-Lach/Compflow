"""Outbound operational alert delivery for administrators."""

import asyncio
import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertDeliveryResult:
    """Result for an outbound alert delivery attempt."""

    status: str
    delivered: int = 0
    suppressed: int = 0
    detail: str | None = None


class AlertDedupe:
    """Small in-process dedupe cache to prevent webhook floods."""

    def __init__(self) -> None:
        self._sent_at: dict[str, float] = {}

    def filter_new(self, alerts: list[dict[str, str]], window_seconds: int) -> list[dict[str, str]]:
        """Return alerts not sent inside the configured window."""
        now = time.monotonic()
        fresh_alerts: list[dict[str, str]] = []
        expired = [
            fingerprint
            for fingerprint, sent_at in self._sent_at.items()
            if now - sent_at >= window_seconds
        ]
        for fingerprint in expired:
            self._sent_at.pop(fingerprint, None)

        for alert in alerts:
            fingerprint = _fingerprint_alert(alert)
            if fingerprint in self._sent_at:
                continue
            self._sent_at[fingerprint] = now
            fresh_alerts.append(alert)

        return fresh_alerts

    def reset(self) -> None:
        """Reset dedupe state for tests and controlled maintenance."""
        self._sent_at.clear()


alert_dedupe = AlertDedupe()


async def deliver_alerts(
    alerts: list[dict[str, str]],
    *,
    trigger: str,
    admin_username: str | None = None,
    force: bool = False,
) -> AlertDeliveryResult:
    """Deliver configured operational alerts through the production webhook."""
    deliverable = [
        alert
        for alert in alerts
        if alert.get("severity") in settings.alert_severities_list
    ]
    if not deliverable:
        return AlertDeliveryResult(status="skipped", detail="No deliverable alert severities")

    if not settings.alert_delivery_configured:
        return AlertDeliveryResult(status="skipped", detail="ALERT_WEBHOOK_URL is not configured")

    if not force:
        fresh = alert_dedupe.filter_new(deliverable, settings.ALERT_DEDUP_WINDOW_SECONDS)
    else:
        fresh = deliverable

    suppressed = len(deliverable) - len(fresh)
    if not fresh:
        return AlertDeliveryResult(status="suppressed", suppressed=suppressed)

    payload = {
        "source": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "trigger": trigger,
        "admin_username": admin_username,
        "generated_at": datetime.now(UTC).isoformat(),
        "alerts": fresh,
    }

    try:
        await _post_webhook(payload)
    except Exception as exc:
        logger.warning("alert_webhook_delivery_failed", exc_info=True)
        return AlertDeliveryResult(
            status="failed",
            delivered=0,
            suppressed=suppressed,
            detail=str(exc),
        )

    return AlertDeliveryResult(
        status="delivered",
        delivered=len(fresh),
        suppressed=suppressed,
    )


async def send_test_alert(admin_username: str | None = None) -> AlertDeliveryResult:
    """Send a forced test alert to verify production alert routing."""
    return await deliver_alerts(
        [
            {
                "severity": "critical",
                "title": "Compflow production alert test",
                "message": "Administrator-triggered test alert from the Compflow console.",
            }
        ],
        trigger="admin_test",
        admin_username=admin_username,
        force=True,
    )


def reset_alert_dedupe() -> None:
    """Reset alert dedupe cache for tests."""
    alert_dedupe.reset()


async def _post_webhook(payload: dict[str, Any]) -> None:
    await asyncio.to_thread(_post_webhook_sync, payload)


def _post_webhook_sync(payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    request = urllib.request.Request(
        settings.ALERT_WEBHOOK_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": f"{settings.APP_NAME}/alerts",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.ALERT_WEBHOOK_TIMEOUT_SECONDS,
        ) as response:
            if response.status >= 400:
                raise RuntimeError(f"Alert webhook returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Alert webhook returned HTTP {exc.code}") from exc


def _fingerprint_alert(alert: dict[str, str]) -> str:
    normalized = json.dumps(
        {
            "severity": alert.get("severity"),
            "title": alert.get("title"),
            "message": alert.get("message"),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
