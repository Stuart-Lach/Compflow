"""
Comprehensive test of ingestion contracts.
"""

import sys
sys.path.insert(0, 'src')

from app.services.ingestion import parse_csv, parse_csv_with_issues
from decimal import Decimal

def test_parse_csv_returns_2_values():
    """Test parse_csv returns exactly 2 values."""
    csv_content = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00
"""

    result = parse_csv(csv_content)
    assert len(result) == 2, f"Expected 2 values, got {len(result)}"
    rows, run_context = result
    assert len(rows) == 1
    assert run_context.payroll_run_id == "RUN001"
    print("✓ parse_csv returns 2 values")


def test_parse_csv_with_issues_returns_3_values():
    """Test parse_csv_with_issues returns exactly 3 values."""
    csv_content = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00
"""

    result = parse_csv_with_issues(csv_content)
    assert len(result) == 3, f"Expected 3 values, got {len(result)}"
    rows, run_context, parse_issues = result
    assert len(rows) == 1
    assert run_context.payroll_run_id == "RUN001"
    assert len(parse_issues) == 0
    print("✓ parse_csv_with_issues returns 3 values")


def test_parse_issues_structure():
    """Test parse issues have correct structure."""
    # Create CSV with an empty row that might trigger parse error
    csv_content = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00
RUN001,COMP001,2025-03-25,2025_26,monthly,,,
"""

    rows, run_context, parse_issues = parse_csv_with_issues(csv_content)

    # At least first row should parse
    assert len(rows) >= 1
    print(f"✓ Parsed {len(rows)} rows")

    # Check parse issues structure if any
    if parse_issues:
        issue = parse_issues[0]
        assert hasattr(issue, 'code')
        assert hasattr(issue, 'severity')
        assert hasattr(issue, 'row_index')
        assert hasattr(issue, 'message')
        assert issue.code == "ROW_PARSE_ERROR"
        assert issue.severity == "error"
        assert "Raw data:" in issue.message
        print(f"✓ Parse issue has correct structure: {issue.code}")
    else:
        print("✓ No parse issues (rows parsed with fallbacks)")


def test_multiple_rows():
    """Test parsing multiple valid rows."""
    csv_content = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP002,employee,65000.00
RUN001,COMP001,2025-03-25,2025_26,monthly,CON001,contractor,35000.00
"""

    rows, run_context = parse_csv(csv_content)
    assert len(rows) == 3
    assert rows[0].employee_id == "EMP001"
    assert rows[1].employee_id == "EMP002"
    assert rows[2].employee_id == "CON001"
    print("✓ Multiple rows parsed correctly")


def test_optional_fields():
    """Test parsing with optional fields."""
    csv_content = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary,overtime_pay,pension_contribution_employee
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00,2500.00,3600.00
"""

    rows, run_context = parse_csv(csv_content)
    assert len(rows) == 1
    assert rows[0].overtime_pay == Decimal("2500.00")
    assert rows[0].pension_contribution_employee == Decimal("3600.00")
    print("✓ Optional fields parsed correctly")


if __name__ == "__main__":
    print("="*60)
    print("TESTING INGESTION CONTRACTS")
    print("="*60)
    print()

    try:
        test_parse_csv_returns_2_values()
        test_parse_csv_with_issues_returns_3_values()
        test_parse_issues_structure()
        test_multiple_rows()
        test_optional_fields()

        print()
        print("="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)

    except Exception as e:
        print()
        print("="*60)
        print(f"✗ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

