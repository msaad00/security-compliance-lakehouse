"""posture metric points time-series table

Revision ID: 0006_metrics
Revises: 0004_remediation
Create Date: 2026-05-26

Note: down_revision is "0005_tags" because #94 (tags) was already merged into
main. If further revisions are added before this merges, rebase accordingly.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_metrics"
down_revision: str | None = "0005_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _alembic_revision_markers() -> tuple[str, str | None, str | Sequence[str] | None, str | Sequence[str] | None]:
    """Expose Alembic revision globals to static analysis without renaming them."""
    return revision, down_revision, branch_labels, depends_on


def upgrade() -> None:
    _alembic_revision_markers()
    op.create_table(
        "posture_metric_points",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("posture_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("control_pass_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("open_violations", sa.Integer(), server_default="0", nullable=False),
        sa.Column("critical_violations", sa.Integer(), server_default="0", nullable=False),
        sa.Column("stale_controls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("evidence_fresh_pct", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("remediation_open", sa.Integer(), server_default="0", nullable=False),
        sa.Column("remediation_overdue", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posture_metric_points_tenant_id", "posture_metric_points", ["tenant_id"])
    op.create_index("ix_posture_metric_points_captured_at", "posture_metric_points", ["captured_at"])
    op.create_index(
        "ix_posture_metric_points_tenant_captured",
        "posture_metric_points",
        ["tenant_id", "captured_at"],
    )


def downgrade() -> None:
    _alembic_revision_markers()
    op.drop_index("ix_posture_metric_points_tenant_captured", table_name="posture_metric_points")
    op.drop_index("ix_posture_metric_points_captured_at", table_name="posture_metric_points")
    op.drop_index("ix_posture_metric_points_tenant_id", table_name="posture_metric_points")
    op.drop_table("posture_metric_points")
