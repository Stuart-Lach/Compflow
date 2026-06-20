"""Ruleset registration and effective-date boundary tests."""

from datetime import date
from decimal import Decimal

import pytest

from app.domain.models import PayrollFrequency
from app.errors import RulesetNotFoundError
from app.rulesets.registry import get_ruleset, select_ruleset_for_date
from app.services.calculation import calculate_paye


def test_ruleset_boundary_switches_on_1_march_2026():
    assert select_ruleset_for_date(date(2026, 2, 28)).ruleset_version_id == "ZA_2025_26_v1"
    assert select_ruleset_for_date(date(2026, 3, 1)).ruleset_version_id == "ZA_2026_27_v1"


def test_2026_27_ruleset_contains_sars_rates():
    ruleset = get_ruleset("ZA_2026_27_v1").module

    assert ruleset.TAX_BRACKETS_ANNUAL[0].max_income == Decimal("245100")
    assert ruleset.TAX_BRACKETS_ANNUAL[-1].base_tax == Decimal("666339")
    assert ruleset.REBATES["primary"] == Decimal("17820")
    assert ruleset.TAX_THRESHOLDS["under_65"] == Decimal("99000")


def test_no_expired_ruleset_fallback():
    with pytest.raises(RulesetNotFoundError):
        select_ruleset_for_date(date(2028, 3, 1))


def test_2026_27_paye_bracket_boundary_uses_previous_ceiling():
    ruleset = get_ruleset("ZA_2026_27_v1")
    annual_income = Decimal("245101")

    annual_paye = calculate_paye(
        annual_income / Decimal("12"),
        PayrollFrequency.MONTHLY,
        ruleset,
    ) * Decimal("12")

    assert annual_paye == Decimal("26298.26")
