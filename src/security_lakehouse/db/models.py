"""Application-state ORM models (server mode).

The first slice is the multi-tenancy spine — ``Tenant`` and ``User`` — that
authentication and RBAC build on. Identifiers are string UUIDs so the schema
is portable across SQLite (default single-node) and Postgres (production)
without database-specific column types.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from security_lakehouse.db.base import Base

# Roles mirror the workbench's existing access tiers.
USER_ROLES = ("admin", "analyst", "viewer", "auditor")


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Tenant(Base):
    """An isolated workspace; all application-state rows hang off a tenant."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """A member of a tenant. Email is unique within (not across) a tenant."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    tenant: Mapped[Tenant] = relationship(back_populates="users")
