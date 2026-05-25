"""Browser session + OIDC login tests for server mode.

The OIDC redirect/token-exchange is driven by an external identity provider, so
the network flow is not unit-tested here. The provisioning + session issuance
logic (:func:`complete_oidc_login`) and the session-cookie auth path are.
"""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

from security_lakehouse.auth.oidc import OIDCConfig, OIDCLoginError, complete_oidc_login  # noqa: E402
from security_lakehouse.auth.sessions import SESSION_COOKIE  # noqa: E402
from security_lakehouse.db import repository  # noqa: E402
from security_lakehouse.db.base import session_scope  # noqa: E402
from security_lakehouse.db.repository import create_tenant, create_user, create_user_session  # noqa: E402
from security_lakehouse.server_app import create_app  # noqa: E402
from test_api_v1 import _seed_lake  # noqa: E402


def _config(*, tenant_slug: str = "acme", auto_provision: bool = False) -> OIDCConfig:
    return OIDCConfig(
        issuer="https://idp.test",
        client_id="cid",
        client_secret="sec",
        tenant_slug=tenant_slug,
        auto_provision=auto_provision,
    )


@pytest.fixture
def app_env(tmp_path: Path):
    _seed_lake(tmp_path)
    app = create_app(tmp_path)  # auth required; OIDC not configured
    return app, TestClient(app)


def test_session_repository_lifecycle(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    app = create_app(tmp_path)
    with session_scope(app.state.sessionmaker) as session:
        tenant = create_tenant(session, slug="acme", name="Acme")
        user = create_user(session, tenant_id=tenant.id, email="u@acme.test", role="read_only")
        row, token = create_user_session(session, tenant_id=tenant.id, user_id=user.id)
        assert row.is_active()
    with session_scope(app.state.sessionmaker) as session:
        assert repository.resolve_user_session(session, token).is_active()
        assert repository.revoke_user_session(session, token, now=datetime.now(UTC))
    with session_scope(app.state.sessionmaker) as session:
        assert not repository.resolve_user_session(session, token).is_active()


def test_expired_session_is_inactive(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    app = create_app(tmp_path)
    with session_scope(app.state.sessionmaker) as session:
        tenant = create_tenant(session, slug="acme", name="Acme")
        user = create_user(session, tenant_id=tenant.id, email="u@acme.test")
        row, _token = create_user_session(session, tenant_id=tenant.id, user_id=user.id, ttl_hours=-1)
        assert not row.is_active()


def test_complete_oidc_login_requires_provisioned_user(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    app = create_app(tmp_path)
    with session_scope(app.state.sessionmaker) as session:
        create_tenant(session, slug="acme", name="Acme")
        with pytest.raises(OIDCLoginError):
            complete_oidc_login(session, config=_config(auto_provision=False), email="new@acme.test")


def test_complete_oidc_login_auto_provisions(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    app = create_app(tmp_path)
    with session_scope(app.state.sessionmaker) as session:
        create_tenant(session, slug="acme", name="Acme")
        user, token = complete_oidc_login(session, config=_config(auto_provision=True), email="new@acme.test")
        assert user.email == "new@acme.test"
        assert user.role == "read_only"
        assert repository.resolve_user_session(session, token).is_active()


def test_complete_oidc_login_unknown_tenant(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    app = create_app(tmp_path)
    with session_scope(app.state.sessionmaker) as session, pytest.raises(OIDCLoginError):
        complete_oidc_login(session, config=_config(tenant_slug="ghost", auto_provision=True), email="x@y.test")


def test_session_cookie_authenticates(app_env) -> None:
    app, client = app_env
    with session_scope(app.state.sessionmaker) as session:
        tenant = create_tenant(session, slug="acme", name="Acme")
        user = create_user(session, tenant_id=tenant.id, email="u@acme.test", role="read_only")
        _row, token = create_user_session(session, tenant_id=tenant.id, user_id=user.id)
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/v1/controls").status_code == HTTPStatus.OK
    who = client.get("/api/v1/auth/whoami").json()["data"]
    assert who["email"] == "u@acme.test"
    assert who["role"] == "read_only"


def test_logout_revokes_session(app_env) -> None:
    app, client = app_env
    with session_scope(app.state.sessionmaker) as session:
        tenant = create_tenant(session, slug="acme", name="Acme")
        user = create_user(session, tenant_id=tenant.id, email="u@acme.test")
        _row, token = create_user_session(session, tenant_id=tenant.id, user_id=user.id)
    client.cookies.set(SESSION_COOKIE, token)
    assert client.post("/api/v1/auth/logout").status_code == HTTPStatus.OK
    client.cookies.set(SESSION_COOKIE, token)  # re-present the now-revoked token
    assert client.get("/api/v1/controls").status_code == HTTPStatus.UNAUTHORIZED


def test_login_501_when_oidc_unconfigured(app_env) -> None:
    _app, client = app_env
    assert client.get("/api/v1/auth/login").status_code == HTTPStatus.NOT_IMPLEMENTED
