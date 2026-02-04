"""
Ruleset endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.domain.schema import (
    RulesetDetailResponse,
    RulesetListResponse,
    RulesetMetadata,
    TaxBracket,
)
from app.errors import RulesetNotFoundError
from app.rulesets.registry import (
    get_ruleset,
    get_tax_brackets,
    get_uif_config,
    get_sdl_config,
    is_ruleset_current,
    list_rulesets,
)

router = APIRouter()


@router.get("/rulesets", response_model=RulesetListResponse)
async def list_all_rulesets() -> RulesetListResponse:
    """
    List all available rulesets.

    Returns:
        RulesetListResponse with list of ruleset metadata.
    """
    rulesets = list_rulesets()

    return RulesetListResponse(
        rulesets=[
            RulesetMetadata(
                ruleset_id=r.ruleset_id,
                description=r.description,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
                is_current=is_ruleset_current(r.ruleset_id),
            )
            for r in rulesets
        ]
    )


@router.get("/rulesets/{ruleset_id}", response_model=RulesetDetailResponse)
async def get_ruleset_detail(ruleset_id: str) -> RulesetDetailResponse:
    """
    Get detailed ruleset information including tax tables.

    Args:
        ruleset_id: The ruleset identifier.

    Returns:
        RulesetDetailResponse with full ruleset details.

    Raises:
        HTTPException: If ruleset not found.
    """
    try:
        ruleset = get_ruleset(ruleset_id)
        brackets = get_tax_brackets(ruleset_id, "monthly")
        uif = get_uif_config(ruleset_id)
        sdl = get_sdl_config(ruleset_id)

        return RulesetDetailResponse(
            ruleset_id=ruleset.ruleset_id,
            description=ruleset.description,
            effective_from=ruleset.effective_from,
            effective_to=ruleset.effective_to,
            is_current=is_ruleset_current(ruleset_id),
            tax_brackets=[
                TaxBracket(
                    min_income=b["min_income"],
                    max_income=b["max_income"],
                    rate=b["rate"],
                    base_tax=b["base_tax"],
                )
                for b in brackets
            ],
            uif_rate_employee=uif["employee_rate"],
            uif_rate_employer=uif["employer_rate"],
            uif_monthly_cap=uif["monthly_cap"],
            sdl_rate=sdl["rate"],
            sdl_annual_threshold=sdl["annual_threshold"],
        )

    except RulesetNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

