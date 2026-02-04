"""
Tests for export services and endpoints.
"""

import pytest
from decimal import Decimal
from datetime import date

from app.domain.models import (
    ComplianceRun,
    EmployeeResult,
    PayrollFrequency,
    RunStatus,
    RunTotals,
)
from app.services.exports import build_employee_breakdown_csv, build_summary_pdf
from app.storage.repo_runs import RunRepository


@pytest.fixture
async def sample_run_with_results(db_session):
    """Create a sample compliance run with results."""
    from datetime import datetime

    run = ComplianceRun(
        run_id="TEST_RUN_001",
        payroll_run_id="PAYROLL_2025_001",
        company_id="COMP_TEST",
        pay_date=date(2025, 4, 1),
        tax_year="2025_26",
        payroll_frequency=PayrollFrequency.MONTHLY,
        ruleset_version_used="ZA_2025_26_v1",
        status=RunStatus.COMPLETED,
        created_at=datetime.utcnow(),
        results=[
            EmployeeResult(
                employee_id="EMP001",
                gross_income=Decimal("10000.00"),
                taxable_income=Decimal("10000.00"),
                paye=Decimal("723.74"),
                uif_employee=Decimal("100.00"),
                uif_employer=Decimal("100.00"),
                sdl=Decimal("100.00"),
                net_pay=Decimal("9176.26"),
                total_employer_cost=Decimal("10200.00"),
            ),
            EmployeeResult(
                employee_id="EMP002",
                gross_income=Decimal("25000.00"),
                taxable_income=Decimal("25000.00"),
                paye=Decimal("3483.06"),
                uif_employee=Decimal("177.12"),
                uif_employer=Decimal("177.12"),
                sdl=Decimal("250.00"),
                net_pay=Decimal("21339.82"),
                total_employer_cost=Decimal("25427.12"),
            ),
        ],
        issues=[],
        totals=RunTotals(
            employee_count=2,
            total_gross=Decimal("35000.00"),
            total_taxable=Decimal("35000.00"),
            total_paye=Decimal("4206.80"),
            total_uif_employee=Decimal("277.12"),
            total_uif_employer=Decimal("277.12"),
            total_sdl=Decimal("350.00"),
            total_net_pay=Decimal("30516.08"),
            total_employer_cost=Decimal("35627.12"),
        ),
    )

    repo = RunRepository(db_session)
    await repo.create_run(run)
    await db_session.commit()

    return run


@pytest.mark.asyncio
async def test_build_employee_breakdown_csv(db_session, sample_run_with_results):
    """Test CSV generation for employee breakdown."""
    run = sample_run_with_results

    csv_bytes = await build_employee_breakdown_csv(db_session, run.run_id)
    csv_content = csv_bytes.decode('utf-8')

    # Check header
    assert "employee_id,gross_income,taxable_income,paye,uif_employee,uif_employer,sdl,net_pay,total_employer_cost" in csv_content

    # Check data rows
    lines = csv_content.strip().split('\n')
    assert len(lines) == 3  # Header + 2 data rows

    # Check first employee
    assert "EMP001" in csv_content
    assert "10000.00" in csv_content
    assert "723.74" in csv_content
    assert "100.00" in csv_content

    # Check second employee
    assert "EMP002" in csv_content
    assert "25000.00" in csv_content
    assert "3483.06" in csv_content
    assert "177.12" in csv_content


@pytest.mark.asyncio
async def test_build_employee_breakdown_csv_run_not_found(db_session):
    """Test CSV generation with non-existent run."""
    with pytest.raises(ValueError, match="Run not found"):
        await build_employee_breakdown_csv(db_session, "NONEXISTENT")


@pytest.mark.asyncio
async def test_build_summary_pdf(db_session, sample_run_with_results):
    """Test PDF generation for compliance summary."""
    run = sample_run_with_results

    pdf_bytes = await build_summary_pdf(db_session, run.run_id)

    # Check PDF signature
    assert pdf_bytes.startswith(b'%PDF'), "PDF should start with %PDF signature"
    assert len(pdf_bytes) > 1000, "PDF should have substantial content"
    assert b'%%EOF' in pdf_bytes, "PDF should have EOF marker"

    # Check PDF contains ReportLab metadata
    assert b'ReportLab' in pdf_bytes



@pytest.mark.asyncio
async def test_build_summary_pdf_run_not_found(db_session):
    """Test PDF generation with non-existent run."""
    with pytest.raises(ValueError, match="Run not found"):
        await build_summary_pdf(db_session, "NONEXISTENT")


@pytest.mark.asyncio
async def test_export_csv_endpoint(client, db_session, sample_run_with_results):
    """Test CSV export endpoint."""
    run = sample_run_with_results

    response = client.get(f"/api/v1/runs/{run.run_id}/export/employee-breakdown.csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert run.run_id in response.headers["content-disposition"]

    content = response.content.decode('utf-8')
    assert "employee_id" in content
    assert "EMP001" in content
    assert "EMP002" in content


@pytest.mark.asyncio
async def test_export_csv_endpoint_not_found(client):
    """Test CSV export endpoint with non-existent run."""
    response = client.get("/api/v1/runs/NONEXISTENT/export/employee-breakdown.csv")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_export_pdf_endpoint(client, db_session, sample_run_with_results):
    """Test PDF export endpoint."""
    run = sample_run_with_results

    response = client.get(f"/api/v1/runs/{run.run_id}/export/summary.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert run.run_id in response.headers["content-disposition"]

    # Check PDF signature
    assert response.content.startswith(b'%PDF')
    assert len(response.content) > 1000


@pytest.mark.asyncio
async def test_export_pdf_endpoint_not_found(client):
    """Test PDF export endpoint with non-existent run."""
    response = client.get("/api/v1/runs/NONEXISTENT/export/summary.pdf")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_csv_format_correctness(db_session, sample_run_with_results):
    """Test CSV format has correct number of columns and decimal precision."""
    run = sample_run_with_results

    csv_bytes = await build_employee_breakdown_csv(db_session, run.run_id)
    csv_content = csv_bytes.decode('utf-8')

    lines = csv_content.strip().split('\n')

    # Check each line has 9 columns
    for line in lines:
        columns = line.split(',')
        assert len(columns) == 9, f"Expected 9 columns, got {len(columns)}"

    # Check decimal precision (all currency values should have .XX format)
    for line in lines[1:]:  # Skip header
        columns = line.split(',')
        for i in range(1, 9):  # All columns except employee_id are currency
            value = columns[i]
            assert '.' in value, f"Currency value should have decimal point: {value}"
            decimal_part = value.split('.')[1]
            assert len(decimal_part) == 2, f"Currency should have 2 decimal places: {value}"


@pytest.mark.asyncio
async def test_pdf_contains_all_required_sections(db_session, sample_run_with_results):
    """Test PDF contains all required sections and data."""
    run = sample_run_with_results

    pdf_bytes = await build_summary_pdf(db_session, run.run_id)

    # Check PDF structure
    assert pdf_bytes.startswith(b'%PDF'), "PDF should have valid header"
    assert b'%%EOF' in pdf_bytes, "PDF should have valid EOF"
    assert len(pdf_bytes) > 2000, "PDF should have substantial content with all sections"

    # Check PDF was created with ReportLab
    assert b'ReportLab' in pdf_bytes

    # PDF should have multiple pages/objects for content
    assert b'/Page' in pdf_bytes
    assert b'/Font' in pdf_bytes
