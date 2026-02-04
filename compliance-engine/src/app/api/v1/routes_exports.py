"""
Export endpoints for compliance runs.

Provides CSV and PDF exports of compliance run results.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.exports import build_employee_breakdown_csv, build_summary_pdf
from app.storage.db import get_session


router = APIRouter()


@router.get("/runs/{run_id}/export/employee-breakdown.csv")
async def export_employee_breakdown_csv(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Export employee breakdown as CSV.

    Returns a CSV file containing per-employee compliance calculations:
    - employee_id
    - gross_income
    - taxable_income
    - paye
    - uif_employee
    - uif_employer
    - sdl
    - net_pay
    - total_employer_cost

    All currency values are formatted to 2 decimal places.
    """
    try:
        csv_bytes = await build_employee_breakdown_csv(session, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    filename = f"employee_breakdown_{run_id}.csv"

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/runs/{run_id}/export/summary.pdf")
async def export_summary_pdf(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Export compliance summary as PDF.

    Returns a 1-page PDF containing:
    - Run information (company, payroll run ID, pay date, tax year, frequency)
    - Ruleset version used
    - Employee count
    - Financial totals (gross, taxable, PAYE, UIF, SDL, net pay, employer cost)
    - Generation timestamp

    All currency values are formatted with "R" prefix and 2 decimal places.
    """
    try:
        pdf_bytes = await build_summary_pdf(session, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    filename = f"compliance_summary_{run_id}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
