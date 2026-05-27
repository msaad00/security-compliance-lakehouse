"""tags, entity_tags, saved_views

Revision ID: 0005_tags
Revises: 0004_remediation
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_tags"
down_revision: str | None = "0004_remediation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _alembic_revision_markers() -> tuple[str, str | None, str | Sequence[str] | None, str | Sequence[str] | None]:
    """Expose Alembic revision globals to static analysis without renaming them."""
    return revision, down_revision, branch_labels, depends_on


def upgrade() -> None:
    _alembic_revision_markers()
    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("color", sa.String(length=32), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_tags_tenant_name"),
    )
    op.create_index("ix_tags_tenant_id", "tags", ["tenant_id"])

    op.create_table(
        "entity_tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tag_id", "entity_type", "entity_id", name="uq_entity_tags_tag_entity"),
    )
    op.create_index("ix_entity_tags_tenant_id", "entity_tags", ["tenant_id"])
    op.create_index("ix_entity_tags_tag_id", "entity_tags", ["tag_id"])
    op.create_index("ix_entity_tags_entity_id", "entity_tags", ["entity_id"])

    op.create_table(
        "saved_views",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("surface", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("filters", sa.Text(), server_default="{}", nullable=False),
        sa.Column("created_by", sa.String(length=255), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_views_tenant_id", "saved_views", ["tenant_id"])


def downgrade() -> None:
    _alembic_revision_markers()
    op.drop_index("ix_saved_views_tenant_id", table_name="saved_views")
    op.drop_table("saved_views")
    op.drop_index("ix_entity_tags_entity_id", table_name="entity_tags")
    op.drop_index("ix_entity_tags_tag_id", table_name="entity_tags")
    op.drop_index("ix_entity_tags_tenant_id", table_name="entity_tags")
    op.drop_table("entity_tags")
    op.drop_index("ix_tags_tenant_id", table_name="tags")
    op.drop_table("tags")
