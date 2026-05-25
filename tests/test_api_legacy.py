"""Legacy console surface: server mode must match local mode, and be auth-gated.

The console (Next.js) talks to the unversioned ``/api/*`` routes. These tests
prove the FastAPI server returns the same bodies as the stdlib server and that
the surface is authenticated + RBAC-enforced in server mode.
"""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

from security_lakehouse.audit_log import build_audit_log  # noqa: E402
from security_lakehouse.db.base import session_scope  # noqa: E402
from security_lakehouse.db.repository import create_api_key, create_tenant, create_user  # noqa: E402
from security_lakehouse.server_app import create_app  # noqa: E402
from test_api_v1 import _request, _seed_lake, _spin  # noqa: E402

# Legacy GETs whose bodies are pure functions of seeded files (no timestamps).
LEGACY_DETERMINISTIC = [
    "/api/controls",
    "/api/control-tests",
    "/api/evidence",
    "/api/assets",
    "/api/frameworks",
    "/api/connectors",
    "/api/readiness",
    "/api/crosswalk",
    "/api/crosswalk/reviewed",
    "/api/mappings",
    "/api/workflows",
    "/api/workflows/actions",
    "/api/trust-shares",
]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_legacy_surface_matches_stdlib(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    client = TestClient(create_app(tmp_path, require_auth=False))
    stdlib = _spin(tmp_path)
    try:
        for path in LEGACY_DETERMINISTIC:
            stdlib_status, stdlib_body = _request(stdlib, "GET", path)
            resp = client.get(path)
            assert resp.status_code == stdlib_status, path
            assert resp.json() == stdlib_body, path
    finally:
        stdlib.shutdown()


def test_legacy_requires_auth_in_server_mode(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    client = TestClient(create_app(tmp_path))  # auth required
    assert client.get("/api/controls").status_code == HTTPStatus.UNAUTHORIZED
    entries = build_audit_log(tmp_path, category="request")
    assert entries[0]["payload"]["route"] == "/api/controls"
    assert entries[0]["result"] == "deny"


def test_legacy_bad_request_sanitizes_internal_exception_text(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    client = TestClient(create_app(tmp_path, require_auth=False))
    resp = client.post("/api/connectors/does-not-exist/configure", json={"state": "enabled"})
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json() == {"error": "bad_request", "reason": "invalid request"}


def test_legacy_post_enforces_route_specific_scopes(tmp_path: Path) -> None:
    _seed_lake(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)
    tokens: dict[str, str] = {}
    with session_scope(app.state.sessionmaker) as session:
        tenant = create_tenant(session, slug="acme", name="Acme")
        for role in ("read_only", "contributor", "security_admin"):
            user = create_user(session, tenant_id=tenant.id, email=f"{role}@acme.test", role=role)
            _key, token = create_api_key(session, tenant_id=tenant.id, user_id=user.id)
            tokens[role] = token

    # read_only may read but not write
    assert client.get("/api/controls", headers=_bearer(tokens["read_only"])).status_code == HTTPStatus.OK
    assert (
        client.post(
            "/api/violations/v1/triage",
            json={"state": "triaged"},
            headers=_bearer(tokens["read_only"]),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )

    # contributor can triage but cannot manage connector credentials or snapshots.
    assert (
        client.post(
            "/api/violations/v1/triage",
            json={"state": "triaged"},
            headers=_bearer(tokens["contributor"]),
        ).status_code
        == HTTPStatus.CREATED
    )
    assert (
        client.post(
            "/api/connectors/github-security/configure",
            json={"state": "enabled"},
            headers=_bearer(tokens["contributor"]),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        client.post("/api/snapshots", json={"reason": "audit"}, headers=_bearer(tokens["contributor"])).status_code
        == HTTPStatus.FORBIDDEN
    )

    # security_admin owns connector/workflow/snapshot operations.
    assert (
        client.post(
            "/api/connectors/github-security/configure",
            json={"state": "enabled"},
            headers=_bearer(tokens["security_admin"]),
        ).status_code
        == HTTPStatus.CREATED
    )
    assert (
        client.post("/api/snapshots", json={"reason": "audit"}, headers=_bearer(tokens["security_admin"])).status_code
        == HTTPStatus.CREATED
    )
