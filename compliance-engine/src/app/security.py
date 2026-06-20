"""Authentication dependencies for protected payroll endpoints."""

import hashlib
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Final

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    """Authenticated company identity derived from a configured API key."""

    company_id: str | None
    key_fingerprint: str


class FixedWindowRateLimiter:
    """Small in-process limiter suitable for a single staging service instance."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[float, int]] = {}

    def check(self, identity: str, limit: int, window_seconds: int) -> int | None:
        """Return retry-after seconds when the identity exceeds its window."""
        now = time.monotonic()
        with self._lock:
            window_start, count = self._windows.get(identity, (now, 0))
            elapsed = now - window_start
            if elapsed >= window_seconds:
                window_start, count = now, 0

            if count >= limit:
                return max(1, int(window_seconds - elapsed))

            self._windows[identity] = (window_start, count + 1)
            return None

    def reset(self) -> None:
        """Clear all counters, primarily for isolated tests."""
        with self._lock:
            self._windows.clear()


_DEVELOPMENT_FINGERPRINT: Final = "development"
rate_limiter = FixedWindowRateLimiter()


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


async def require_api_key(
    request: Request,
    provided_key: str | None = Security(api_key_header),
) -> AuthContext:
    """
    Require a configured API key.

    Development remains frictionless when bindings are empty. Production
    configuration validation prevents the service from starting without keys.
    """
    bindings = settings.api_key_bindings
    context: AuthContext
    if not bindings:
        context = AuthContext(company_id=None, key_fingerprint=_DEVELOPMENT_FINGERPRINT)
    else:
        matched_context: AuthContext | None = None
        if provided_key is not None:
            for company_id, configured_keys in bindings.items():
                if any(
                    secrets.compare_digest(provided_key, configured_key)
                    for configured_key in configured_keys
                ):
                    matched_context = AuthContext(
                        company_id=company_id,
                        key_fingerprint=_fingerprint(provided_key),
                    )
                    break

        if matched_context is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )
        context = matched_context

    retry_after = rate_limiter.check(
        identity=context.key_fingerprint,
        limit=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    request.state.company_id = context.company_id
    request.state.key_fingerprint = context.key_fingerprint
    return context


def reset_rate_limiter() -> None:
    """Reset counters for tests and controlled local verification."""
    rate_limiter.reset()
