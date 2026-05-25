"""Alembic environment for the application-state database."""

from __future__ import annotations

from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

from security_lakehouse.db import models  # noqa: F401 - import registers tables on Base.metadata
from security_lakehouse.db.base import Base

config = context.config
target_metadata = Base.metadata


def _ensure_sqlite_parent(url: str) -> None:
    """Create the parent directory for a file-based SQLite URL if absent."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return
    db_path = url[len(prefix) :]
    if db_path and db_path != ":memory:":
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    _ensure_sqlite_parent(url)
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
