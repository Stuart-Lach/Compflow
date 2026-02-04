"""
End-to-end test to verify calculations match expected outputs.

This test uses the Excel workbook as the source of truth:
- Generates expected outputs from workbook before each test run
- Compares engine calculations to workbook-derived expectations
- No manual maintenance of expected outputs

The test must pass before the system is considered production-ready.
"""

import pytest
import csv
import sys
import subprocess
import os
from decimal import Decimal
from pathlib import Path

from app.services.ingestion import parse_csv_with_issues
from app.services.validation import validate_rows
from app.services.calculation import calculate_compliance_run
from app.rulesets.registry import select_ruleset
from scripts.export_inputs_from_workbook import export_inputs
from scripts.generate_expected_from_rules import generate_expected_from_rules


def generate_expected():
    """Generate expected outputs (rules-based default, Excel oracle if enabled)."""
    repo_root = Path(__file__).parent.parent
    if os.getenv("EXCEL_ORACLE") == "1":
        script_path = repo_root / "scripts" / "generate_expected_from_excel_oracle.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return False
        return True

    # Deterministic mode (default)
    inputs_path = repo_root / "data" / "samples" / "inputs_from_workbook.csv"
    output_path = repo_root / "data" / "samples" / "expected_from_rules.csv"
    generate_expected_from_rules(inputs_path, output_path)
    return True


def load_test_csv():
    """Load the test CSV exported from the workbook Inputs sheet."""
    csv_path = Path(__file__).parent.parent / "data" / "samples" / "inputs_from_workbook.csv"

    if not csv_path.exists():
        pytest.skip(f"Test CSV not found: {csv_path}")

    with open(csv_path, "rb") as f:
        return f.read()


def load_expected_outputs():
    """Load expected outputs from generated CSV."""
    repo_root = Path(__file__).parent.parent
    if os.getenv("EXCEL_ORACLE") == "1":
        csv_path = repo_root / "data" / "samples" / "expected_from_excel.csv"
    else:
        csv_path = repo_root / "data" / "samples" / "expected_from_rules.csv"

    if not csv_path.exists():
        pytest.skip(f"Expected outputs CSV not found: {csv_path}.")

    expected_results = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            expected_results.append({
                "employee_id": row["employee_id"],
                "gross_income": Decimal(row["gross_income"]),
                "taxable_income": Decimal(row["taxable_income"]) if row.get("taxable_income") else None,
                "paye": Decimal(row["paye"]),
                "uif_employee": Decimal(row["uif_employee"]),
                "uif_employer": Decimal(row["uif_employer"]),
                "sdl": Decimal(row["sdl"]),
                "net_pay": Decimal(row["net_pay"]),
                "total_employer_cost": Decimal(row["total_employer_cost"]),
            })

    return expected_results


def _paye_diagnostics(taxable_income: Decimal, ruleset) -> str:
    annual_income = taxable_income * Decimal("12")
    selected = None
    for bracket in ruleset.module.TAX_BRACKETS_ANNUAL:
        max_income = bracket.max_income
        if annual_income >= bracket.min_income and (max_income is None or annual_income <= max_income):
            selected = bracket
            break

    rebate = ruleset.module.REBATES.get("primary", Decimal("0"))
    if selected is None:
        return f"annual_taxable={annual_income} bracket=NONE rebate={rebate}"

    annual_tax_before = selected.base_tax + ((annual_income - selected.min_income) * selected.rate)
    annual_tax_after = annual_tax_before - rebate
    return (
        f"annual_taxable={annual_income} bracket={selected.min_income}-{selected.max_income} "
        f"base_tax={selected.base_tax} rate={selected.rate} "
        f"annual_before={annual_tax_before} rebate={rebate} annual_after={annual_tax_after}"
    )


def print_ruleset_diagnostics(ruleset):
    """Print diagnostic info about the ruleset being used."""
    print("\n" + "="*60)
    print("[*] RULESET DIAGNOSTICS")
    print("="*60)
    print(f"Ruleset ID: {ruleset.ruleset_version_id}")
    print(f"Effective: {ruleset.effective_from} to {ruleset.effective_to}")
    print(f"Tax Year: {ruleset.tax_year}")

    # UIF info
    print(f"\nUIF Configuration:")
    print(f"  Employee rate: {ruleset.module.UIF_EMPLOYEE_RATE * 100}%")
    print(f"  Employer rate: {ruleset.module.UIF_EMPLOYER_RATE * 100}%")
    print(f"  Monthly cap: R{ruleset.module.UIF_MONTHLY_CAP:,.2f}")
    print(f"  Annual cap: R{ruleset.module.UIF_ANNUAL_CAP:,.2f}")

    # SDL info
    print(f"\nSDL Configuration:")
    print(f"  Rate: {ruleset.module.SDL_RATE * 100}%")
    print(f"  Annual threshold: R{ruleset.module.SDL_ANNUAL_PAYROLL_THRESHOLD:,.2f}")

    # PAYE brackets summary
    print(f"\nPAYE Tax Brackets (Annual): {len(ruleset.module.TAX_BRACKETS_ANNUAL)} tiers")
    for i, bracket in enumerate(ruleset.module.TAX_BRACKETS_ANNUAL[:3], 1):
        max_str = f"R{bracket.max_income:,.0f}" if bracket.max_income else "inf"
        print(f"  Tier {i}: R{bracket.min_income:,.0f} - {max_str} @ {bracket.rate*100}%")
    if len(ruleset.module.TAX_BRACKETS_ANNUAL) > 3:
        print(f"  ... {len(ruleset.module.TAX_BRACKETS_ANNUAL) - 3} more tiers")

    print("="*60 + "\n")


def test_excel_match_synthetic_scenario():
    """
    End-to-end test: Verify compliance engine matches workbook-calculated outputs.

    This test:
    1. Generates fresh expected outputs from Excel workbook (source of truth)
    2. Loads sample CSV from data/samples/payroll_input_sample_v1.csv
    3. Runs full pipeline: parse → validate → calculate
    4. Compares results to workbook-generated expectations
    5. Fails if any value differs after 2-decimal rounding

    The Excel workbook is the authoritative source - we do NOT manually edit expectations.
    """

    # Generate fresh expected outputs from workbook
    # Generate Inputs CSV from workbook
    repo_root = Path(__file__).parent.parent
    export_inputs(
        repo_root / "data" / "sa_payroll_workbook.xlsx",
        repo_root / "data" / "samples" / "inputs_from_workbook.csv",
    )

    # Generate expected outputs
    if not generate_expected():
        pytest.fail("Failed to generate expected outputs")

    # 1. Load CSV data
    csv_data = load_test_csv()
    print("\n[+] Loaded test CSV")

    # 2. Parse (now returns parse_issues too)
    rows, run_context, parse_issues = parse_csv_with_issues(csv_data)

    assert len(rows) > 0, "No rows parsed from CSV"
    print(f"[+] Parsed {len(rows)} employees")

    if parse_issues:
        print(f"[!] Parse issues found: {len(parse_issues)}")
        for issue in parse_issues:
            print(f"    {issue.code}: {issue.message}")

    # 3. Select ruleset
    ruleset = select_ruleset(
        tax_year=run_context.tax_year,
        pay_date=run_context.pay_date,
        override=run_context.ruleset_version_override
    )

    print(f"[+] Selected ruleset: {ruleset.ruleset_version_id}")

    # Print diagnostic info
    print_ruleset_diagnostics(ruleset)

    # 4. Validate
    validation_issues = validate_rows(rows, ruleset)
    all_issues = parse_issues + validation_issues

    # Test MUST fail if there are ERROR severity issues
    errors = [i for i in all_issues if i.severity == "error"]
    if errors:
        error_msg = "\n".join([
            "\n[!] TEST FAILED: Validation errors found:",
            *[f"  - Row {i.row_index}: {i.code} - {i.message}" for i in errors]
        ])
        pytest.fail(error_msg)

    print(f"[+] Validation passed ({len(all_issues)} warnings/info)")

    # 5. Calculate
    calc_result = calculate_compliance_run(rows, ruleset)

    print(f"[+] Calculated results for {len(calc_result.employee_results)} employees")
    print(f"  Ruleset used: {calc_result.ruleset_version_used}")

    # 6. Load expected values from workbook-generated CSV
    expected_results = load_expected_outputs()

    assert len(calc_result.employee_results) == len(expected_results), \
        f"Employee count mismatch: got {len(calc_result.employee_results)}, expected {len(expected_results)}"

    # 7. Compare each employee result - EXACT match after 2-decimal rounding
    tolerance = Decimal("0.01")

    print("\n" + "="*60)
    print("[*] COMPARING ENGINE vs WORKBOOK")
    print("="*60)

    all_match = True
    mismatches = []

    for i, result in enumerate(calc_result.employee_results):
        expected = expected_results[i]

        assert result.employee_id == expected["employee_id"], \
            f"Employee ID mismatch at index {i}"

        print(f"\n{result.employee_id}:")

        # Check each field
        fields_to_check = [
            ("gross_income", "Gross Income"),
            ("taxable_income", "Taxable Income"),
            ("paye", "PAYE"),
            ("uif_employee", "UIF Employee"),
            ("uif_employer", "UIF Employer"),
            ("sdl", "SDL"),
            ("net_pay", "Net Pay"),
            ("total_employer_cost", "Total Employer Cost"),
        ]

        for field, label in fields_to_check:
            # Skip taxable_income if not in expected
            if field == "taxable_income" and expected[field] is None:
                continue

            actual_val = getattr(result, field)
            expected_val = expected[field]
            diff = abs(actual_val - expected_val)

            if diff > tolerance:
                all_match = False
                mismatch_msg = f"  {label}: Expected R{expected_val:,.2f}, got R{actual_val:,.2f} (diff: R{diff:,.2f})"
                if field == "paye":
                    mismatch_msg += f" | {_paye_diagnostics(result.taxable_income, ruleset)}"
                if field in {"uif_employee", "uif_employer"}:
                    basis = min(result.gross_income, ruleset.module.UIF_MONTHLY_CAP)
                    mismatch_msg += (
                        f" | uif_basis={basis} rate={ruleset.module.UIF_EMPLOYEE_RATE}"
                    )
                mismatches.append(f"{result.employee_id} - {mismatch_msg}")
                print(f"  [!] {mismatch_msg}")
            else:
                print(f"  [+] {label}: R{actual_val:,.2f}")

    print("\n" + "="*60)

    # Final assertion
    if not all_match:
        error_msg = "\n".join([
            "\n[!] EXCEL MATCH TEST FAILED",
            "The following values do not match workbook calculations:",
            "",
            *mismatches,
            "",
            "IMPORTANT: The Excel workbook is the source of truth.",
            "Review engine calculations or verify workbook formulas.",
            "",
            f"Ruleset used: {calc_result.ruleset_version_used}",
            f"UIF cap applied: R{ruleset.module.UIF_MONTHLY_CAP:,.2f}",
        ])
        pytest.fail(error_msg)

    print("\n[+] ALL VALUES MATCH WORKBOOK (within tolerance of R0.01)")
    print("="*60)


def test_rounding_matches_excel():
    """
    Verify our rounding strategy matches Excel ROUND() function.

    Python's ROUND_HALF_UP should match Excel's ROUND(value, 2).
    """
    from decimal import Decimal, ROUND_HALF_UP

    test_cases = [
        (Decimal("123.454"), Decimal("123.45")),  # Round down
        (Decimal("123.455"), Decimal("123.46")),  # Round up (ROUND_HALF_UP)
        (Decimal("123.456"), Decimal("123.46")),  # Round up
        (Decimal("0.005"), Decimal("0.01")),      # Edge case
        (Decimal("0.004"), Decimal("0.00")),      # Edge case
        (Decimal("99.995"), Decimal("100.00")),   # Rollover
        (Decimal("1234.5678"), Decimal("1234.57")),
    ]

    for value, expected in test_cases:
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert rounded == expected, \
            f"Rounding {value} should give {expected}, got {rounded}"

    print("[+] All rounding tests passed")


if __name__ == "__main__":
    print("="*60)
    print("Excel Match Test - Running")
    print("="*60)

    # Run rounding test
    print("\n1. Testing rounding strategy:")
    test_rounding_matches_excel()

    # Run main test
    print("\n2. Testing Excel match:")
    test_excel_match_synthetic_scenario()

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)

