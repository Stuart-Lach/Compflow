"""
Tests for validation service.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.domain.models import (
    EmploymentType,
    IssueSeverity,
    PayrollFrequency,
    PayrollInputRow,
    ResidencyStatus,
)
from app.rulesets.registry import get_current_ruleset
from app.services.validation import (
    is_sdl_liable,
    is_uif_applicable,
    validate_rows,
)


@pytest.fixture
def ruleset():
    """Get current ruleset for testing."""
    return get_current_ruleset()


@pytest.fixture
def sample_employee_row():
    """Create a sample employee row."""
    return PayrollInputRow(
        payroll_run_id="RUN001",
        company_id="COMP001",
        pay_date=date(2025, 3, 25),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("45000.00"),
        annual_payroll_estimate=Decimal("1200000"),
    )


@pytest.fixture
def sample_contractor_row():
    """Create a sample contractor row."""
    return PayrollInputRow(
        payroll_run_id="RUN001",
        company_id="COMP001",
        pay_date=date(2025, 3, 25),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="CON001",
        employment_type=EmploymentType.CONTRACTOR,
        basic_salary=Decimal("35000.00"),
    )


def test_validate_employee_row_no_issues(ruleset, sample_employee_row):
    """Test validation of valid employee row."""
    issues = validate_rows([sample_employee_row], ruleset)

    # Should have no errors, but might have warnings
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_validate_contractor_generates_warning(ruleset, sample_contractor_row):
    """Test that contractor employment type generates warning."""
    issues = validate_rows([sample_contractor_row], ruleset)

    assert any(i.code == "CONTRACTOR_UIF_SDL_EXEMPT" for i in issues)
    assert any(i.severity == "warn" for i in issues)


def test_validate_invalid_date_range(ruleset):
    """Test validation with invalid employment date range."""
    row = PayrollInputRow(
        payroll_run_id="RUN001",
        company_id="COMP001",
        pay_date=date(2025, 3, 25),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("45000.00"),
        employment_start_date=date(2025, 1, 1),
        employment_end_date=date(2024, 12, 31),  # Before start date
    )

    issues = validate_rows([row], ruleset)

    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) > 0  # Row should be rejected
    assert any(i.code == "INVALID_DATE_RANGE" for i in issues)


def test_validate_sdl_below_threshold(ruleset):
    """Test SDL warning when below threshold."""
    row = PayrollInputRow(
        payroll_run_id="RUN001",
        company_id="COMP001",
        pay_date=date(2025, 3, 25),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("45000.00"),
        annual_payroll_estimate=Decimal("400000"),  # Below SDL threshold
    )

    issues = validate_rows([row], ruleset)

    assert any(i.code == "SDL_BELOW_THRESHOLD" for i in issues)


def test_validate_sdl_missing_estimate(ruleset):
    """Test SDL warning when estimate is missing."""
    row = PayrollInputRow(
        payroll_run_id="RUN001",
        company_id="COMP001",
        pay_date=date(2025, 3, 25),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("45000.00"),
        annual_payroll_estimate=None,  # Missing
    )

    issues = validate_rows([row], ruleset)

    assert any(i.code == "SDL_ESTIMATE_MISSING" for i in issues)


def test_is_sdl_liable_employee_above_threshold(ruleset, sample_employee_row):
    """Test SDL liability for employee above threshold."""
    assert is_sdl_liable(sample_employee_row, ruleset) is True


def test_is_sdl_liable_contractor(ruleset, sample_contractor_row):
    """Test SDL liability for contractor (always False)."""
    assert is_sdl_liable(sample_contractor_row, ruleset) is False


def test_is_sdl_liable_with_override(ruleset):
    """Test SDL liability with explicit override."""
    row = PayrollInputRow(
        payroll_run_id="RUN001",
        company_id="COMP001",
        pay_date=date(2025, 3, 25),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        employee_id="EMP001",
        employment_type=EmploymentType.EMPLOYEE,
        basic_salary=Decimal("45000.00"),
        is_sdl_liable_override=False,  # Explicitly not liable
    )

    assert is_sdl_liable(row, ruleset) is False


def test_is_uif_applicable_employee(sample_employee_row):
    """Test UIF applicability for employee."""
    assert is_uif_applicable(sample_employee_row) is True


def test_is_uif_applicable_contractor(sample_contractor_row):
    """Test UIF applicability for contractor."""
    assert is_uif_applicable(sample_contractor_row) is False


def test_validate_multiple_rows(ruleset, sample_employee_row, sample_contractor_row):
    """Test validation of multiple rows."""
    rows = [sample_employee_row, sample_contractor_row]
    issues = validate_rows(rows, ruleset)

    # Contractor should generate warning
    assert any(i.employee_id == "CON001" for i in issues)

