"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

from app.domain.schema import HealthResponse
from app.rulesets.registry import get_current_ruleset

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check API health and return current ruleset info.

    Returns:
        HealthResponse with status and current ruleset.
    """
    try:
        current_ruleset = get_current_ruleset()
        ruleset_id = current_ruleset.ruleset_id
    except Exception:
        ruleset_id = "NONE"

    return HealthResponse(
        status="healthy",
        current_ruleset=ruleset_id,
        timestamp=datetime.utcnow(),
    )

