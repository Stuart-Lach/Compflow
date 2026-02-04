"""
Pydantic schemas for API request/response validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Common Schemas
# ============================================================================


class IssueCount(BaseModel):
    """Count of validation issues by severity."""

    errors: int = 0
    warnings: int = 0


class Totals(BaseModel):
    """Aggregated totals for a compliance run."""

    model_config = ConfigDict(coerce_numbers_to_str=False)

    employee_count: int
    total_gross: Decimal
    total_taxable: Decimal
    total_paye: Decimal
    total_uif_employee: Decimal
    total_uif_employer: Decimal
    total_sdl: Decimal
    total_net_pay: Decimal
    total_employer_cost: Decimal


# ============================================================================
# Health Schemas
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    current_ruleset: str
    timestamp: datetime


# ============================================================================
# Ruleset Schemas
# ============================================================================


class RulesetMetadata(BaseModel):
    """Ruleset metadata."""

    ruleset_id: str
    description: str
    effective_from: date
    effective_to: Optional[date]
    is_current: bool


class RulesetListResponse(BaseModel):
    """Response for listing rulesets."""

    rulesets: List[RulesetMetadata]


class TaxBracket(BaseModel):
    """Tax bracket definition."""

    min_income: Decimal
    max_income: Optional[Decimal]
    rate: Decimal
    base_tax: Decimal


class RulesetDetailResponse(BaseModel):
    """Detailed ruleset information including tables."""

    ruleset_id: str
    description: str
    effective_from: date
    effective_to: Optional[date]
    is_current: bool
    tax_brackets: List[TaxBracket]
    uif_rate_employee: Decimal
    uif_rate_employer: Decimal
    uif_monthly_cap: Decimal
    sdl_rate: Decimal
    sdl_annual_threshold: Decimal


# ============================================================================
# Run Schemas
# ============================================================================


class ValidationIssueResponse(BaseModel):
    """Validation issue in response."""

    row: Optional[int]
    employee_id: Optional[str]
    severity: str
    code: str
    message: str
    field: Optional[str] = None


class EmployeeResultResponse(BaseModel):
    """Employee result in response."""

    model_config = ConfigDict(coerce_numbers_to_str=False)

    employee_id: str
    gross_income: Decimal
    taxable_income: Decimal
    paye: Decimal
    uif_employee: Decimal
    uif_employer: Decimal
    sdl: Decimal
    net_pay: Decimal
    total_employer_cost: Decimal


class RunCreateResponse(BaseModel):
    """Response after creating a compliance run."""

    run_id: str
    payroll_run_id: str  # From CSV input
    status: str
    ruleset_version_used: str
    created_at: datetime
    issue_count: IssueCount
    totals: Optional[Totals] = None


class RunDetailResponse(BaseModel):
    """Detailed run information."""

    run_id: str
    payroll_run_id: str  # From CSV input
    company_id: str
    pay_date: date
    tax_year: str
    payroll_frequency: str
    ruleset_version_used: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    issue_count: IssueCount
    totals: Optional[Totals] = None


class RunResultsResponse(BaseModel):
    """Run results with per-employee breakdown."""

    run_id: str
    payroll_run_id: str  # From CSV input
    ruleset_version_used: str  # For auditability
    results: List[EmployeeResultResponse]
    totals: Optional[Totals] = None


class RunErrorsResponse(BaseModel):
    """Validation issues for a run."""

    run_id: str
    payroll_run_id: str  # From CSV input
    issues: List[ValidationIssueResponse]


# ============================================================================
# Error Schemas
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

