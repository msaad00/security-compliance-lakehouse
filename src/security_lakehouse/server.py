"""Lightweight human and agent API for the assessment engine."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from security_lakehouse.assessment import build_current_posture, write_assessment_snapshot
from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.io import read_jsonl


def serve(lake_dir: str | Path, *, host: str = "127.0.0.1", port: int = 8787) -> None:
    """Serve the TrustOps console and JSON assessment API."""
    lake = Path(lake_dir)
    dashboard = lake / "console.html"
    render_dashboard(lake, dashboard)

    class Handler(_Handler):
        lake_dir = lake
        dashboard_path = dashboard

    httpd = ThreadingHTTPServer((host, port), Handler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


class _Handler(BaseHTTPRequestHandler):
    lake_dir: Path
    dashboard_path: Path

    server_version = "TrustOpsAssessment/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/console"}:
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
            violations = posture["violations"]
            if framework:
                control_frameworks = {
                    row["control_id"]: row["framework"]
                    for row in read_jsonl(self.lake_dir / "gold" / "control_posture.jsonl")
                }
                violations = [row for row in violations if control_frameworks.get(row["control_id"]) == framework]
            self._send_json({"count": len(violations), "violations": violations})
            return
        if parsed.path == "/api/controls":
            self._send_json({"controls": read_jsonl(self.lake_dir / "gold" / "control_posture.jsonl")})
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
