"""Lightweight human and agent API for the assessment engine."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from security_lakehouse.assessment import build_current_posture, write_assessment_snapshot
from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.io import read_jsonl
from security_lakehouse.web import web_dist_dir, web_dist_index


def serve(lake_dir: str | Path, *, host: str = "127.0.0.1", port: int = 8787) -> None:
    """Serve the TrustOps console and JSON assessment API."""
    lake = Path(lake_dir)
    dashboard = lake / "console.html"
    render_dashboard(lake, dashboard)

    class Handler(_Handler):
        lake_dir = lake
        dashboard_path = dashboard
        web_dist = web_dist_dir() if web_dist_index() else None

    httpd = ThreadingHTTPServer((host, port), Handler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


# MIME types Next.js static export ships that aren't always in the system table.
_MIME_OVERRIDES = {
    ".mjs": "text/javascript",
    ".map": "application/json",
    ".webmanifest": "application/manifest+json",
}


class _Handler(BaseHTTPRequestHandler):
    lake_dir: Path
    dashboard_path: Path
    web_dist: Path | None = None

    server_version = "TrustOpsAssessment/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if self.web_dist is not None and self._serve_from_dist(parsed.path):
            return
        if parsed.path in {"/", "/console", "/console/"}:
            self._send_bytes(self.dashboard_path.read_bytes(), content_type="text/html; charset=utf-8")
            return
        if parsed.path == "/api/healthz":
            self._send_json({"ok": True, "service": "trustops-assessment"})
            return
        if parsed.path == "/api/posture/current":
            self._send_json(build_current_posture(self.lake_dir))
            return
        if parsed.path == "/api/violations":
            posture = build_current_posture(self.lake_dir)
            filters = parse_qs(parsed.query)
            framework = (filters.get("framework") or [None])[0]
            control_id = (filters.get("control_id") or [None])[0]
            violations = posture["violations"]
            if framework:
                control_frameworks = {
                    row["control_id"]: row["framework"]
                    for row in read_jsonl(self.lake_dir / "gold" / "control_posture.jsonl")
                }
                violations = [row for row in violations if control_frameworks.get(row["control_id"]) == framework]
            if control_id:
                violations = [row for row in violations if row["control_id"] == control_id]
            self._send_json({"count": len(violations), "violations": violations})
            return
        if parsed.path == "/api/controls":
            filters = parse_qs(parsed.query)
            control_id = (filters.get("control_id") or [None])[0]
            controls = read_jsonl(self.lake_dir / "gold" / "control_posture.jsonl")
            if control_id:
                controls = [row for row in controls if row["control_id"] == control_id]
            self._send_json({"controls": controls})
            return
        if parsed.path == "/api/control-tests":
            filters = parse_qs(parsed.query)
            result = (filters.get("result") or [None])[0]
            control_id = (filters.get("control_id") or [None])[0]
            rows = read_jsonl(self.lake_dir / "gold" / "control_tests.jsonl")
            if result:
                rows = [row for row in rows if row["result"] == result]
            if control_id:
                rows = [row for row in rows if row["control_id"] == control_id]
            self._send_json({"count": len(rows), "control_tests": rows})
            return
        if parsed.path == "/api/evidence":
            filters = parse_qs(parsed.query)
            control_id = (filters.get("control_id") or [None])[0]
            rows = read_jsonl(self.lake_dir / "silver" / "normalized_events.jsonl")
            if control_id:
                rows = [row for row in rows if control_id in row["control_ids"]]
            self._send_json({"count": len(rows), "evidence": rows})
            return
        if parsed.path == "/api/assets":
            self._send_json({"assets": read_jsonl(self.lake_dir / "gold" / "asset_risk.jsonl")})
            return
        self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/snapshots":
            body = self._read_json_body()
            reason = str(body.get("reason") or "api_request")
            path = write_assessment_snapshot(self.lake_dir, reason=reason)
            self._send_json({"snapshot_path": str(path), "reason": reason}, status=HTTPStatus.CREATED)
            return
        self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _serve_from_dist(self, request_path: str) -> bool:
        """Serve Next.js static export files when the React bundle is packaged.

        Routes resolve in this order:
          - /                                     -> dist/index.html (redirects to /console/dashboard/)
          - /console, /console/                   -> dist/index.html
          - /console/<route>/                     -> dist/<route>/index.html
          - /console/_next/static/<asset>         -> dist/_next/static/<asset>
          - any other /console/<asset>            -> dist/<asset>

        Returns True if the request was handled (200 or 404 served from dist).
        """
        dist = self.web_dist
        if dist is None:
            return False
        if request_path in {"/", "/console", "/console/"}:
            self._send_file(dist / "index.html", "text/html; charset=utf-8")
            return True
        if not request_path.startswith("/console/"):
            return False
        rel = request_path[len("/console/") :]
        # Strip query/fragment if any survived urlparse path handling.
        rel = rel.split("?", 1)[0].split("#", 1)[0]
        candidates: list[Path] = []
        # Treat directory-style routes as <route>/index.html.
        if rel.endswith("/") or not Path(rel).suffix:
            base = rel.rstrip("/")
            if base:
                candidates.append(dist / base / "index.html")
            candidates.append(dist / "index.html")
        if rel:
            candidates.append(dist / rel)
        for candidate in candidates:
            resolved = candidate.resolve()
            try:
                resolved.relative_to(dist.resolve())
            except ValueError:
                continue
            if resolved.is_file():
                content_type = (
                    _MIME_OVERRIDES.get(resolved.suffix)
                    or mimetypes.guess_type(resolved.name)[0]
                    or "application/octet-stream"
                )
                if content_type.startswith("text/") or content_type.endswith("javascript"):
                    content_type = f"{content_type}; charset=utf-8"
                self._send_file(resolved, content_type)
                return True
        return False

    def _send_file(self, path: Path, content_type: str) -> None:
        self._send_bytes(path.read_bytes(), content_type=content_type)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("content-length") or "0")
        if length <= 0:
            return {}
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _send_json(self, payload: object, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        self._send_bytes(body, status=status, content_type="application/json; charset=utf-8")

    def _send_bytes(
        self,
        body: bytes,
        *,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str,
    ) -> None:
        self.send_response(int(status))
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("access-control-allow-origin", "http://127.0.0.1")
        self.end_headers()
        self.wfile.write(body)
