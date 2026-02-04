"""
Ruleset Registry

Manages ruleset discovery, selection, and retrieval.
Selects the appropriate ruleset based on tax_year, pay_date, and optional override.

Design: Rulesets are stored as code modules, not in database. This provides:
- Version control for tax rules
- Type safety and IDE support
- Easy testing of rules
- Simple deployment (no data migrations)
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from app.errors import RulesetNotFoundError
from app.rulesets import za_2025_26_v1


@dataclass
class RulesetInfo:
    """Container for ruleset information and data."""

    ruleset_version_id: str
    ruleset_id: str  # Alias for backward compatibility
    tax_year: str
    description: str
    effective_from: date
    effective_to: Optional[date]
    module: object  # Reference to the ruleset module


# ============================================================================
# RULESET REGISTRY
# ============================================================================

_RULESETS: Dict[str, RulesetInfo] = {}


def _register_ruleset(module: object) -> None:
    """
    Register a ruleset module in the registry.
    
    Args:
        module: Ruleset module with required attributes.
    """
    info = RulesetInfo(
        ruleset_version_id=module.RULESET_VERSION_ID,
        ruleset_id=module.RULESET_ID,
        tax_year=module.TAX_YEAR,
        description=module.DESCRIPTION,
        effective_from=module.EFFECTIVE_FROM,
        effective_to=module.EFFECTIVE_TO,
        module=module,
    )
    # Register by both ruleset_version_id and ruleset_id for flexibility
    _RULESETS[module.RULESET_VERSION_ID] = info
    if module.RULESET_ID != module.RULESET_VERSION_ID:
        _RULESETS[module.RULESET_ID] = info


# Register available rulesets
_register_ruleset(za_2025_26_v1)


# ============================================================================
# RULESET SELECTION FUNCTIONS (NO COMPUTATION, ONLY DATA SELECTION)
# ============================================================================


def select_ruleset(
    tax_year: str,
    pay_date: date,
    override: Optional[str] = None,
) -> RulesetInfo:
    """
    Select the appropriate ruleset based on tax_year, pay_date, and optional override.
    
    This function ONLY selects data, it does NOT perform any calculations.
    
    Selection logic:
    1. If override provided, use that exact ruleset
    2. Otherwise, find ruleset where:
       - tax_year matches (if specified)
       - effective_from <= pay_date <= effective_to
    3. If multiple match, use the one with the latest effective_from
    
    Args:
        tax_year: Tax year string (e.g., "2025_26")
        pay_date: The payment date
        override: Optional explicit ruleset version ID to use
        
    Returns:
        RulesetInfo for the selected ruleset
        
    Raises:
        RulesetNotFoundError: If no suitable ruleset found
    """
    # 1. If explicit override provided, use it
    if override:
        if override not in _RULESETS:
            raise RulesetNotFoundError(
                f"Ruleset '{override}' not found",
                details={"available_rulesets": list(_RULESETS.keys())},
            )
        return _RULESETS[override]
    
    # 2. Find ruleset by tax_year and pay_date
    candidates = []
    
    for info in _RULESETS.values():
        # Check tax year match
        if info.tax_year != tax_year:
            continue
            
        # Check effective date range
        if info.effective_from <= pay_date:
            if info.effective_to is None or pay_date <= info.effective_to:
                candidates.append(info)
    
    # 3. If multiple candidates, use the one with latest effective_from
    if candidates:
        # Sort by effective_from descending, take the first (most recent)
        candidates.sort(key=lambda r: r.effective_from, reverse=True)
        return candidates[0]
    
    # No ruleset found
    raise RulesetNotFoundError(
        f"No active ruleset found for tax_year={tax_year}, pay_date={pay_date}",
        details={
            "tax_year": tax_year,
            "pay_date": str(pay_date),
            "available_rulesets": [
                {
                    "id": r.ruleset_version_id,
                    "tax_year": r.tax_year,
                    "effective_from": str(r.effective_from),
                    "effective_to": str(r.effective_to) if r.effective_to else None,
                }
                for r in _RULESETS.values()
            ],
        },
    )


def select_ruleset_for_date(
    pay_date: date,
    tax_year: Optional[str] = None,
    ruleset_override: Optional[str] = None,
) -> RulesetInfo:
    """
    Legacy function for backward compatibility.
    Selects ruleset based on pay_date and optional tax_year hint.
    
    Args:
        pay_date: The payment date
        tax_year: Optional tax year hint (e.g., "2025_26")
        ruleset_override: Optional explicit ruleset ID to use
        
    Returns:
        RulesetInfo for the selected ruleset
        
    Raises:
        RulesetNotFoundError: If no suitable ruleset found
    """
    # If explicit override provided, use it
    if ruleset_override:
        return get_ruleset(ruleset_override)
    
    # Determine tax_year from pay_date if not provided
    if tax_year is None:
        # SA tax year runs March 1 to Feb 28/29
        if pay_date.month >= 3:
            # March onwards: current year to next year
            tax_year = f"{pay_date.year}_{str(pay_date.year + 1)[-2:]}"
        else:
            # Jan-Feb: previous year to current year
            tax_year = f"{pay_date.year - 1}_{str(pay_date.year)[-2:]}"
    
    return select_ruleset(tax_year, pay_date, ruleset_override)


# ============================================================================
# QUERY FUNCTIONS (NO COMPUTATION, ONLY DATA RETRIEVAL)
# ============================================================================


def list_rulesets() -> List[RulesetInfo]:
    """
    List all available rulesets.
    
    Returns:
        List of RulesetInfo objects.
    """
    # Return unique rulesets (avoid duplicates from double registration)
    seen = set()
    unique_rulesets = []
    for info in _RULESETS.values():
        if info.ruleset_version_id not in seen:
            seen.add(info.ruleset_version_id)
            unique_rulesets.append(info)
    return unique_rulesets


def get_ruleset(ruleset_id: str) -> RulesetInfo:
    """
    Get a specific ruleset by ID.
    
    Args:
        ruleset_id: The ruleset identifier (e.g., "ZA_2025_26_v1")
        
    Returns:
        RulesetInfo for the requested ruleset.
        
    Raises:
        RulesetNotFoundError: If ruleset doesn't exist.
    """
    if ruleset_id not in _RULESETS:
        raise RulesetNotFoundError(
            f"Ruleset '{ruleset_id}' not found",
            details={"available_rulesets": list(_RULESETS.keys())},
        )
    return _RULESETS[ruleset_id]


def get_current_ruleset() -> RulesetInfo:
    """
    Get the currently active ruleset based on today's date.
    
    Returns:
        RulesetInfo for the current ruleset.
        
    Raises:
        RulesetNotFoundError: If no active ruleset found.
    """
    today = date.today()
    return select_ruleset_for_date(today)


def is_ruleset_current(ruleset_id: str) -> bool:
    """
    Check if a ruleset is currently active.
    
    Args:
        ruleset_id: The ruleset identifier.
        
    Returns:
        True if the ruleset is currently active.
    """
    try:
        current = get_current_ruleset()
        return current.ruleset_version_id == ruleset_id
    except RulesetNotFoundError:
        return False


# ============================================================================
# DATA ACCESSOR FUNCTIONS (NO COMPUTATION, ONLY DATA EXTRACTION)
# ============================================================================


def get_tax_brackets(ruleset_id: str, frequency: str = "monthly") -> List[dict]:
    """
    Get tax brackets from a ruleset.
    
    Args:
        ruleset_id: The ruleset identifier.
        frequency: "monthly" or "annual".
        
    Returns:
        List of tax bracket dictionaries.
    """
    info = get_ruleset(ruleset_id)
    module = info.module
    
    if frequency == "monthly":
        brackets = module.get_monthly_tax_brackets()
    else:
        brackets = module.TAX_BRACKETS_ANNUAL
    
    return [
        {
            "min_income": b.min_income,
            "max_income": b.max_income,
            "rate": b.rate,
            "base_tax": b.base_tax,
        }
        for b in brackets
    ]


def get_uif_config(ruleset_id: str) -> dict:
    """
    Get UIF configuration from a ruleset.
    
    Args:
        ruleset_id: The ruleset identifier.
        
    Returns:
        Dictionary with UIF rates and caps.
    """
    info = get_ruleset(ruleset_id)
    module = info.module
    return {
        "employee_rate": module.UIF_EMPLOYEE_RATE,
        "employer_rate": module.UIF_EMPLOYER_RATE,
        "monthly_cap": module.UIF_MONTHLY_CAP,
        "annual_cap": module.UIF_ANNUAL_CAP,
    }


def get_sdl_config(ruleset_id: str) -> dict:
    """
    Get SDL configuration from a ruleset.
    
    Args:
        ruleset_id: The ruleset identifier.
        
    Returns:
        Dictionary with SDL rate and threshold.
    """
    info = get_ruleset(ruleset_id)
    module = info.module
    return {
        "rate": module.SDL_RATE,
        "annual_threshold": module.SDL_ANNUAL_PAYROLL_THRESHOLD,
    }

