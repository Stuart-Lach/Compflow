"""
Compliance run endpoints.

Handles CSV upload, validation, calculation, and results retrieval.
All responses include ruleset_version_used and payroll_run_id for auditability.
"""

import csv
import io
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schema import (
    IssueCount,
    RunCreateResponse,
    RunDetailResponse,
    RunErrorsResponse,
    RunResultsResponse,
    Totals,
    EmployeeResultResponse,
    ValidationIssueResponse,
)
from app.errors import SchemaValidationError
from app.rulesets.registry import select_ruleset
from app.services import (
    calculate_compliance_run,
    create_compliance_run,
    has_errors,
    parse_csv_with_issues,
    persist_compliance_run,
    store_raw_file,
    validate_rows,
)
from app.storage.db import get_session
from app.storage.repo_runs import RunRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/runs", response_model=RunCreateResponse)
async def create_compliance_run_endpoint(
    file: Annotated[UploadFile, File(description="Payroll CSV file")],
    session: AsyncSession = Depends(get_session),
) -> RunCreateResponse:
    """
    Upload a payroll CSV and create a compliance run.

    This endpoint:
    1. Parses the CSV
    2. Validates business rules
    3. Calculates PAYE, UIF, SDL
    4. Stores complete evidence
    5. Returns summary with ruleset_version_used

    Args:
        file: The uploaded CSV file.
        session: Database session.

    Returns:
        RunCreateResponse with run_id, payroll_run_id, ruleset_version_used, and totals.

    Raises:
        HTTPException: If schema validation fails or processing error occurs.
    """
    try:
        # Read file content
        content = await file.read()

        # Generate unique run ID
        run_id = generate_run_id()

        logger.info(f"Processing compliance run {run_id}")

        # Store raw file (evidence)
        raw_file_id = await store_raw_file(content, file.filename or "payroll.csv")

        # Parse CSV → (rows, run_context, parse_issues)
        try:
            rows, run_context, parse_issues = parse_csv_with_issues(content)
        except SchemaValidationError as e:
            raise HTTPException(status_code=400, detail=e.message)

        if not rows and not parse_issues:
            raise HTTPException(
                status_code=400,
                detail="No valid rows found in CSV after parsing.",
            )

        logger.info(
            f"Parsed {len(rows)} rows for company {run_context.company_id}, "
            f"pay_date {run_context.pay_date}, parse_issues: {len(parse_issues)}"
        )

        # Select ruleset based on tax_year and pay_date
        ruleset = select_ruleset(
            tax_year=run_context.tax_year,
            pay_date=run_context.pay_date,
            override=run_context.ruleset_version_override,
        )

        logger.info(f"Using ruleset {ruleset.ruleset_version_id} for run {run_id}")

        # Validate rows → issues
        validation_issues = validate_rows(rows, ruleset)

        # Combine parse issues with validation issues
        all_issues = parse_issues + validation_issues

        # Check for blocking errors
        if has_errors(all_issues):
            logger.warning(
                f"Run {run_id} has validation errors, creating failed run"
            )
            # Create failed run with no results
            run = create_compliance_run(
                run_id=run_id,
                run_context=run_context,
                results=[],
                issues=all_issues,
                totals=None,
                ruleset_version_used=ruleset.ruleset_version_id,
                raw_file_id=raw_file_id,
            )
            await persist_compliance_run(run)

            return RunCreateResponse(
                run_id=run.run_id,
                payroll_run_id=run_context.payroll_run_id,
                status=run.status.value,
                ruleset_version_used=run.ruleset_version_used,
                created_at=run.created_at,
                issue_count=IssueCount(
                    errors=run.error_count,
                    warnings=run.warning_count,
                ),
                totals=None,
            )

        # Calculate PAYE, UIF, SDL → CalculationResult
        calc_result = calculate_compliance_run(rows, ruleset)

        logger.info(
            f"Calculated results for {len(calc_result.employee_results)} employees: "
            f"Total PAYE: {calc_result.totals.total_paye}, "
            f"Total UIF: {calc_result.totals.total_uif_employee + calc_result.totals.total_uif_employer}, "
            f"Total SDL: {calc_result.totals.total_sdl}"
        )

        # Create compliance run (evidence)
        run = create_compliance_run(
            run_id=run_id,
            run_context=run_context,
            results=calc_result.employee_results,
            issues=all_issues,
            totals=calc_result.totals,
            ruleset_version_used=calc_result.ruleset_version_used,
            raw_file_id=raw_file_id,
        )

        # Persist to database
        await persist_compliance_run(run)

        logger.info(
            f"Completed run {run_id}: {len(calc_result.employee_results)} employees, "
            f"{run.error_count} errors, {run.warning_count} warnings"
        )

        # Return summary
        return RunCreateResponse(
            run_id=run.run_id,
            payroll_run_id=run_context.payroll_run_id,
            status=run.status.value,
            ruleset_version_used=run.ruleset_version_used,
            created_at=run.created_at,
            issue_count=IssueCount(
                errors=run.error_count,
                warnings=run.warning_count,
            ),
            totals=Totals(
                employee_count=calc_result.totals.employee_count,
                total_gross=calc_result.totals.total_gross,
                total_taxable=calc_result.totals.total_taxable,
                total_paye=calc_result.totals.total_paye,
                total_uif_employee=calc_result.totals.total_uif_employee,
                total_uif_employer=calc_result.totals.total_uif_employer,
                total_sdl=calc_result.totals.total_sdl,
                total_net_pay=calc_result.totals.total_net_pay,
                total_employer_cost=calc_result.totals.total_employer_cost,
            ),
        )

    except SchemaValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error processing compliance run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_detail(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> RunDetailResponse:
    """
    Get compliance run metadata and totals.

    Returns run details including ruleset_version_used and payroll_run_id.

    Args:
        run_id: The run identifier.
        session: Database session.

    Returns:
        RunDetailResponse with run metadata, ruleset_version_used, and totals.

    Raises:
        HTTPException: If run not found.
    """
    repo = RunRepository(session)
    run = await repo.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return RunDetailResponse(
        run_id=run.run_id,
        payroll_run_id=run.payroll_run_id,  # Direct from run object - audit purity
        company_id=run.company_id,
        pay_date=run.pay_date,
        tax_year=run.tax_year,
        payroll_frequency=run.payroll_frequency.value,
        ruleset_version_used=run.ruleset_version_used,
        status=run.status.value,
        created_at=run.created_at,
        completed_at=run.completed_at,
        issue_count=IssueCount(
            errors=run.error_count,
            warnings=run.warning_count,
        ),
        totals=Totals(
            employee_count=run.totals.employee_count,
            total_gross=run.totals.total_gross,
            total_taxable=run.totals.total_taxable,
            total_paye=run.totals.total_paye,
            total_uif_employee=run.totals.total_uif_employee,
            total_uif_employer=run.totals.total_uif_employer,
            total_sdl=run.totals.total_sdl,
            total_net_pay=run.totals.total_net_pay,
            total_employer_cost=run.totals.total_employer_cost,
        ) if run.totals else None,
    )


@router.get("/runs/{run_id}/results", response_model=RunResultsResponse)
async def get_run_results(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> RunResultsResponse:
    """
    Get per-employee results for a compliance run.

    Returns employee results with totals, including ruleset_version_used.

    Args:
        run_id: The run identifier.
        session: Database session.

    Returns:
        RunResultsResponse with per-employee results and aggregated totals.

    Raises:
        HTTPException: If run not found.
    """
    repo = RunRepository(session)
    run = await repo.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return RunResultsResponse(
        run_id=run.run_id,
        payroll_run_id=run.payroll_run_id,  # Direct from run object - audit purity
        ruleset_version_used=run.ruleset_version_used,
        results=[
            EmployeeResultResponse(
                employee_id=r.employee_id,
                gross_income=r.gross_income,
                taxable_income=r.taxable_income,
                paye=r.paye,
                uif_employee=r.uif_employee,
                uif_employer=r.uif_employer,
                sdl=r.sdl,
                net_pay=r.net_pay,
                total_employer_cost=r.total_employer_cost,
            )
            for r in run.results
        ],
        totals=Totals(
            employee_count=run.totals.employee_count,
            total_gross=run.totals.total_gross,
            total_taxable=run.totals.total_taxable,
            total_paye=run.totals.total_paye,
            total_uif_employee=run.totals.total_uif_employee,
            total_uif_employer=run.totals.total_uif_employer,
            total_sdl=run.totals.total_sdl,
            total_net_pay=run.totals.total_net_pay,
            total_employer_cost=run.totals.total_employer_cost,
        ) if run.totals else None,
    )


@router.get("/runs/{run_id}/errors", response_model=RunErrorsResponse)
async def get_run_errors(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> RunErrorsResponse:
    """
    Get validation issues (errors and warnings) for a compliance run.

    Args:
        run_id: The run identifier.
        session: Database session.

    Returns:
        RunErrorsResponse with list of validation issues.

    Raises:
        HTTPException: If run not found.
    """
    repo = RunRepository(session)
    run = await repo.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return RunErrorsResponse(
        run_id=run_id,
        payroll_run_id=run.payroll_run_id,  # Direct from run object - audit purity
        issues=[
            ValidationIssueResponse(
                row=i.row_number if i.row_number else 0,
                employee_id=i.employee_id,
                severity=i.severity.value,
                code=i.code,
                message=i.message,
                field=i.field,
            )
            for i in run.issues
        ],
    )


@router.get("/runs/{run_id}/export")
async def export_run_results(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """
    Export compliance run results as CSV with totals row.

    CSV includes:
    - Header row
    - Per-employee result rows
    - Totals summary row
    - Metadata (ruleset_version_used, payroll_run_id)

    Args:
        run_id: The run identifier.
        session: Database session.

    Returns:
        StreamingResponse with CSV content.

    Raises:
        HTTPException: If run not found.
    """
    repo = RunRepository(session)
    run = await repo.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Generate CSV with totals
    output = io.StringIO()
    writer = csv.writer(output)

    # Metadata rows
    writer.writerow(["# Compliance Results Export"])
    writer.writerow(["# Run ID", run.run_id])
    writer.writerow(["# Payroll Run ID", run.payroll_run_id])  # Direct from run object - audit purity
    writer.writerow(["# Company ID", run.company_id])
    writer.writerow(["# Pay Date", str(run.pay_date)])
    writer.writerow(["# Tax Year", run.tax_year])
    writer.writerow(["# Ruleset Version", run.ruleset_version_used])
    writer.writerow(["# Generated At", str(run.completed_at or run.created_at)])
    writer.writerow([])  # Blank line

    # Header row
    writer.writerow([
        "employee_id",
        "gross_income",
        "taxable_income",
        "paye",
        "uif_employee",
        "uif_employer",
        "sdl",
        "net_pay",
        "total_employer_cost",
    ])

    # Per-employee data rows
    for result in run.results:
        writer.writerow([
            result.employee_id,
            str(result.gross_income),
            str(result.taxable_income),
            str(result.paye),
            str(result.uif_employee),
            str(result.uif_employer),
            str(result.sdl),
            str(result.net_pay),
            str(result.total_employer_cost),
        ])

    # Totals row
    if run.totals:
        writer.writerow([])  # Blank line
        writer.writerow(["TOTALS"])
        writer.writerow([
            f"{run.totals.employee_count} employees",
            str(run.totals.total_gross),
            str(run.totals.total_taxable),
            str(run.totals.total_paye),
            str(run.totals.total_uif_employee),
            str(run.totals.total_uif_employer),
            str(run.totals.total_sdl),
            str(run.totals.total_net_pay),
            str(run.totals.total_employer_cost),
        ])

    csv_content = output.getvalue().encode("utf-8")

    # Return as streaming response
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=compliance_results_{run_id}.csv"
        },
    )

