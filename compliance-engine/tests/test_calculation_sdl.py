"""
Tests for SDL calculation.
"""

from decimal import Decimal

import pytest

from app.rulesets.registry import get_current_ruleset
from app.services.calculation import calculate_sdl


@pytest.fixture
def ruleset():
    """Get current ruleset for testing."""
    return get_current_ruleset()


def test_calculate_sdl_normal_income(ruleset):
    """Test SDL calculation for normal income."""
    gross_income = Decimal("50000")
    sdl = calculate_sdl(gross_income, ruleset)

    # Should be 1% of gross income
    assert sdl == Decimal("500.00")


def test_calculate_sdl_zero_income(ruleset):
    """Test SDL calculation with zero income."""
    gross_income = Decimal("0")
    sdl = calculate_sdl(gross_income, ruleset)

    assert sdl == Decimal("0")


def test_calculate_sdl_rate(ruleset):
    """Test that SDL rate matches ruleset configuration."""
    gross_income = Decimal("100000")
    sdl = calculate_sdl(gross_income, ruleset)

    sdl_rate = ruleset.module.SDL_RATE
    expected = gross_income * sdl_rate

    assert sdl == expected


def test_calculate_sdl_sample_amounts(ruleset):
    """Test SDL calculation with specific sample amounts."""
    # Test case 1: R47,500 gross
    sdl = calculate_sdl(Decimal("47500"), ruleset)
    assert sdl == Decimal("475.00")

    # Test case 2: R73,500 gross
    sdl = calculate_sdl(Decimal("73500"), ruleset)
    assert sdl == Decimal("735.00")

    # Test case 3: R26,000 gross
    sdl = calculate_sdl(Decimal("26000"), ruleset)
    assert sdl == Decimal("260.00")

    # Test case 4: Contractor (should be called with 0 or not at all in practice)
    sdl = calculate_sdl(Decimal("0"), ruleset)
    assert sdl == Decimal("0")


def test_calculate_sdl_small_amount(ruleset):
    """Test SDL calculation with small income amount."""
    gross_income = Decimal("1000")
    sdl = calculate_sdl(gross_income, ruleset)

    assert sdl == Decimal("10.00")


def test_calculate_sdl_large_amount(ruleset):
    """Test SDL calculation with large income amount."""
    gross_income = Decimal("500000")
    sdl = calculate_sdl(gross_income, ruleset)

    assert sdl == Decimal("5000.00")


def test_calculate_sdl_decimal_precision(ruleset):
    """Test SDL calculation maintains decimal precision."""
    gross_income = Decimal("12345.67")
    sdl = calculate_sdl(gross_income, ruleset)

    # Should be exactly 1% with proper rounding
    assert sdl == Decimal("123.46")  # Rounded to 2 decimal places

