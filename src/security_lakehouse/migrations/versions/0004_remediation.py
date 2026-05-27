"""remediation tasks, evidence requests, control exceptions

Revision ID: 0004_remediation
Revises: 0003_user_sessions
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_remediation"
down_revision: str | None = "0003_user_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _alembic_revision_markers() -> tuple[str, str | None, str | Sequence[str] | None, str | Sequence[str] | None]:
    """Expose Alembic revision globals to static analysis without renaming them."""
    return revision, down_revision, branch_labels, depends_on


def upgrade() -> None:
    _alembic_revision_markers()
    op.create_table(
        "remediation_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("control_id", sa.String(length=128), nullable=True),
        sa.Column("violation_id", sa.String(length=255), nullable=True),
        sa.Column("owner", sa.String(length=255), server_default="", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("priority", sa.String(length=16), server_default="medium", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_remediation_tasks_tenant_id", "remediation_tasks", ["tenant_id"])
    op.create_index("ix_remediation_tasks_control_id", "remediation_tasks", ["control_id"])
    op.create_index("ix_remediation_tasks_violation_id", "remediation_tasks", ["violation_id"])

    op.create_table(
        "evidence_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("control_id", sa.String(length=128), nullable=False),
        sa.Column("requested_from", sa.String(length=255), server_default="", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("note", sa.Text(), server_default="", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_requests_tenant_id", "evidence_requests", ["tenant_id"])
    op.create_index("ix_evidence_requests_control_id", "evidence_requests", ["control_id"])

    op.create_table(
        "control_exceptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("control_id", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), server_default="", nullable=False),
        sa.Column("approved_by", sa.String(length=255), server_default="", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_control_exceptions_tenant_id", "control_exceptions", ["tenant_id"])
    op.create_index("ix_control_exceptions_control_id", "control_exceptions", ["control_id"])


def downgrade() -> None:
    _alembic_revision_markers()
    op.drop_index("ix_control_exceptions_control_id", table_name="control_exceptions")
    op.drop_index("ix_control_exceptions_tenant_id", table_name="control_exceptions")
    op.drop_table("control_exceptions")
    op.drop_index("ix_evidence_requests_control_id", table_name="evidence_requests")
    op.drop_index("ix_evidence_requests_tenant_id", table_name="evidence_requests")
    op.drop_table("evidence_requests")
    op.drop_index("ix_remediation_tasks_violation_id", table_name="remediation_tasks")
    op.drop_index("ix_remediation_tasks_control_id", table_name="remediation_tasks")
    op.drop_index("ix_remediation_tasks_tenant_id", table_name="remediation_tasks")
    op.drop_table("remediation_tasks")
