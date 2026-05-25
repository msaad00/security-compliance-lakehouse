"""Thin data-access helpers over the application-state models.

Keeping create/lookup logic here (rather than in request handlers) means the
auth and remediation work that follows shares one validated path into the
application-state database.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from security_lakehouse.auth.tokens import generate_token, hash_token
from security_lakehouse.db.models import USER_ROLES, ApiKey, Tenant, User


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
    role: str = "read_only",
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


def get_user_by_id(session: Session, *, user_id: str) -> User | None:
    """Look up a user by id."""
    return session.get(User, user_id)


def create_api_key(
    session: Session,
    *,
    tenant_id: str,
    user_id: str,
    name: str = "",
    expires_at: datetime | None = None,
) -> tuple[ApiKey, str]:
    """Mint an API key for a user. Returns ``(key, plaintext_token)``.

    The plaintext token is returned only here and is never persisted.
    """
    user = get_user_by_id(session, user_id=user_id)
    if user is None or user.tenant_id != tenant_id:
        raise ValueError("API key user must exist in the same tenant")
    token, prefix, key_hash = generate_token()
    key = ApiKey(
        tenant_id=tenant_id,
        user_id=user_id,
        workspace_id=tenant_id,
        role=user.role,
        status="active",
        name=name,
        key_hash=key_hash,
        prefix=prefix,
        expires_at=expires_at,
    )
    session.add(key)
    session.flush()
    return key, token


def resolve_api_key(session: Session, token: str) -> ApiKey | None:
    """Resolve a presented token to its API key by hash (active or not)."""
    return session.scalars(select(ApiKey).where(ApiKey.key_hash == hash_token(token))).one_or_none()


def list_api_keys(session: Session, *, tenant_id: str) -> list[ApiKey]:
    """List a tenant's API keys, newest first."""
    stmt = select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at.desc())
    return list(session.scalars(stmt))


def revoke_api_key(session: Session, *, tenant_id: str, key_id: str, now: datetime) -> bool:
    """Revoke a key within a tenant. Returns False if not found or already revoked."""
    key = session.get(ApiKey, key_id)
    if key is None or key.tenant_id != tenant_id or key.revoked_at is not None:
        return False
    key.revoked_at = now
    key.status = "revoked"
    session.flush()
    return True
