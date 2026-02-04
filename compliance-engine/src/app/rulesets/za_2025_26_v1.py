"""
South Africa Tax Ruleset for 2025/26 Tax Year (1 March 2025 - 28 February 2026)

FROZEN: 2026-01-27 - Values extracted from data/samples/sa_payroll_workbook.xlsx
This ruleset is IMMUTABLE. Any changes require creating ZA_2025_26_v2.

VALUES SOURCE: data/samples/sa_payroll_workbook.xlsx (Ruleset v1.1 sheet)
These values match official SARS 2024/25 rates.

All tax rules, brackets, caps, and thresholds are stored as data (not code).

Sources:
- data/samples/sa_payroll_workbook.xlsx (primary source of truth)
- SARS Tax Tables 2024/25: https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/
- UIF: Unemployment Insurance Act
- SDL: Skills Development Act
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class TaxBracket:
    """Immutable tax bracket definition."""

    min_income: Decimal
    max_income: Optional[Decimal]  # None = no upper limit
    rate: Decimal  # e.g., 0.18 for 18%
    base_tax: Decimal  # Tax on income below this bracket


# ============================================================================
# RULESET METADATA - Required fields
# ============================================================================

RULESET_VERSION_ID = "ZA_2025_26_v1"
RULESET_ID = "ZA_2025_26_v1"  # Alias for backward compatibility
TAX_YEAR = "2025_26"
DESCRIPTION = "South Africa Tax Year 2025/26 (1 March 2025 - 28 February 2026)"
EFFECTIVE_FROM = date(2025, 3, 1)
EFFECTIVE_TO = date(2026, 2, 28)


# ============================================================================
# PAYE TAX BRACKETS (Annual amounts)
# ============================================================================
# Source: Extracted from sa_payroll_workbook.xlsx on 2026-01-27
# These are the official SARS 2025/26 values as confirmed in the workbook

TAX_BRACKETS_ANNUAL: List[TaxBracket] = [
    TaxBracket(
        min_income=Decimal("1"),  # Workbook shows 1 instead of 0
        max_income=Decimal("237100"),
        rate=Decimal("0.18"),
        base_tax=Decimal("0"),
    ),
    TaxBracket(
        min_income=Decimal("237101"),
        max_income=Decimal("370500"),
        rate=Decimal("0.26"),
        base_tax=Decimal("42678"),
    ),
    TaxBracket(
        min_income=Decimal("370501"),
        max_income=Decimal("512800"),
        rate=Decimal("0.31"),
        base_tax=Decimal("77362"),
    ),
    TaxBracket(
        min_income=Decimal("512801"),
        max_income=Decimal("673000"),
        rate=Decimal("0.36"),
        base_tax=Decimal("121475"),
    ),
    TaxBracket(
        min_income=Decimal("673001"),
        max_income=Decimal("857900"),
        rate=Decimal("0.39"),
        base_tax=Decimal("179147"),
    ),
    TaxBracket(
        min_income=Decimal("857901"),
        max_income=Decimal("1817000"),
        rate=Decimal("0.41"),
        base_tax=Decimal("251258"),
    ),
    TaxBracket(
        min_income=Decimal("1817001"),
        max_income=Decimal("99999999"),  # Workbook explicit upper bound
        rate=Decimal("0.45"),
        base_tax=Decimal("644489"),
    ),
]


# ============================================================================
# TAX REBATES (Annual amounts)
# ============================================================================

REBATES = {
    "primary": Decimal("17235"),  # All taxpayers
    "secondary": Decimal("9444"),  # Age 65+
    "tertiary": Decimal("3145"),  # Age 75+
}


# ============================================================================
# TAX THRESHOLDS (Annual taxable income below which no tax is payable)
# ============================================================================

TAX_THRESHOLDS = {
    "under_65": Decimal("95750"),
    "65_to_74": Decimal("148217"),
    "75_plus": Decimal("165689"),
}


# ============================================================================
# UIF (Unemployment Insurance Fund)
# ============================================================================

UIF_EMPLOYEE_RATE = Decimal("0.01")  # 1% of gross income
UIF_EMPLOYER_RATE = Decimal("0.01")  # 1% of gross income
UIF_ANNUAL_CAP = Decimal("212544")  # Annual remuneration cap for UIF calculation
UIF_MONTHLY_CAP = Decimal("17712")  # Monthly equivalent (212544 / 12)


# ============================================================================
# SDL (Skills Development Levy)
# ============================================================================

SDL_RATE = Decimal("0.01")  # 1% of gross income
SDL_ANNUAL_PAYROLL_THRESHOLD = Decimal("500000")  # R500,000 annual payroll threshold


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_monthly_tax_brackets() -> List[TaxBracket]:
    """
    Convert annual tax brackets to monthly equivalents.

    Returns:
        List of TaxBracket with monthly amounts.
    """
    monthly_brackets = []
    for bracket in TAX_BRACKETS_ANNUAL:
        monthly_brackets.append(
            TaxBracket(
                min_income=bracket.min_income / 12,
                max_income=bracket.max_income / 12 if bracket.max_income else None,
                rate=bracket.rate,
                base_tax=bracket.base_tax / 12,
            )
        )
    return monthly_brackets


def get_ruleset_metadata() -> dict:
    """
    Get ruleset metadata as a dictionary.

    Returns:
        Dictionary with ruleset metadata including required fields.
    """
    return {
        "ruleset_version_id": RULESET_VERSION_ID,
        "ruleset_id": RULESET_ID,
        "tax_year": TAX_YEAR,
        "description": DESCRIPTION,
        "effective_from": EFFECTIVE_FROM,
        "effective_to": EFFECTIVE_TO,
    }
