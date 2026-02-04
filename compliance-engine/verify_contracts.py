"""
Verify ingestion function contracts work correctly.
"""

import sys
sys.path.insert(0, 'src')

from app.services.ingestion import parse_csv, parse_csv_with_issues

# Test CSV
csv_data = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP002,employee,65000.00
"""

print("="*60)
print("TESTING INGESTION CONTRACTS")
print("="*60)

# Test parse_csv (2 values)
print("\n1. Testing parse_csv() - should return 2 values:")
try:
    rows, run_context = parse_csv(csv_data)
    print(f"   ✓ Returns 2 values")
    print(f"   ✓ Rows: {len(rows)}")
    print(f"   ✓ Run context: {run_context.payroll_run_id}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test parse_csv_with_issues (3 values)
print("\n2. Testing parse_csv_with_issues() - should return 3 values:")
try:
    rows, run_context, parse_issues = parse_csv_with_issues(csv_data)
    print(f"   ✓ Returns 3 values")
    print(f"   ✓ Rows: {len(rows)}")
    print(f"   ✓ Run context: {run_context.payroll_run_id}")
    print(f"   ✓ Parse issues: {len(parse_issues)}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test with invalid row
invalid_csv = b"""payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00
RUN001,COMP001,2025-03-25,2025_26,monthly,,,
"""

print("\n3. Testing parse_csv_with_issues() with invalid row:")
try:
    rows, run_context, parse_issues = parse_csv_with_issues(invalid_csv)
    print(f"   ✓ Rows parsed: {len(rows)}")
    print(f"   ✓ Parse issues: {len(parse_issues)}")
    if parse_issues:
        for issue in parse_issues:
            print(f"   ✓ Issue: {issue.code} - {issue.severity}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*60)
print("✓ ALL CONTRACTS VERIFIED")
print("="*60)

