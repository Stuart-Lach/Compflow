"""
Export services for compliance runs.

Generates CSV and PDF exports from stored run results.
"""

import io
from datetime import datetime
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.db import RunRecord, ResultRecord


async def build_employee_breakdown_csv(session: AsyncSession, run_id: str) -> bytes:
    """
    Build employee breakdown CSV for a compliance run.

    Args:
        session: Database session.
        run_id: The compliance run ID.

    Returns:
        CSV file as bytes.

    Raises:
        ValueError: If run not found.
    """
    # Get results for this run
    result = await session.execute(
        select(ResultRecord).where(ResultRecord.run_id == run_id).order_by(ResultRecord.employee_id)
    )
    results = result.scalars().all()

    if not results:
        # Check if run exists
        run_result = await session.execute(
            select(RunRecord).where(RunRecord.id == run_id)
        )
        run = run_result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        # Run exists but has no results
        raise ValueError(f"No results found for run: {run_id}")

    # Build CSV
    output = io.StringIO()

    # Write header
    output.write("employee_id,gross_income,taxable_income,paye,uif_employee,uif_employer,sdl,net_pay,total_employer_cost\n")

    # Write data rows
    for record in results:
        output.write(
            f"{record.employee_id},"
            f"{record.gross_income},"
            f"{record.taxable_income},"
            f"{record.paye},"
            f"{record.uif_employee},"
            f"{record.uif_employer},"
            f"{record.sdl},"
            f"{record.net_pay},"
            f"{record.total_employer_cost}\n"
        )

    return output.getvalue().encode('utf-8')


async def build_summary_pdf(session: AsyncSession, run_id: str) -> bytes:
    """
    Build compliance summary PDF for a payroll run.

    Args:
        session: Database session.
        run_id: The compliance run ID.

    Returns:
        PDF file as bytes.

    Raises:
        ValueError: If run not found.
    """
    # Get run record
    result = await session.execute(
        select(RunRecord).where(RunRecord.id == run_id)
    )
    run = result.scalar_one_or_none()

    if not run:
        raise ValueError(f"Run not found: {run_id}")

    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1,  # Center
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
    )

    # Title
    title = Paragraph("Payroll Compliance Summary", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    # Run metadata
    metadata_heading = Paragraph("Run Information", heading_style)
    elements.append(metadata_heading)

    metadata_data = [
        ["Company ID:", run.company_id],
        ["Payroll Run ID:", run.payroll_run_id],
        ["Pay Date:", run.pay_date],
        ["Tax Year:", run.tax_year],
        ["Payroll Frequency:", run.payroll_frequency],
        ["Ruleset Version:", run.ruleset_version_used],
        ["Employee Count:", str(run.employee_count or 0)],
    ]

    metadata_table = Table(metadata_data, colWidths=[2 * inch, 4 * inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
    ]))

    elements.append(metadata_table)
    elements.append(Spacer(1, 0.4 * inch))

    # Totals
    totals_heading = Paragraph("Financial Totals", heading_style)
    elements.append(totals_heading)

    def format_currency(value: Optional[str]) -> str:
        """Format currency with R prefix and 2 decimals."""
        if value is None:
            return "R0.00"
        try:
            decimal_val = Decimal(value)
            return f"R{decimal_val:,.2f}"
        except:
            return "R0.00"

    totals_data = [
        ["Total Gross Income:", format_currency(run.total_gross)],
        ["Total Taxable Income:", format_currency(run.total_taxable)],
        ["Total PAYE:", format_currency(run.total_paye)],
        ["Total UIF (Employee):", format_currency(run.total_uif_employee)],
        ["Total UIF (Employer):", format_currency(run.total_uif_employer)],
        ["Total SDL:", format_currency(run.total_sdl)],
        ["Total Net Pay:", format_currency(run.total_net_pay)],
        ["Total Employer Cost:", format_currency(run.total_employer_cost)],
    ]

    totals_table = Table(totals_data, colWidths=[2.5 * inch, 3.5 * inch])
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        # Highlight total employer cost
        ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (-2, -1), (-1, -1), colors.white),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 0.5 * inch))

    # Footer
    footer_text = (
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>"
        f"Ruleset: {run.ruleset_version_used}"
    )
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=1,  # Center
    )
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)

    # Build PDF
    doc.build(elements)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
