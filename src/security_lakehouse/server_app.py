"""Optional FastAPI server (``trustops[server]`` extra).

This is the foundation of *server mode*: the same assessment engine and the
same :mod:`security_lakehouse.api_v1` contract served on an ASGI stack so that
later work (auth, multi-tenancy, live connectors) has a real middleware and
concurrency surface to build on. Local mode keeps using the zero-dependency
:mod:`security_lakehouse.server`.

Import this module only when the ``server`` extra is installed; it requires
``fastapi`` and ``uvicorn``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from security_lakehouse import api_v1
from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.web import web_dist_dir, web_dist_index


def _params(request: Request) -> dict[str, list[str]]:
    """Convert Starlette's query multidict into the ``api_v1`` param shape."""
    params: dict[str, list[str]] = {}
    for key, value in request.query_params.multi_items():
        params.setdefault(key, []).append(value)
    return params


def create_app(lake_dir: str | Path) -> FastAPI:
    """Build the server-mode ASGI app bound to a security data lake directory."""
    lake = Path(lake_dir)
    dashboard = lake / "console.html"
    render_dashboard(lake, dashboard)
    web_dist = web_dist_dir() if web_dist_index() else None

    app = FastAPI(title="TrustOps Security Data Lake", version=api_v1.API_VERSION)

    @app.get("/api/healthz")
    def healthz() -> dict[str, object]:
        return {"ok": True, "service": "trustops-assessment"}

    @app.get("/api/v1/{rest:path}")
    def v1_get(rest: str, request: Request) -> JSONResponse:
        status, body = api_v1.handle_get(f"/api/v1/{rest}", _params(request), lake)
        return JSONResponse(body, status_code=int(status))

    @app.post("/api/v1/{rest:path}")
    async def v1_post(rest: str, request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001 - empty/invalid body is treated as no body
            body = {}
        status, payload = api_v1.handle_post(f"/api/v1/{rest}", body, lake)
        return JSONResponse(payload, status_code=int(status))

    @app.get("/", response_class=HTMLResponse)
    @app.get("/console", response_class=HTMLResponse)
    def console() -> HTMLResponse:
        return HTMLResponse(dashboard.read_text(encoding="utf-8"))

    if web_dist is not None:
        # Next.js static export; html=True resolves /console/<route>/ to index.html.
        app.mount("/console", StaticFiles(directory=str(web_dist), html=True), name="console")

    return app


def serve(lake_dir: str | Path, *, host: str = "127.0.0.1", port: int = 8787) -> None:
    """Run the server-mode app under uvicorn."""
    import uvicorn

    uvicorn.run(create_app(lake_dir), host=host, port=port)
