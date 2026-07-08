"""Create administrator audit event schema.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("admin_username", sa.String(length=255), nullable=True),
        sa.Column("admin_role", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("client_ip", sa.String(length=100), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_audit_events")),
    )
    op.create_index(
        op.f("ix_admin_audit_events_admin_username"),
        "admin_audit_events",
        ["admin_username"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_created_at"),
        "admin_audit_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_event_type"),
        "admin_audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_request_id"),
        "admin_audit_events",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_status"),
        "admin_audit_events",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_events_status"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_request_id"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_event_type"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_created_at"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_admin_username"), table_name="admin_audit_events")
    op.drop_table("admin_audit_events")
