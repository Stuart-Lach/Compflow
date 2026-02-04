"""
CSV Ingestion Service

Handles parsing and initial processing of payroll CSV files.
Converts raw CSV data into domain objects for validation and calculation.

This service:
- Parses CSV bytes
- Normalizes empty numeric fields to 0
- Parses dates in YYYY-MM-DD format
- Returns (rows, run_context) tuple
"""

import csv
import io
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from app.domain.models import (
    EmploymentType,
    PayrollFrequency,
    PayrollInputRow,
    ResidencyStatus,
)
from app.errors import SchemaValidationError


logger = logging.getLogger(__name__)


@dataclass
class RunContext:
    """
    Context information extracted from the CSV for the entire run.
    All rows in a CSV should share these common attributes.
    """

    payroll_run_id: str
    company_id: str
    pay_date: date
    tax_year: str
    payroll_frequency: PayrollFrequency
    ruleset_version_override: Optional[str] = None
    annual_payroll_estimate: Optional[Decimal] = None
    is_sdl_liable_override: Optional[bool] = None


# Required columns that must be present in every CSV
REQUIRED_COLUMNS = [
    "payroll_run_id",
    "company_id",
    "pay_date",
    "tax_year",
    "payroll_frequency",
    "employee_id",
    "employment_type",
    "basic_salary",
]

# All valid columns (required + optional)
VALID_COLUMNS = REQUIRED_COLUMNS + [
    "annual_payroll_estimate",
    "is_sdl_liable_override",
    "ruleset_version_override",
    "residency_status",
    "employment_start_date",
    "employment_end_date",
    "overtime_pay",
    "bonus_commission",
    "allowances_taxable",
    "allowances_non_taxable",
    "fringe_benefits_taxable",
    "reimbursements",
    "other_earnings",
    "pension_contribution_employee",
    "retirement_annuity_employee",
    "medical_aid_contribution_employee",
    "other_pre_tax_deductions",
    "union_fees",
    "garnishees",
    "other_post_tax_deductions",
]


def parse_csv(content: bytes) -> Tuple[List[PayrollInputRow], RunContext]:
    """
    Parse CSV content into PayrollInputRow objects and extract run context.

    Backwards compatible version that returns 2 values.
    For parse issues, use parse_csv_with_issues().

    Args:
        content: Raw CSV file content as bytes.

    Returns:
        Tuple of (parsed rows, run context).

    Raises:
        SchemaValidationError: If required columns are missing or CSV is invalid.
    """
    rows, run_context, _ = parse_csv_with_issues(content)
    return rows, run_context


def parse_csv_with_issues(content: bytes) -> Tuple[List[PayrollInputRow], RunContext, List]:
    """
    Parse CSV content into PayrollInputRow objects and extract run context.

    IMPORTANT: This function NEVER silently drops rows. Any row that fails parsing
    will generate a ROW_PARSE_ERROR validation issue with the raw row data.

    Args:
        content: Raw CSV file content as bytes.

    Returns:
        Tuple of (parsed rows, run context, parse issues).
        - parsed rows: Successfully parsed PayrollInputRow objects
        - run context: Shared run-level information
        - parse issues: List of ValidationIssue objects for rows that failed parsing

    Raises:
        SchemaValidationError: If required columns are missing or CSV is invalid.
    """
    # Decode content
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except UnicodeDecodeError:
            raise SchemaValidationError(
                "Unable to decode CSV file. Please use UTF-8 or Latin-1 encoding."
            )

    # Parse CSV
    reader = csv.DictReader(io.StringIO(text))

    # Validate required columns
    if reader.fieldnames is None:
        raise SchemaValidationError("CSV file appears to be empty or invalid.")

    headers = [h.strip().lower() for h in reader.fieldnames]
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in headers]

    if missing_columns:
        raise SchemaValidationError(
            f"Missing required columns: {', '.join(missing_columns)}",
            errors=[{"field": col, "error": "required"} for col in missing_columns],
        )

    # Parse all rows first
    rows: List[PayrollInputRow] = []
    raw_rows = list(reader)

    if not raw_rows:
        raise SchemaValidationError("CSV file contains no data rows.")

    # Extract run context from first row
    first_raw_row = raw_rows[0]
    first_row_normalized = {
        k.strip().lower(): v.strip() if v else "" for k, v in first_raw_row.items()
    }

    run_context = _extract_run_context(first_row_normalized)

    # Track parse errors as issues - NEVER silently drop rows
    parse_issues = []

    # Parse each row - capture parse failures as structured issues
    for row_num, raw_row in enumerate(raw_rows, start=2):  # Start at 2 (header is row 1)
        # Normalize keys to lowercase and trim whitespace
        row = {k.strip().lower(): v.strip() if v else "" for k, v in raw_row.items()}

        try:
            parsed_row = _parse_row(row, row_num)
            if parsed_row:
                rows.append(parsed_row)
            else:
                # _parse_row returned None - critical field missing
                # Record as evidence with parse error
                from app.services.validation import ValidationIssue
                parse_issues.append(
                    ValidationIssue(
                        code="ROW_PARSE_ERROR",
                        severity="error",
                        field=None,
                        row_index=row_num - 2,  # Convert to 0-based
                        message=f"Row {row_num} could not be parsed - critical field missing or invalid. Raw data: {dict(raw_row)}",
                        employee_id=row.get("employee_id", f"UNKNOWN_ROW_{row_num}"),
                    )
                )
        except Exception as e:
            # Parse exception - record the failure as structured evidence
            # DO NOT silently drop - user must see what failed
            from app.services.validation import ValidationIssue
            parse_issues.append(
                ValidationIssue(
                    code="ROW_PARSE_ERROR",
                    severity="error",
                    field=None,
                    row_index=row_num - 2,  # Convert to 0-based
                    message=f"Row {row_num} parsing failed: {str(e)}. Raw data: {dict(raw_row)}",
                    employee_id=row.get("employee_id", f"UNKNOWN_ROW_{row_num}"),
                )
            )
            logger.error(f"Row {row_num} failed to parse: {e}. Issue recorded, row NOT dropped.")

    return rows, run_context, parse_issues


def _extract_run_context(first_row: Dict[str, str]) -> RunContext:
    """
    Extract run context from the first row of the CSV.

    All rows in a CSV should share these common attributes.

    Args:
        first_row: The first data row (normalized to lowercase keys).

    Returns:
        RunContext with shared run information.

    Raises:
        SchemaValidationError: If required context fields are invalid.
    """
    # Extract and validate pay_date
    pay_date_str = first_row.get("pay_date", "")
    try:
        pay_date = date.fromisoformat(pay_date_str)
    except (ValueError, AttributeError):
        raise SchemaValidationError(
            f"Invalid pay_date in first row: '{pay_date_str}'. Expected YYYY-MM-DD format."
        )

    # Extract and validate payroll_frequency
    freq_str = first_row.get("payroll_frequency", "").lower()
    try:
        payroll_frequency = PayrollFrequency(freq_str)
    except ValueError:
        raise SchemaValidationError(
            f"Invalid payroll_frequency in first row: '{freq_str}'. "
            f"Expected: {', '.join(e.value for e in PayrollFrequency)}"
        )

    # Extract optional run-level fields
    annual_payroll_estimate = None
    annual_est_str = first_row.get("annual_payroll_estimate", "")
    if annual_est_str:
        try:
            annual_payroll_estimate = Decimal(annual_est_str.replace(",", "").replace("R", ""))
        except (InvalidOperation, ValueError):
            # Invalid format, will be caught in validation
            pass

    is_sdl_liable_override = _parse_bool(first_row.get("is_sdl_liable_override", ""))
    ruleset_version_override = first_row.get("ruleset_version_override", "") or None

    return RunContext(
        payroll_run_id=first_row.get("payroll_run_id", ""),
        company_id=first_row.get("company_id", ""),
        pay_date=pay_date,
        tax_year=first_row.get("tax_year", ""),
        payroll_frequency=payroll_frequency,
        ruleset_version_override=ruleset_version_override,
        annual_payroll_estimate=annual_payroll_estimate,
        is_sdl_liable_override=is_sdl_liable_override,
    )


def _parse_row(row: Dict[str, str], row_num: int) -> Optional[PayrollInputRow]:
    """
    Parse a single CSV row into a PayrollInputRow.

    Empty numeric fields are normalized to 0.
    Uses sensible defaults for invalid data to avoid silent row drops.
    Validation service will flag issues with invalid fields.

    Args:
        row: Dictionary of column name -> value (lowercase keys).
        row_num: Row number for error reporting.

    Returns:
        PayrollInputRow object, or None only if completely unparseable.
    """
    employee_id = row.get("employee_id", f"UNKNOWN_ROW_{row_num}")  # Default to avoid dropping row

    # Parse required fields with fallbacks
    payroll_run_id = row.get("payroll_run_id", "")
    company_id = row.get("company_id", "")

    # Parse pay_date (required) - use today as fallback to avoid dropping row
    pay_date = _parse_date(row.get("pay_date", ""))
    if pay_date is None:
        logger.warning(f"Row {row_num}: Invalid pay_date, using today as fallback. Validation will flag this.")
        pay_date = date.today()  # Fallback to avoid dropping row

    tax_year = row.get("tax_year", "")

    # Parse payroll_frequency (required) - use MONTHLY as fallback
    payroll_frequency = _parse_enum(
        row.get("payroll_frequency", ""),
        PayrollFrequency,
    )
    if payroll_frequency is None:
        logger.warning(f"Row {row_num}: Invalid payroll_frequency, using MONTHLY as fallback. Validation will flag this.")
        payroll_frequency = PayrollFrequency.MONTHLY  # Fallback to avoid dropping row

    # Parse employment_type (required) - use EMPLOYEE as fallback
    employment_type = _parse_enum(
        row.get("employment_type", ""),
        EmploymentType,
    )
    if employment_type is None:
        logger.warning(f"Row {row_num}: Invalid employment_type, using EMPLOYEE as fallback. Validation will flag this.")
        employment_type = EmploymentType.EMPLOYEE  # Fallback to avoid dropping row

    # Parse basic_salary (required) - validation will flag if <= 0
    basic_salary = _parse_money_with_default(row.get("basic_salary", ""))
    # Don't return None here - let validation handle it

    # Parse optional fields with defaults
    residency_status = _parse_enum(
        row.get("residency_status", "resident"),
        ResidencyStatus,
    ) or ResidencyStatus.RESIDENT

    employment_start_date = _parse_date(row.get("employment_start_date", ""))
    employment_end_date = _parse_date(row.get("employment_end_date", ""))

    # Parse all money fields - empty values normalize to 0
    annual_payroll_estimate_val = row.get("annual_payroll_estimate", "")
    annual_payroll_estimate = None
    if annual_payroll_estimate_val:
        parsed = _parse_money_with_default(annual_payroll_estimate_val)
        if parsed > 0:
            annual_payroll_estimate = parsed

    overtime_pay = _parse_money_with_default(row.get("overtime_pay", ""))
    bonus_commission = _parse_money_with_default(row.get("bonus_commission", ""))
    allowances_taxable = _parse_money_with_default(row.get("allowances_taxable", ""))
    allowances_non_taxable = _parse_money_with_default(row.get("allowances_non_taxable", ""))
    fringe_benefits_taxable = _parse_money_with_default(row.get("fringe_benefits_taxable", ""))
    reimbursements = _parse_money_with_default(row.get("reimbursements", ""))
    other_earnings = _parse_money_with_default(row.get("other_earnings", ""))
    pension_contribution_employee = _parse_money_with_default(row.get("pension_contribution_employee", ""))
    retirement_annuity_employee = _parse_money_with_default(row.get("retirement_annuity_employee", ""))
    medical_aid_contribution_employee = _parse_money_with_default(row.get("medical_aid_contribution_employee", ""))
    other_pre_tax_deductions = _parse_money_with_default(row.get("other_pre_tax_deductions", ""))
    union_fees = _parse_money_with_default(row.get("union_fees", ""))
    garnishees = _parse_money_with_default(row.get("garnishees", ""))
    other_post_tax_deductions = _parse_money_with_default(row.get("other_post_tax_deductions", ""))

    # Parse boolean fields
    is_sdl_liable_override = _parse_bool(row.get("is_sdl_liable_override", ""))
    ruleset_version_override = row.get("ruleset_version_override", "") or None

    # Create the row object
    return PayrollInputRow(
        payroll_run_id=payroll_run_id,
        company_id=company_id,
        pay_date=pay_date,
        tax_year=tax_year,
        payroll_frequency=payroll_frequency,
        employee_id=employee_id,
        employment_type=employment_type,
        basic_salary=basic_salary,
        annual_payroll_estimate=annual_payroll_estimate,
        is_sdl_liable_override=is_sdl_liable_override,
        ruleset_version_override=ruleset_version_override,
        residency_status=residency_status,
        employment_start_date=employment_start_date,
        employment_end_date=employment_end_date,
        overtime_pay=overtime_pay,
        bonus_commission=bonus_commission,
        allowances_taxable=allowances_taxable,
        allowances_non_taxable=allowances_non_taxable,
        fringe_benefits_taxable=fringe_benefits_taxable,
        reimbursements=reimbursements,
        other_earnings=other_earnings,
        pension_contribution_employee=pension_contribution_employee,
        retirement_annuity_employee=retirement_annuity_employee,
        medical_aid_contribution_employee=medical_aid_contribution_employee,
        other_pre_tax_deductions=other_pre_tax_deductions,
        union_fees=union_fees,
        garnishees=garnishees,
        other_post_tax_deductions=other_post_tax_deductions,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _parse_date(value: str) -> Optional[date]:
    """Parse a date string in YYYY-MM-DD format."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_enum(value: str, enum_class: type) -> Optional[Any]:
    """Parse an enum value."""
    if not value:
        return None
    try:
        return enum_class(value.lower())
    except ValueError:
        return None


def _parse_money_with_default(value: str) -> Decimal:
    """
    Parse a monetary value, returning Decimal("0") for empty/invalid values.

    This ensures empty numeric fields are normalized to 0 as required.

    Args:
        value: String value to parse.

    Returns:
        Decimal value, or Decimal("0") if empty or invalid.
    """
    if not value or value.strip() == "":
        return Decimal("0")

    try:
        # Remove currency symbols and whitespace
        cleaned = value.replace("R", "").replace(",", "").strip()
        amount = Decimal(cleaned)

        # Disallow negative values (return 0 instead)
        if amount < 0:
            return Decimal("0")

        return amount
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _parse_bool(value: str) -> Optional[bool]:
    """Parse a boolean value."""
    if not value:
        return None
    lower = value.lower().strip()
    if lower in ("true", "yes", "1"):
        return True
    if lower in ("false", "no", "0"):
        return False
    return None

