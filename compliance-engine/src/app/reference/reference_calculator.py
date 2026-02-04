"""
Reference calculator for deterministic expected outputs.

This module is intentionally independent of app.services.calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from app.domain.models import EmploymentType, PayrollFrequency, PayrollInputRow


@dataclass(frozen=True)
class TaxBracket:
    min_income: Decimal
    max_income: Optional[Decimal]
    base_tax: Decimal
    rate: Decimal


@dataclass(frozen=True)
class ReferenceRuleset:
    brackets: list[TaxBracket]
    primary_rebate: Decimal
    uif_cap_monthly: Decimal
    uif_employee_rate: Decimal
    uif_employer_rate: Decimal
    sdl_rate: Decimal
    sdl_threshold_annual: Decimal


@dataclass(frozen=True)
class ReferenceEmployeeResult:
    employee_id: str
    gross_income: Decimal
    taxable_income: Decimal
    paye: Decimal
    uif_employee: Decimal
    uif_employer: Decimal
    sdl: Decimal
    net_pay: Decimal
    total_employer_cost: Decimal


def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def load_ruleset_from_json(data: dict) -> ReferenceRuleset:
    brackets: list[TaxBracket] = []
    for bracket in data.get("brackets", []):
        brackets.append(
            TaxBracket(
                min_income=Decimal(str(bracket["from_amount"])),
                max_income=(
                    Decimal(str(bracket["to_amount"]))
                    if bracket.get("to_amount") is not None
                    else None
                ),
                base_tax=Decimal(str(bracket["base_tax"])),
                rate=Decimal(str(bracket["marginal_rate"])),
            )
        )

    rebates = data.get("rebates", {})
    primary_rebate = Decimal(str(rebates.get("primary", 0)))

    uif = data.get("uif", {})
    uif_cap = uif.get("uif_ceiling_monthly") or uif.get("uif_ceiling_monthly_")
    if uif_cap is None:
        raise ValueError("UIF ceiling monthly not found in ruleset JSON")

    sdl = data.get("sdl", {})
    sdl_rate = sdl.get("sdl_rate")
    sdl_threshold = sdl.get("sdl_threshold_annual_payroll")
    if sdl_rate is None or sdl_threshold is None:
        raise ValueError("SDL parameters not found in ruleset JSON")

    return ReferenceRuleset(
        brackets=brackets,
        primary_rebate=primary_rebate,
        uif_cap_monthly=Decimal(str(uif_cap)),
        uif_employee_rate=Decimal(str(uif.get("uif_employee_rate", 0))),
        uif_employer_rate=Decimal(str(uif.get("uif_employer_rate", 0))),
        sdl_rate=Decimal(str(sdl_rate)),
        sdl_threshold_annual=Decimal(str(sdl_threshold)),
    )


def calculate_reference_results(
    rows: Iterable[PayrollInputRow],
    ruleset: ReferenceRuleset,
) -> list[ReferenceEmployeeResult]:
    results: list[ReferenceEmployeeResult] = []
    for row in rows:
        results.append(_calculate_employee(row, ruleset))
    return results


def _calculate_employee(row: PayrollInputRow, ruleset: ReferenceRuleset) -> ReferenceEmployeeResult:
    gross_income = row.gross_income
    taxable_income = row.taxable_income

    if taxable_income < 0:
        taxable_income = Decimal("0")

    paye = _calculate_paye(taxable_income, row.payroll_frequency, ruleset)

    if row.employment_type == EmploymentType.CONTRACTOR:
        uif_employee = Decimal("0")
        uif_employer = Decimal("0")
    else:
        uif_employee, uif_employer = _calculate_uif(gross_income, ruleset)

    if _is_sdl_liable(row, ruleset):
        sdl = round_money(gross_income * ruleset.sdl_rate)
    else:
        sdl = Decimal("0")

    net_pay = gross_income - paye - uif_employee - row.post_tax_deductions
    if net_pay < 0:
        net_pay = Decimal("0")

    total_employer_cost = gross_income + uif_employer + sdl

    return ReferenceEmployeeResult(
        employee_id=row.employee_id,
        gross_income=round_money(gross_income),
        taxable_income=round_money(taxable_income),
        paye=round_money(paye),
        uif_employee=round_money(uif_employee),
        uif_employer=round_money(uif_employer),
        sdl=round_money(sdl),
        net_pay=round_money(net_pay),
        total_employer_cost=round_money(total_employer_cost),
    )


def _calculate_paye(
    taxable_income: Decimal,
    frequency: PayrollFrequency,
    ruleset: ReferenceRuleset,
) -> Decimal:
    if taxable_income <= 0:
        return Decimal("0")

    periods_per_year = frequency.periods_per_year
    annual_income = taxable_income * periods_per_year

    annual_tax = Decimal("0")
    for bracket in ruleset.brackets:
        in_lower = annual_income >= bracket.min_income
        in_upper = bracket.max_income is None or annual_income <= bracket.max_income
        if in_lower and in_upper:
            annual_tax = bracket.base_tax + ((annual_income - bracket.min_income) * bracket.rate)
            break

    annual_tax = annual_tax - ruleset.primary_rebate
    if annual_tax < 0:
        annual_tax = Decimal("0")

    return annual_tax / periods_per_year


def _calculate_uif(
    gross_income: Decimal,
    ruleset: ReferenceRuleset,
) -> tuple[Decimal, Decimal]:
    basis = min(gross_income, ruleset.uif_cap_monthly)
    employee = round_money(basis * ruleset.uif_employee_rate)
    employer = round_money(basis * ruleset.uif_employer_rate)
    return employee, employer


def _is_sdl_liable(row: PayrollInputRow, ruleset: ReferenceRuleset) -> bool:
    if row.employment_type == EmploymentType.CONTRACTOR:
        return False

    if row.is_sdl_liable_override is not None:
        return row.is_sdl_liable_override

    if row.annual_payroll_estimate is not None:
        return row.annual_payroll_estimate >= ruleset.sdl_threshold_annual

    return True
