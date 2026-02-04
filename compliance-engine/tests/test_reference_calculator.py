"""
Test to verify reference calculator independence and correctness.
"""

from decimal import Decimal
from datetime import date

import pytest

from app.domain.models import EmploymentType, PayrollFrequency, PayrollInputRow
from app.reference.reference_calculator import (
    ReferenceRuleset,
    TaxBracket,
    calculate_reference_results,
    round_money,
)


def test_reference_calculator_independence():
    """Verify reference calculator doesn't import production calculation service."""
    import sys
    import app.reference.reference_calculator as ref_calc

    # Check module doesn't have any imports from app.services.calculation
    module_dict = vars(ref_calc)
    for name, obj in module_dict.items():
        if hasattr(obj, '__module__'):
            assert 'app.services.calculation' not in obj.__module__, \
                f"Reference calculator must not import from app.services.calculation, but {name} does"


def test_reference_calculator_basic():
    """Test reference calculator with a simple scenario."""
    ruleset = ReferenceRuleset(
        brackets=[
            TaxBracket(
                min_income=Decimal("1"),
                max_income=Decimal("237100"),
                base_tax=Decimal("0"),
                rate=Decimal("0.18"),
            ),
        ],
        primary_rebate=Decimal("17235"),
        uif_cap_monthly=Decimal("17712"),
        uif_employee_rate=Decimal("0.01"),
        uif_employer_rate=Decimal("0.01"),
        sdl_rate=Decimal("0.01"),
        sdl_threshold_annual=Decimal("500000"),
    )

    row = PayrollInputRow(
        payroll_run_id="TEST",
        company_id="TEST",
        pay_date=date(2025, 4, 1),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("10000"),
    )

    results = calculate_reference_results([row], ruleset)

    assert len(results) == 1
    result = results[0]

    assert result.employee_id == "EMP001"
    assert result.gross_income == Decimal("10000.00")
    assert result.uif_employee == Decimal("100.00")
    assert result.uif_employer == Decimal("100.00")
    assert result.sdl == Decimal("100.00")


def test_reference_uif_cap():
    """Verify UIF is properly capped in reference calculator."""
    ruleset = ReferenceRuleset(
        brackets=[
            TaxBracket(
                min_income=Decimal("1"),
                max_income=Decimal("237100"),
                base_tax=Decimal("0"),
                rate=Decimal("0.18"),
            ),
        ],
        primary_rebate=Decimal("17235"),
        uif_cap_monthly=Decimal("17712"),
        uif_employee_rate=Decimal("0.01"),
        uif_employer_rate=Decimal("0.01"),
        sdl_rate=Decimal("0.01"),
        sdl_threshold_annual=Decimal("500000"),
    )

    row = PayrollInputRow(
        payroll_run_id="TEST",
        company_id="TEST",
        pay_date=date(2025, 4, 1),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("50000"),
    )

    results = calculate_reference_results([row], ruleset)
    result = results[0]

    # UIF should be capped at 17712 * 0.01 = 177.12
    assert result.uif_employee == Decimal("177.12")
    assert result.uif_employer == Decimal("177.12")


def test_reference_contractor_no_uif():
    """Verify contractors get zero UIF in reference calculator."""
    ruleset = ReferenceRuleset(
        brackets=[
            TaxBracket(
                min_income=Decimal("1"),
                max_income=Decimal("237100"),
                base_tax=Decimal("0"),
                rate=Decimal("0.18"),
            ),
        ],
        primary_rebate=Decimal("17235"),
        uif_cap_monthly=Decimal("17712"),
        uif_employee_rate=Decimal("0.01"),
        uif_employer_rate=Decimal("0.01"),
        sdl_rate=Decimal("0.01"),
        sdl_threshold_annual=Decimal("500000"),
    )

    row = PayrollInputRow(
        payroll_run_id="TEST",
        company_id="TEST",
        pay_date=date(2025, 4, 1),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="CON001",
        employment_type=EmploymentType.CONTRACTOR,
        basic_salary=Decimal("50000"),
    )

    results = calculate_reference_results([row], ruleset)
    result = results[0]

    assert result.uif_employee == Decimal("0.00")
    assert result.uif_employer == Decimal("0.00")
    assert result.sdl == Decimal("0.00")
