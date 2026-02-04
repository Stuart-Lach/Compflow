"""
Tests for UIF calculation.
"""

from decimal import Decimal
from datetime import date

import pytest

from app.rulesets.registry import get_current_ruleset
from app.domain.models import EmploymentType, PayrollFrequency, PayrollInputRow
from app.services.calculation import calculate_employee, calculate_uif


@pytest.fixture
def ruleset():
    """Get current ruleset for testing."""
    return get_current_ruleset()


def test_calculate_uif_normal_income(ruleset):
    """Test UIF calculation for normal income below cap."""
    gross_income = Decimal("10000")
    employee, employer = calculate_uif(gross_income, ruleset)

    assert employee == Decimal("100.00")
    assert employer == Decimal("100.00")


def test_calculate_uif_above_cap(ruleset):
    """Test UIF calculation for income above cap."""
    gross_income = Decimal("50000")
    employee, employer = calculate_uif(gross_income, ruleset)

    assert employee == Decimal("177.12")
    assert employer == Decimal("177.12")


def test_calculate_uif_contractor_zero(ruleset):
    """Contractors should have UIF employee and employer = 0."""
    row = PayrollInputRow(
        payroll_run_id="RUN-1",
        company_id="COMP-1",
        pay_date=date(2025, 4, 1),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="CON-1",
        employment_type=EmploymentType.CONTRACTOR,
        basic_salary=Decimal("50000"),
    )
    result = calculate_employee(row, ruleset)
    assert result.uif_employee == Decimal("0.00")
    assert result.uif_employer == Decimal("0.00")
