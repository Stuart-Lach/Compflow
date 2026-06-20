"""Create compliance evidence schema.

Revision ID: 0001
Revises:
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
    )
    op.create_index(op.f("ix_files_content_hash"), "files", ["content_hash"], unique=False)

    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("payroll_run_id", sa.String(length=100), nullable=False),
        sa.Column("company_id", sa.String(length=100), nullable=False),
        sa.Column("pay_date", sa.String(length=10), nullable=False),
        sa.Column("tax_year", sa.String(length=10), nullable=False),
        sa.Column("payroll_frequency", sa.String(length=20), nullable=False),
        sa.Column("ruleset_version_used", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_file_id", sa.String(length=100), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("total_gross", sa.String(length=50), nullable=True),
        sa.Column("total_taxable", sa.String(length=50), nullable=True),
        sa.Column("total_paye", sa.String(length=50), nullable=True),
        sa.Column("total_uif_employee", sa.String(length=50), nullable=True),
        sa.Column("total_uif_employer", sa.String(length=50), nullable=True),
        sa.Column("total_sdl", sa.String(length=50), nullable=True),
        sa.Column("total_net_pay", sa.String(length=50), nullable=True),
        sa.Column("total_employer_cost", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["raw_file_id"],
            ["files.id"],
            name=op.f("fk_runs_raw_file_id_files"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runs")),
    )
    op.create_index(op.f("ix_runs_company_id"), "runs", ["company_id"], unique=False)
    op.create_index(op.f("ix_runs_payroll_run_id"), "runs", ["payroll_run_id"], unique=False)

    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=50), nullable=False),
        sa.Column("employee_id", sa.String(length=100), nullable=False),
        sa.Column("gross_income", sa.String(length=50), nullable=False),
        sa.Column("taxable_income", sa.String(length=50), nullable=False),
        sa.Column("paye", sa.String(length=50), nullable=False),
        sa.Column("uif_employee", sa.String(length=50), nullable=False),
        sa.Column("uif_employer", sa.String(length=50), nullable=False),
        sa.Column("sdl", sa.String(length=50), nullable=False),
        sa.Column("net_pay", sa.String(length=50), nullable=False),
        sa.Column("total_employer_cost", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_results_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_results")),
    )
    op.create_index(op.f("ix_results_run_id"), "results", ["run_id"], unique=False)

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=50), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.String(length=100), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("field", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_issues_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_issues")),
    )
    op.create_index(op.f("ix_issues_run_id"), "issues", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_issues_run_id"), table_name="issues")
    op.drop_table("issues")
    op.drop_index(op.f("ix_results_run_id"), table_name="results")
    op.drop_table("results")
    op.drop_index(op.f("ix_runs_payroll_run_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_company_id"), table_name="runs")
    op.drop_table("runs")
    op.drop_index(op.f("ix_files_content_hash"), table_name="files")
    op.drop_table("files")
