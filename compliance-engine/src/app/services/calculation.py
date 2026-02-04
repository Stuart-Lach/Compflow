"""
Calculation Service

Orchestrates PAYE, UIF, and SDL computations.
Returns per-employee results plus employer totals, including ruleset_version_used.

All calculations are deterministic and based on the ruleset data.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

from app.domain.models import (
    EmployeeResult,
    PayrollFrequency,
    PayrollInputRow,
    RunTotals,
)
from app.rulesets.registry import RulesetInfo
from app.services.validation import is_sdl_liable, is_uif_applicable


@dataclass
class CalculationResult:
    """
    Complete calculation result including per-employee results and totals.
    """

    employee_results: List[EmployeeResult]
    totals: RunTotals
    ruleset_version_used: str


def calculate_compliance_run(
    rows: List[PayrollInputRow],
    ruleset: RulesetInfo,
) -> CalculationResult:
    """
    Orchestrate all compliance calculations for a payroll run.

    This is the main entry point for calculations. It:
    1. Calculates PAYE, UIF, SDL for each employee
    2. Aggregates totals
    3. Returns structured result with ruleset version

    Args:
        rows: List of validated payroll input rows.
        ruleset: The ruleset to use for calculations.

    Returns:
        CalculationResult with employee results, totals, and ruleset version.
    """
    # Calculate per-employee results
    employee_results = []
    for row in rows:
        result = calculate_employee(row, ruleset)
        employee_results.append(result)

    # Calculate aggregated totals
    totals = calculate_totals(employee_results)

    # Return structured result
    return CalculationResult(
        employee_results=employee_results,
        totals=totals,
        ruleset_version_used=ruleset.ruleset_version_id,
    )


def calculate_employee(
    row: PayrollInputRow,
    ruleset: RulesetInfo,
) -> EmployeeResult:
    """
    Calculate compliance outputs for a single employee.

    Args:
        row: The payroll input row.
        ruleset: The ruleset to use for calculations.

    Returns:
        EmployeeResult with computed values.
    """
    # Calculate gross and taxable income
    gross_income = row.gross_income
    taxable_income = row.taxable_income

    # Ensure taxable income is not negative
    if taxable_income < 0:
        taxable_income = Decimal("0")

    # Calculate PAYE
    paye = calculate_paye(taxable_income, row.payroll_frequency, ruleset)

    # Calculate UIF
    if is_uif_applicable(row):
        uif_employee, uif_employer = calculate_uif(gross_income, ruleset)
    else:
        uif_employee = Decimal("0")
        uif_employer = Decimal("0")

    # Calculate SDL
    if is_sdl_liable(row, ruleset):
        sdl = calculate_sdl(gross_income, ruleset)
    else:
        sdl = Decimal("0")

    # Calculate net pay (gross - PAYE - UIF employee - post-tax deductions)
    net_pay = (
        gross_income
        - paye
        - uif_employee
        - row.post_tax_deductions
    )

    # Ensure net pay is not negative
    if net_pay < 0:
        net_pay = Decimal("0")

    # Calculate total employer cost (gross + UIF employer + SDL)
    total_employer_cost = gross_income + uif_employer + sdl

    # Apply deterministic rounding to 2 decimal places (ROUND_HALF_UP) to match Excel behavior
    # Round per-employee first, then sum rounded values for totals (not sum then round)
    return EmployeeResult(
        employee_id=row.employee_id,
        gross_income=_round_currency(gross_income),
        taxable_income=_round_currency(taxable_income),
        paye=_round_currency(paye),
        uif_employee=_round_currency(uif_employee),
        uif_employer=_round_currency(uif_employer),
        sdl=_round_currency(sdl),
        net_pay=_round_currency(net_pay),
        total_employer_cost=_round_currency(total_employer_cost),
        pre_tax_deductions=_round_currency(row.pre_tax_deductions),
        post_tax_deductions=_round_currency(row.post_tax_deductions),
    )


def calculate_paye(
    taxable_income: Decimal,
    frequency: PayrollFrequency,
    ruleset: RulesetInfo,
) -> Decimal:
    """
    Calculate PAYE (Pay-As-You-Earn) tax.

    Uses the tax brackets from the ruleset. Converts period income to
    annual for bracket lookup, then converts back to period amount.

    Args:
        taxable_income: Taxable income for the period.
        frequency: Payroll frequency.
        ruleset: The ruleset containing tax brackets.

    Returns:
        PAYE amount for the period.
    """
    # Current PAYE method (workbook-aligned):
    # 1) Annualize period taxable income
    # 2) Apply annual bracket base tax + marginal rate
    # 3) Subtract primary rebate
    # 4) De-annualize back to period amount
    if taxable_income <= 0:
        return Decimal("0")

    periods_per_year = frequency.periods_per_year
    annual_income = taxable_income * periods_per_year

    brackets = ruleset.module.TAX_BRACKETS_ANNUAL
    rebates = ruleset.module.REBATES

    annual_tax = Decimal("0")

    for bracket in brackets:
        max_income = bracket.max_income
        in_lower = annual_income >= bracket.min_income
        in_upper = max_income is None or annual_income <= max_income
        if in_lower and in_upper:
            taxable_in_bracket = annual_income - bracket.min_income
            annual_tax = bracket.base_tax + (taxable_in_bracket * bracket.rate)
            break

    annual_tax -= rebates.get("primary", Decimal("0"))
    if annual_tax < 0:
        annual_tax = Decimal("0")

    return annual_tax / periods_per_year


def calculate_uif(
    gross_income: Decimal,
    ruleset: RulesetInfo,
) -> Tuple[Decimal, Decimal]:
    """
    Calculate UIF (Unemployment Insurance Fund) contributions.

    Args:
        gross_income: Gross income for the period.
        ruleset: The ruleset containing UIF rates and caps.

    Returns:
        Tuple of (employee contribution, employer contribution).
    """
    # Get UIF config
    employee_rate = ruleset.module.UIF_EMPLOYEE_RATE
    employer_rate = ruleset.module.UIF_EMPLOYER_RATE
    monthly_cap = ruleset.module.UIF_MONTHLY_CAP

    # Apply cap
    uif_basis = min(gross_income, monthly_cap)

    # Calculate contributions and round to 2 decimals (ROUND_HALF_UP)
    employee_contribution = _round_currency(uif_basis * employee_rate)
    employer_contribution = _round_currency(uif_basis * employer_rate)

    return employee_contribution, employer_contribution


def calculate_sdl(
    gross_income: Decimal,
    ruleset: RulesetInfo,
) -> Decimal:
    """
    Calculate SDL (Skills Development Levy).

    Args:
        gross_income: Gross income for the period.
        ruleset: The ruleset containing SDL rate.

    Returns:
        SDL amount (rounded to 2 decimals).
    """
    sdl_rate = ruleset.module.SDL_RATE
    return _round_currency(gross_income * sdl_rate)


def calculate_totals(results: List[EmployeeResult]) -> RunTotals:
    """
    Calculate aggregated totals from employee results.

    IMPORTANT: Totals are calculated by summing pre-rounded per-employee values,
    then rounding the sum. This matches Excel behavior and ensures deterministic results.

    Args:
        results: List of employee results (already rounded per-employee).

    Returns:
        RunTotals with aggregated values.
    """
    return RunTotals(
        employee_count=len(results),
        # Sum already-rounded employee values, then round the total
        total_gross=_round_currency(sum(r.gross_income for r in results)),
        total_taxable=_round_currency(sum(r.taxable_income for r in results)),
        total_paye=_round_currency(sum(r.paye for r in results)),
        total_uif_employee=_round_currency(sum(r.uif_employee for r in results)),
        total_uif_employer=_round_currency(sum(r.uif_employer for r in results)),
        total_sdl=_round_currency(sum(r.sdl for r in results)),
        total_net_pay=_round_currency(sum(r.net_pay for r in results)),
        total_employer_cost=_round_currency(sum(r.total_employer_cost for r in results)),
    )


def _round_currency(value: Decimal) -> Decimal:
    """
    Round a currency value to 2 decimal places using ROUND_HALF_UP.

    This matches Excel's ROUND() function behavior for deterministic results.
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
