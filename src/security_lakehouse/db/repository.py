"""Thin data-access helpers over the application-state models.

Keeping create/lookup logic here (rather than in request handlers) means the
auth and remediation work that follows shares one validated path into the
application-state database.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from security_lakehouse.db.models import USER_ROLES, Tenant, User


def create_tenant(session: Session, *, slug: str, name: str) -> Tenant:
    """Create a tenant. ``slug`` must be unique across the database."""
    tenant = Tenant(slug=slug, name=name)
    session.add(tenant)
    session.flush()
    return tenant


def create_user(
    session: Session,
    *,
    tenant_id: str,
    email: str,
    display_name: str = "",
    role: str = "viewer",
) -> User:
    """Create a user within a tenant. Email is unique within the tenant."""
    if role not in USER_ROLES:
        raise ValueError(f"role must be one of {sorted(USER_ROLES)}, got {role!r}")
    user = User(tenant_id=tenant_id, email=email, display_name=display_name, role=role)
    session.add(user)
    session.flush()
    return user


def get_user_by_email(session: Session, *, tenant_id: str, email: str) -> User | None:
    """Look up a user by tenant + email."""
    stmt = select(User).where(User.tenant_id == tenant_id, User.email == email)
    return session.scalars(stmt).one_or_none()


def get_tenant_by_slug(session: Session, *, slug: str) -> Tenant | None:
    """Look up a tenant by slug."""
    return session.scalars(select(Tenant).where(Tenant.slug == slug)).one_or_none()
