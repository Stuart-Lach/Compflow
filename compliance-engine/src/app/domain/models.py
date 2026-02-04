"""
Domain models for the Compliance Engine.

These are the core business objects, independent of API or storage concerns.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class PayrollFrequency(str, Enum):
    """Payroll frequency enumeration."""

    MONTHLY = "monthly"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"

    @property
    def periods_per_year(self) -> int:
        """Get number of pay periods per year."""
        return {
            PayrollFrequency.MONTHLY: 12,
            PayrollFrequency.WEEKLY: 52,
            PayrollFrequency.FORTNIGHTLY: 26,
        }[self]


class EmploymentType(str, Enum):
    """Employment type enumeration."""

    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"


class ResidencyStatus(str, Enum):
    """Tax residency status enumeration."""

    RESIDENT = "resident"
    NON_RESIDENT = "non_resident"


class RunStatus(str, Enum):
    """Compliance run status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    """Validation issue severity enumeration."""

    ERROR = "error"
    WARNING = "warning"


@dataclass
class PayrollInputRow:
    """
    Represents a single row from the payroll input CSV.
    All monetary values are Decimal for precision.
    """

    # Required fields
    payroll_run_id: str
    company_id: str
    pay_date: date
    tax_year: str
    payroll_frequency: PayrollFrequency
    employee_id: str
    employment_type: EmploymentType
    basic_salary: Decimal

    # Optional context fields
    annual_payroll_estimate: Optional[Decimal] = None
    is_sdl_liable_override: Optional[bool] = None
    ruleset_version_override: Optional[str] = None
    residency_status: ResidencyStatus = ResidencyStatus.RESIDENT
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None

    # Earnings (default to 0)
    overtime_pay: Decimal = Decimal("0")
    bonus_commission: Decimal = Decimal("0")
    allowances_taxable: Decimal = Decimal("0")
    allowances_non_taxable: Decimal = Decimal("0")
    fringe_benefits_taxable: Decimal = Decimal("0")
    reimbursements: Decimal = Decimal("0")
    other_earnings: Decimal = Decimal("0")

    # Pre-tax deductions (default to 0)
    pension_contribution_employee: Decimal = Decimal("0")
    retirement_annuity_employee: Decimal = Decimal("0")
    medical_aid_contribution_employee: Decimal = Decimal("0")
    other_pre_tax_deductions: Decimal = Decimal("0")

    # Post-tax deductions (default to 0)
    union_fees: Decimal = Decimal("0")
    garnishees: Decimal = Decimal("0")
    other_post_tax_deductions: Decimal = Decimal("0")

    @property
    def gross_income(self) -> Decimal:
        """Calculate gross income (taxable earnings + fringe benefits)."""
        return (
            self.basic_salary
            + self.overtime_pay
            + self.bonus_commission
            + self.allowances_taxable
            + self.fringe_benefits_taxable
            + self.other_earnings
        )

    @property
    def pre_tax_deductions(self) -> Decimal:
        """Calculate total pre-tax deductions."""
        return (
            self.pension_contribution_employee
            + self.retirement_annuity_employee
            + self.medical_aid_contribution_employee
            + self.other_pre_tax_deductions
        )

    @property
    def taxable_income(self) -> Decimal:
        """Calculate taxable income."""
        return self.gross_income - self.pre_tax_deductions

    @property
    def post_tax_deductions(self) -> Decimal:
        """Calculate total post-tax deductions."""
        return self.union_fees + self.garnishees + self.other_post_tax_deductions


@dataclass
class ValidationIssue:
    """Represents a validation error or warning."""

    row_number: Optional[int]
    employee_id: Optional[str]
    severity: IssueSeverity
    code: str
    message: str
    field: Optional[str] = None


@dataclass
class EmployeeResult:
    """Computed compliance results for a single employee."""

    employee_id: str
    gross_income: Decimal
    taxable_income: Decimal
    paye: Decimal
    uif_employee: Decimal
    uif_employer: Decimal
    sdl: Decimal
    net_pay: Decimal
    total_employer_cost: Decimal

    # Additional breakdown (optional)
    pre_tax_deductions: Decimal = Decimal("0")
    post_tax_deductions: Decimal = Decimal("0")


@dataclass
class RunTotals:
    """Aggregated totals for a compliance run."""

    employee_count: int
    total_gross: Decimal
    total_taxable: Decimal
    total_paye: Decimal
    total_uif_employee: Decimal
    total_uif_employer: Decimal
    total_sdl: Decimal
    total_net_pay: Decimal
    total_employer_cost: Decimal


@dataclass
class ComplianceRun:
    """Represents a complete compliance run with all data."""

    run_id: str
    payroll_run_id: str  # From CSV - external payroll system reference (audit trail)
    company_id: str
    pay_date: date
    tax_year: str
    payroll_frequency: PayrollFrequency
    ruleset_version_used: str
    status: RunStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Results
    results: List[EmployeeResult] = field(default_factory=list)
    issues: List[ValidationIssue] = field(default_factory=list)
    totals: Optional[RunTotals] = None

    # Evidence references
    raw_file_id: Optional[str] = None
    normalized_rows_id: Optional[str] = None

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

