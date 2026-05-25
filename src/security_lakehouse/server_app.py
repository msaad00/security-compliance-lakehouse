"""Optional FastAPI server (``trustops[server]`` extra).

Server mode serves the same assessment engine and the same
:mod:`security_lakehouse.api_v1` contract as local mode, plus the platform
surface local mode cannot provide: an application-state database, bearer-token
authentication, and role-based access control.

Authentication is required by default. Start with ``require_auth=False`` (or set
``TRUSTOPS_ALLOW_INSECURE_NO_AUTH=1``) only for local development; every request
then runs as a synthetic admin. Local mode (:mod:`security_lakehouse.server`)
remains zero-dependency and unauthenticated by design.

Import this module only when the ``server`` extra is installed.
"""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from security_lakehouse import api_v1
from security_lakehouse.auth.dependencies import get_session, require_scope
from security_lakehouse.auth.oidc import OIDCLoginError, build_oauth, complete_oidc_login, load_oidc_config
from security_lakehouse.auth.rbac import Identity
from security_lakehouse.auth.request_audit import append_request_audit
from security_lakehouse.auth.saml import (
    SAMLLoginError,
    build_saml_auth,
    complete_saml_login,
    email_from_saml_assertion,
    load_saml_config,
    saml_request_data,
)
from security_lakehouse.auth.sessions import SESSION_COOKIE
from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.db import migrate, repository
from security_lakehouse.db.base import create_engine_for, session_factory
from security_lakehouse.web import web_dist_dir, web_dist_index

_COOKIE_SECURE = os.environ.get("TRUSTOPS_COOKIE_SECURE", "true").lower() in {"1", "true", "yes", "on"}

_ERROR_CODES = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found"}

# Scope dependencies are built once (module-level) and reused as route defaults.
_require_read = require_scope("read")
_require_snapshot = require_scope("snapshot")
_require_admin = require_scope("auth_admin")
_REDACTED_FIELDS = {"owner", "asset_owner", "actor", "assignee", "note", "credentials"}


class CreateKeyRequest(BaseModel):
    user_email: str
    name: str = ""
    expires_in_days: int | None = None


def _params(request: Request) -> dict[str, list[str]]:
    """Convert Starlette's query multidict into the ``api_v1`` param shape."""
    params: dict[str, list[str]] = {}
    for key, value in request.query_params.multi_items():
        params.setdefault(key, []).append(value)
    return params


def _insecure_requested() -> bool:
    return os.environ.get("TRUSTOPS_ALLOW_INSECURE_NO_AUTH", "").lower() in {"1", "true", "yes"}


def _redact_payload(payload: object, identity: Identity) -> object:
    if identity.role != "auditor":
        return payload
    if isinstance(payload, dict):
        return {
            key: ("[redacted]" if key in _REDACTED_FIELDS else _redact_payload(value, identity))
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [_redact_payload(item, identity) for item in payload]
    return payload


def create_app(lake_dir: str | Path, *, require_auth: bool = True) -> FastAPI:
    """Build the server-mode ASGI app bound to a security data lake directory."""
    lake = Path(lake_dir)
    dashboard = lake / "console.html"
    render_dashboard(lake, dashboard)
    web_dist = web_dist_dir() if web_dist_index() else None

    migrate.upgrade(lake)
    engine = create_engine_for(lake)

    app = FastAPI(title="TrustOps Security Data Lake", version=api_v1.API_VERSION)
    app.state.sessionmaker = session_factory(engine)
    app.state.require_auth = require_auth and not _insecure_requested()

    # OIDC SSO is optional; the OAuth client + signed session middleware are only
    # wired when an identity provider is configured via the environment.
    app.state.oidc_config = load_oidc_config()
    app.state.oauth = None
    app.state.saml_config = load_saml_config()
    app.state.saml_auth_factory = build_saml_auth
    if app.state.oidc_config is not None:
        from starlette.middleware.sessions import SessionMiddleware

        secret = os.environ.get("TRUSTOPS_SESSION_SECRET") or secrets.token_hex(32)
        app.add_middleware(SessionMiddleware, secret_key=secret, same_site="lax", https_only=_COOKIE_SECURE)
        app.state.oauth = build_oauth(app.state.oidc_config)

    @app.middleware("http")
    async def _record_request_audit(request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        response = await call_next(request)
        path = request.url.path
        # Audit authorization decisions on the secured surface only; health is open.
        if path.startswith("/api/v1/") and path != "/api/v1/healthz":
            append_request_audit(
                lake,
                method=request.method,
                route=path,
                status_code=response.status_code,
                decision="allow" if response.status_code < 400 else "deny",
                correlation_id=correlation_id,
                identity=getattr(request.state, "identity", None),
            )
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def _error_envelope(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _ERROR_CODES.get(exc.status_code, "error")
        return JSONResponse(
            api_v1.error_envelope(code, str(exc.detail)),
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    # --- open health checks (registered before the authenticated catch-all) ---
    @app.get("/api/healthz")
    def healthz() -> dict[str, object]:
        return {"ok": True, "service": "trustops-assessment"}

    @app.get("/api/v1/healthz")
    def v1_healthz() -> JSONResponse:
        _status, body = api_v1.handle_get("/api/v1/healthz", {}, lake)
        return JSONResponse(body, status_code=int(_status))

    # --- SSO (OIDC) ---
    @app.get("/api/v1/auth/login")
    async def sso_login(request: Request):
        if app.state.oauth is None:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC SSO is not configured")
        redirect_uri = os.environ.get("TRUSTOPS_OIDC_REDIRECT_URL") or str(request.url_for("sso_callback"))
        return await app.state.oauth.oidc.authorize_redirect(request, redirect_uri)

    @app.get("/api/v1/auth/callback", name="sso_callback")
    async def sso_callback(request: Request, session: Session = Depends(get_session)):
        if app.state.oauth is None:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC SSO is not configured")
        try:
            token = await app.state.oauth.oidc.authorize_access_token(request)
        except Exception as exc:  # noqa: BLE001 - authlib surfaces several OAuth error types
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC token exchange failed") from exc
        email = (token.get("userinfo") or {}).get("email", "")
        try:
            _user, sess_token = complete_oidc_login(session, config=app.state.oidc_config, email=email)
        except OIDCLoginError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        session.commit()
        response = RedirectResponse(url="/console", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE, sess_token, httponly=True, secure=_COOKIE_SECURE, samesite="lax", path="/")
        return response

    @app.post("/api/v1/auth/logout")
    def sso_logout(request: Request, session: Session = Depends(get_session)) -> JSONResponse:
        cookie = request.cookies.get(SESSION_COOKIE)
        if cookie:
            repository.revoke_user_session(session, cookie, now=datetime.now(UTC))
            session.commit()
        response = JSONResponse(api_v1.envelope("auth.logout", {"ok": True}))
        response.delete_cookie(SESSION_COOKIE, path="/")
        return response

    # --- SSO (SAML) ---
    @app.get("/api/v1/auth/saml/login")
    def saml_login(request: Request):
        if app.state.saml_config is None:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="SAML SSO is not configured")
        auth = app.state.saml_auth_factory(
            app.state.saml_config,
            saml_request_data(
                scheme=request.url.scheme,
                host=request.url.netloc,
                port=request.url.port,
                path=request.url.path,
                query=dict(request.query_params),
            ),
        )
        return RedirectResponse(url=auth.login(), status_code=status.HTTP_302_FOUND)

    @app.get("/api/v1/auth/saml/metadata")
    def saml_metadata(request: Request):
        if app.state.saml_config is None:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="SAML SSO is not configured")
        auth = app.state.saml_auth_factory(
            app.state.saml_config,
            saml_request_data(
                scheme=request.url.scheme,
                host=request.url.netloc,
                port=request.url.port,
                path=request.url.path,
                query=dict(request.query_params),
            ),
        )
        metadata = auth.get_settings().get_sp_metadata()
        errors = auth.get_settings().validate_metadata(metadata)
        if errors:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="invalid SAML metadata")
        return HTMLResponse(metadata, media_type="application/xml")

    @app.post("/api/v1/auth/saml/acs")
    async def saml_acs(request: Request, session: Session = Depends(get_session)):
        if app.state.saml_config is None:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="SAML SSO is not configured")
        body = await request.body()
        auth = app.state.saml_auth_factory(
            app.state.saml_config,
            saml_request_data(
                scheme=request.url.scheme,
                host=request.url.netloc,
                port=request.url.port,
                path=request.url.path,
                query=dict(request.query_params),
                body=body,
            ),
        )
        auth.process_response()
        errors = auth.get_errors()
        if errors or not auth.is_authenticated():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SAML response rejected")
        try:
            _user, sess_token = complete_saml_login(
                session,
                config=app.state.saml_config,
                email=email_from_saml_assertion(auth),
            )
        except SAMLLoginError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        session.commit()
        response = RedirectResponse(url="/console", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE, sess_token, httponly=True, secure=_COOKIE_SECURE, samesite="lax", path="/")
        return response

    # --- auth surface ---
    @app.get("/api/v1/auth/whoami")
    def whoami(identity: Identity = Depends(_require_read)) -> JSONResponse:
        return JSONResponse(
            api_v1.envelope(
                "auth.whoami",
                {
                    "user_id": identity.user_id,
                    "tenant_id": identity.tenant_id,
                    "email": identity.email,
                    "role": identity.role,
                    "scopes": sorted(identity.scopes),
                },
            )
        )

    @app.get("/api/v1/auth/keys")
    def list_keys(
        identity: Identity = Depends(_require_admin),
        session: Session = Depends(get_session),
    ) -> JSONResponse:
        keys = repository.list_api_keys(session, tenant_id=identity.tenant_id)
        rows = [
            {
                "id": key.id,
                "name": key.name,
                "prefix": key.prefix,
                "user_email": key.user.email,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "revoked": key.revoked_at is not None,
            }
            for key in keys
        ]
        return JSONResponse(api_v1.envelope("auth.keys", rows, meta={"count": len(rows)}))

    @app.post("/api/v1/auth/keys", status_code=status.HTTP_201_CREATED)
    def create_key(
        body: CreateKeyRequest,
        identity: Identity = Depends(_require_admin),
        session: Session = Depends(get_session),
    ) -> JSONResponse:
        user = repository.get_user_by_email(session, tenant_id=identity.tenant_id, email=body.user_email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no user {body.user_email!r} in tenant")
        expires_at = None
        if body.expires_in_days is not None:
            expires_at = datetime.now(UTC) + timedelta(days=body.expires_in_days)
        key, token = repository.create_api_key(
            session, tenant_id=identity.tenant_id, user_id=user.id, name=body.name, expires_at=expires_at
        )
        session.commit()
        return JSONResponse(
            api_v1.envelope(
                "auth.keys",
                {"id": key.id, "prefix": key.prefix, "user_email": user.email, "token": token},
            ),
            status_code=status.HTTP_201_CREATED,
        )

    @app.delete("/api/v1/auth/keys/{key_id}")
    def revoke_key(
        key_id: str,
        identity: Identity = Depends(_require_admin),
        session: Session = Depends(get_session),
    ) -> JSONResponse:
        revoked = repository.revoke_api_key(session, tenant_id=identity.tenant_id, key_id=key_id, now=datetime.now(UTC))
        if not revoked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="key not found or already revoked")
        session.commit()
        return JSONResponse(api_v1.envelope("auth.keys", {"id": key_id, "revoked": True}))

    # --- versioned data surface (authenticated) ---
    @app.get("/api/v1/{rest:path}")
    def v1_get(rest: str, request: Request, identity: Identity = Depends(_require_read)) -> JSONResponse:
        _status, body = api_v1.handle_get(f"/api/v1/{rest}", _params(request), lake)
        return JSONResponse(_redact_payload(body, identity), status_code=int(_status))

    @app.post("/api/v1/{rest:path}")
    async def v1_post(rest: str, request: Request, _identity: Identity = Depends(_require_snapshot)) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001 - empty/invalid body is treated as no body
            body = {}
        _status, payload = api_v1.handle_post(f"/api/v1/{rest}", body, lake)
        return JSONResponse(payload, status_code=int(_status))

    @app.get("/", response_class=HTMLResponse)
    @app.get("/console", response_class=HTMLResponse)
    def console() -> HTMLResponse:
        return HTMLResponse(dashboard.read_text(encoding="utf-8"))

    if web_dist is not None:
        # Next.js static export; html=True resolves /console/<route>/ to index.html.
        app.mount("/console", StaticFiles(directory=str(web_dist), html=True), name="console")

    return app


def serve(lake_dir: str | Path, *, host: str = "127.0.0.1", port: int = 8787, require_auth: bool = True) -> None:
    """Run the server-mode app under uvicorn."""
    import uvicorn

    uvicorn.run(create_app(lake_dir, require_auth=require_auth), host=host, port=port)
