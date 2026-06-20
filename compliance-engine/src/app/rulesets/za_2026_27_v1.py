"""
South Africa tax rules for the 2027 year of assessment.

Effective 1 March 2026 through 28 February 2027.

Primary source:
https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/

UIF source:
https://www.sars.gov.za/types-of-tax/unemployment-insurance-fund/

SDL source:
https://www.sars.gov.za/types-of-tax/skills-development-levy/
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TaxBracket:
    """Immutable annual tax bracket."""

    min_income: Decimal
    max_income: Decimal | None
    rate: Decimal
    base_tax: Decimal


RULESET_VERSION_ID = "ZA_2026_27_v1"
RULESET_ID = "ZA_2026_27_v1"
TAX_YEAR = "2026_27"
DESCRIPTION = "South Africa 2027 year of assessment (1 March 2026 - 28 February 2027)"
EFFECTIVE_FROM = date(2026, 3, 1)
EFFECTIVE_TO = date(2027, 2, 28)


TAX_BRACKETS_ANNUAL: list[TaxBracket] = [
    TaxBracket(Decimal("1"), Decimal("245100"), Decimal("0.18"), Decimal("0")),
    TaxBracket(Decimal("245101"), Decimal("383100"), Decimal("0.26"), Decimal("44118")),
    TaxBracket(Decimal("383101"), Decimal("530200"), Decimal("0.31"), Decimal("79998")),
    TaxBracket(Decimal("530201"), Decimal("695800"), Decimal("0.36"), Decimal("125599")),
    TaxBracket(Decimal("695801"), Decimal("887000"), Decimal("0.39"), Decimal("185215")),
    TaxBracket(Decimal("887001"), Decimal("1878600"), Decimal("0.41"), Decimal("259783")),
    TaxBracket(Decimal("1878601"), None, Decimal("0.45"), Decimal("666339")),
]


REBATES = {
    "primary": Decimal("17820"),
    "secondary": Decimal("9765"),
    "tertiary": Decimal("3249"),
}


TAX_THRESHOLDS = {
    "under_65": Decimal("99000"),
    "65_to_74": Decimal("153250"),
    "75_plus": Decimal("171300"),
}


UIF_EMPLOYEE_RATE = Decimal("0.01")
UIF_EMPLOYER_RATE = Decimal("0.01")
UIF_ANNUAL_CAP = Decimal("212544")
UIF_MONTHLY_CAP = Decimal("17712")


SDL_RATE = Decimal("0.01")
SDL_ANNUAL_PAYROLL_THRESHOLD = Decimal("500000")


def get_monthly_tax_brackets() -> list[TaxBracket]:
    """Return annual brackets converted to monthly equivalents."""
    return [
        TaxBracket(
            min_income=bracket.min_income / 12,
            max_income=bracket.max_income / 12 if bracket.max_income else None,
            rate=bracket.rate,
            base_tax=bracket.base_tax / 12,
        )
        for bracket in TAX_BRACKETS_ANNUAL
    ]


def get_ruleset_metadata() -> dict:
    """Return ruleset metadata."""
    return {
        "ruleset_version_id": RULESET_VERSION_ID,
        "ruleset_id": RULESET_ID,
        "tax_year": TAX_YEAR,
        "description": DESCRIPTION,
        "effective_from": EFFECTIVE_FROM,
        "effective_to": EFFECTIVE_TO,
    }
