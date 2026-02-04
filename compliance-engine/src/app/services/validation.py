"""
Validation Service

Applies business rule validation to parsed payroll data.
Returns structured list of issues with fields: code, severity, field, row_index, message.

Severity levels:
- error: Blocks processing
- warn: Advisory, processing continues
- info: Informational only
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from app.domain.models import (
    EmploymentType,
    PayrollInputRow,
)
from app.rulesets.registry import RulesetInfo


@dataclass
class ValidationIssue:
    """
    Structured validation issue.

    Fields match the canonical contract exactly.
    """

    code: str
    severity: str  # "error", "warn", or "info"
    field: Optional[str]
    row_index: int  # 0-based index, or -1 for run-level issues
    message: str
    employee_id: Optional[str] = None  # For easier debugging


def validate_rows(
    rows: List[PayrollInputRow],
    ruleset: RulesetInfo,
) -> List[ValidationIssue]:
    """
    Validate parsed payroll rows against business rules.

    Returns structured list of issues. Rows with errors are marked but not removed
    (caller decides how to handle).

    Args:
        rows: List of parsed PayrollInputRow objects.
        ruleset: The ruleset to use for validation.

    Returns:
        List of ValidationIssue objects.
    """
    issues: List[ValidationIssue] = []

    # Run-level validations (execute once per run, not per employee)
    run_level_issues = _validate_run_level(rows, ruleset)
    issues.extend(run_level_issues)

    # Row-level validations (per employee)
    for idx, row in enumerate(rows):
        row_issues = _validate_row(row, idx, ruleset)
        issues.extend(row_issues)

    return issues


def _validate_run_level(
    rows: List[PayrollInputRow],
    ruleset: RulesetInfo,
) -> List[ValidationIssue]:
    """
    Perform run-level validations that should execute once per payroll run.

    These include checks like SDL liability determination that are based on
    company-wide criteria, not individual employee data.

    Args:
        rows: List of parsed PayrollInputRow objects.
        ruleset: The ruleset to use for validation.

    Returns:
        List of run-level ValidationIssue objects (row_index = -1).
    """
    issues: List[ValidationIssue] = []

    if not rows:
        return issues

    # Check if annual_payroll_estimate is provided (run-level check)
    # Use first row to check run-level fields
    first_row = rows[0]
    sdl_threshold = ruleset.module.SDL_ANNUAL_PAYROLL_THRESHOLD

    # Check for missing annual payroll estimate (run-level)
    if first_row.annual_payroll_estimate is None and first_row.is_sdl_liable_override is None:
        issues.append(
            ValidationIssue(
                code="SDL_ESTIMATE_MISSING",
                severity="warn",
                field="annual_payroll_estimate",
                row_index=-1,  # Run-level issue
                message=f"annual_payroll_estimate not provided. SDL liability cannot be determined. Assuming liable if company total > R{sdl_threshold:,.0f}.",
                employee_id=None,
            )
        )

    return issues


def _validate_row(
    row: PayrollInputRow,
    row_index: int,
    ruleset: RulesetInfo,
) -> List[ValidationIssue]:
    """
    Validate a single row against business rules.

    Args:
        row: The payroll input row.
        row_index: 0-based row index in the parsed list.
        ruleset: The active ruleset.

    Returns:
        List of validation issues for this row.
    """
    issues: List[ValidationIssue] = []

    # Validate employee_id is present (may have been defaulted during parse)
    if not row.employee_id or row.employee_id.startswith("UNKNOWN_ROW_"):
        issues.append(
            ValidationIssue(
                code="MISSING_EMPLOYEE_ID",
                severity="error",
                field="employee_id",
                row_index=row_index,
                message="employee_id is required but was missing or invalid.",
                employee_id=row.employee_id,
            )
        )

    # Validate employment dates
    if row.employment_start_date and row.employment_end_date:
        if row.employment_end_date < row.employment_start_date:
            issues.append(
                ValidationIssue(
                    code="INVALID_DATE_RANGE",
                    severity="error",
                    field="employment_end_date",
                    row_index=row_index,
                    message="employment_end_date cannot be before employment_start_date.",
                    employee_id=row.employee_id,
                )
            )

    # Validate gross income is positive
    if row.gross_income <= 0:
        issues.append(
            ValidationIssue(
                code="ZERO_GROSS_INCOME",
                severity="error",
                field="basic_salary",
                row_index=row_index,
                message="Gross income must be greater than 0.",
                employee_id=row.employee_id,
            )
        )

    # Validate basic salary is positive
    if row.basic_salary <= 0:
        issues.append(
            ValidationIssue(
                code="INVALID_SALARY",
                severity="error",
                field="basic_salary",
                row_index=row_index,
                message="basic_salary must be a positive number.",
                employee_id=row.employee_id,
            )
        )

    # Warn if pre-tax deductions exceed gross income
    if row.pre_tax_deductions > row.gross_income:
        issues.append(
            ValidationIssue(
                code="DEDUCTIONS_EXCEED_GROSS",
                severity="warn",
                field="pension_contribution_employee",
                row_index=row_index,
                message="Pre-tax deductions exceed gross income. Taxable income will be negative.",
                employee_id=row.employee_id,
            )
        )

    # Contractor warning - UIF and SDL will be 0
    if row.employment_type == EmploymentType.CONTRACTOR:
        issues.append(
            ValidationIssue(
                code="CONTRACTOR_UIF_SDL_EXEMPT",
                severity="warn",
                field="employment_type",
                row_index=row_index,
                message="Contractor: UIF and SDL will be computed as 0.",
                employee_id=row.employee_id,
            )
        )

    # SDL liability warnings (row-level only for specific overrides/thresholds)
    sdl_threshold = ruleset.module.SDL_ANNUAL_PAYROLL_THRESHOLD

    if row.employment_type == EmploymentType.EMPLOYEE:
        if row.is_sdl_liable_override is False:
            # Explicitly exempt
            issues.append(
                ValidationIssue(
                    code="SDL_OVERRIDE_EXEMPT",
                    severity="info",
                    field="is_sdl_liable_override",
                    row_index=row_index,
                    message="SDL explicitly set to exempt via override.",
                    employee_id=row.employee_id,
                )
            )
        # Note: SDL_ESTIMATE_MISSING is now a run-level validation, not per-employee
        elif row.annual_payroll_estimate is not None and row.annual_payroll_estimate < sdl_threshold:
            issues.append(
                ValidationIssue(
                    code="SDL_BELOW_THRESHOLD",
                    severity="info",
                    field="annual_payroll_estimate",
                    row_index=row_index,
                    message=f"Annual payroll estimate (R{row.annual_payroll_estimate:,.2f}) is below SDL threshold (R{sdl_threshold:,.0f}). SDL will be 0.",
                    employee_id=row.employee_id,
                )
            )

    return issues


def is_sdl_liable(row: PayrollInputRow, ruleset: RulesetInfo) -> bool:
    """
    Determine if SDL applies to this employee.

    Args:
        row: The payroll input row.
        ruleset: The active ruleset.

    Returns:
        True if SDL should be calculated.
    """
    # Contractors are never SDL liable
    if row.employment_type == EmploymentType.CONTRACTOR:
        return False

    # Check override first
    if row.is_sdl_liable_override is not None:
        return row.is_sdl_liable_override

    # Check annual payroll estimate
    sdl_threshold = ruleset.module.SDL_ANNUAL_PAYROLL_THRESHOLD
    if row.annual_payroll_estimate is not None:
        return row.annual_payroll_estimate >= sdl_threshold

    # Default to liable if estimate not provided (conservative)
    return True


def is_uif_applicable(row: PayrollInputRow) -> bool:
    """
    Determine if UIF applies to this employee.

    Args:
        row: The payroll input row.

    Returns:
        True if UIF should be calculated.
    """
    return row.employment_type == EmploymentType.EMPLOYEE


def filter_errors(issues: List[ValidationIssue]) -> List[ValidationIssue]:
    """
    Filter to only error-level issues.

    Args:
        issues: List of validation issues.

    Returns:
        List of only error-severity issues.
    """
    return [i for i in issues if i.severity == "error"]


def has_errors(issues: List[ValidationIssue]) -> bool:
    """
    Check if there are any error-level issues.

    Args:
        issues: List of validation issues.

    Returns:
        True if any errors present.
    """
    return any(i.severity == "error" for i in issues)


def get_valid_row_indices(rows: List[PayrollInputRow], issues: List[ValidationIssue]) -> List[int]:
    """
    Get indices of rows that have no errors.

    Args:
        rows: List of all rows.
        issues: List of validation issues.

    Returns:
        List of row indices that can be processed.
    """
    error_indices = {i.row_index for i in issues if i.severity == "error"}
    return [idx for idx in range(len(rows)) if idx not in error_indices]

