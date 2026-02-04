"""
Tests for PAYE calculation.
"""

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json

import pytest

from app.domain.models import PayrollFrequency
from app.rulesets.registry import get_current_ruleset
from app.services.calculation import calculate_paye


@pytest.fixture
def ruleset():
    """Get current ruleset for testing."""
    return get_current_ruleset()


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _load_workbook_paye_rules() -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    rules_path = repo_root / "data" / "samples" / "paye_rules_from_workbook.json"
    return json.loads(rules_path.read_text(encoding="utf-8"))


def _expected_paye_from_workbook(monthly_taxable: Decimal) -> tuple[Decimal, str]:
    rules = _load_workbook_paye_rules()
    annual_taxable = monthly_taxable * Decimal("12")

    selected = None
    for bracket in rules["brackets"]:
        bracket_min = Decimal(str(bracket["from_amount"]))
        bracket_max = Decimal(str(bracket["to_amount"]))
        if annual_taxable >= bracket_min and annual_taxable <= bracket_max:
            selected = bracket
            break

    assert selected is not None, "No bracket selected for annual taxable"

    base_tax = Decimal(str(selected["base_tax"]))
    rate = Decimal(str(selected["marginal_rate"]))
    annual_tax_before_rebate = base_tax + ((annual_taxable - Decimal(str(selected["from_amount"]))) * rate)

    primary_rebate = Decimal(str(rules["rebates"]["primary"]))
    annual_tax_after_rebate = annual_tax_before_rebate - primary_rebate
    if annual_tax_after_rebate < 0:
        annual_tax_after_rebate = Decimal("0")

    monthly_paye = annual_tax_after_rebate / Decimal("12")
    monthly_paye_rounded = _round_money(monthly_paye)

    diagnostics = (
        f"annual_taxable={annual_taxable} | "
        f"bracket_from={selected['from_amount']} bracket_to={selected['to_amount']} | "
        f"base_tax={base_tax} rate={rate} | "
        f"annual_before_rebate={annual_tax_before_rebate} rebate={primary_rebate} "
        f"annual_after_rebate={annual_tax_after_rebate} | "
        f"monthly_rounded={monthly_paye_rounded}"
    )
    return monthly_paye_rounded, diagnostics


def test_calculate_paye_zero_income(ruleset):
    """Test PAYE calculation with zero taxable income."""
    paye = calculate_paye(Decimal("0"), PayrollFrequency.MONTHLY, ruleset)
    assert paye == Decimal("0")


def test_calculate_paye_below_threshold(ruleset):
    """Test PAYE calculation for income below tax threshold."""
    paye = calculate_paye(Decimal("5000"), PayrollFrequency.MONTHLY, ruleset)
    expected, diagnostics = _expected_paye_from_workbook(Decimal("5000"))
    assert _round_money(paye) == expected, diagnostics


def test_calculate_paye_low_income(ruleset):
    """Test PAYE calculation for low income in first bracket."""
    paye = calculate_paye(Decimal("10000"), PayrollFrequency.MONTHLY, ruleset)
    expected, diagnostics = _expected_paye_from_workbook(Decimal("10000"))
    assert _round_money(paye) == expected, diagnostics


def test_calculate_paye_medium_income(ruleset):
    """Test PAYE calculation for medium income."""
    paye = calculate_paye(Decimal("30000"), PayrollFrequency.MONTHLY, ruleset)
    expected, diagnostics = _expected_paye_from_workbook(Decimal("30000"))
    assert _round_money(paye) == expected, diagnostics


def test_calculate_paye_high_income(ruleset):
    """Test PAYE calculation for high income."""
    paye = calculate_paye(Decimal("100000"), PayrollFrequency.MONTHLY, ruleset)
    expected, diagnostics = _expected_paye_from_workbook(Decimal("100000"))
    assert _round_money(paye) == expected, diagnostics


def test_calculate_paye_weekly_frequency(ruleset):
    """Test PAYE calculation with weekly frequency."""
    # R2,000 per week = R104,000 per year (52 weeks)
    paye = calculate_paye(Decimal("2000"), PayrollFrequency.WEEKLY, ruleset)
    assert paye >= Decimal("0")


def test_calculate_paye_fortnightly_frequency(ruleset):
    """Test PAYE calculation with fortnightly frequency."""
    # R4,000 per fortnight = R104,000 per year (26 periods)
    paye = calculate_paye(Decimal("4000"), PayrollFrequency.FORTNIGHTLY, ruleset)
    assert paye >= Decimal("0")


def test_calculate_paye_negative_income(ruleset):
    """Test PAYE calculation with negative income returns zero."""
    paye = calculate_paye(Decimal("-5000"), PayrollFrequency.MONTHLY, ruleset)
    assert paye == Decimal("0")


def test_calculate_paye_specific_amounts(ruleset):
    """Test PAYE calculation with specific workbook-derived test cases."""
    for monthly in [Decimal("43900"), Decimal("64800")]:
        paye = calculate_paye(monthly, PayrollFrequency.MONTHLY, ruleset)
        expected, diagnostics = _expected_paye_from_workbook(monthly)
        assert _round_money(paye) == expected, diagnostics
