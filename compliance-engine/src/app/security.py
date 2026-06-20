"""Authentication dependencies for protected payroll endpoints."""

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    provided_key: str | None = Security(api_key_header),
) -> str | None:
    """
    Require a configured API key.

    Development remains frictionless when API_KEYS is empty. Production
    configuration validation prevents the service from starting without keys.
    """
    configured_keys = settings.api_keys_list
    if not configured_keys:
        return None

    if provided_key is None or not any(
        secrets.compare_digest(provided_key, configured_key) for configured_key in configured_keys
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    return provided_key
