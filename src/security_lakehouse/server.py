"""Lightweight human and agent API for the assessment engine."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from security_lakehouse.assessment import build_current_posture, write_assessment_snapshot
from security_lakehouse.audit_log import build_audit_log
from security_lakehouse.connector_state import (
    append_config_event,
    build_catalog_view,
    list_runs,
    run_probe,
)
from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.framework_provenance import build_framework_view
from security_lakehouse.graph import build_compliance_graph, build_framework_crosswalk
from security_lakehouse.io import read_jsonl
from security_lakehouse.mappings import build_reviewed_crosswalk, load_control_article_mappings
from security_lakehouse.readiness import build_readiness_view
from security_lakehouse.scheduler import tick as scheduler_tick
from security_lakehouse.tracking import ALLOWED_STATES, append_event, latest_state, list_events
from security_lakehouse.trust_share import create_share, list_shares, revoke_share
from security_lakehouse.verification import verify_event
from security_lakehouse.web import web_dist_dir, web_dist_index
from security_lakehouse.workflows import (
    action_catalog,
    get_workflow,
    list_workflows,
    run_action,
    run_workflow,
    save_workflow,
)
from security_lakehouse.workflows import (
    list_runs as list_workflow_runs,
)

AUDITOR_ROLE = "auditor"
REDACTED_FIELDS = {"asset_owner", "actor", "assignee", "note", "credentials"}


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
        if parsed.path.startswith("/api/v1/"):
            self._handle_v1_get(parsed.path, parse_qs(parsed.query))
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
        if parsed.path == "/api/snapshots":
            snapshots = self._list_snapshots()
            self._send_json({"count": len(snapshots), "snapshots": snapshots})
            return
        if parsed.path == "/api/connectors":
            view = build_catalog_view(self.lake_dir)
            self._send_json({"count": len(view), "connectors": view})
            return
        if parsed.path == "/api/frameworks":
            view = build_framework_view()
            self._send_json({"count": len(view), "frameworks": view})
            return
        if parsed.path == "/api/graph":
            self._send_json(build_compliance_graph(self.lake_dir))
            return
        if parsed.path == "/api/crosswalk":
            self._send_json(build_framework_crosswalk())
            return
        if parsed.path == "/api/crosswalk/reviewed":
            self._send_json(build_reviewed_crosswalk())
            return
        if parsed.path == "/api/mappings":
            mappings = load_control_article_mappings()
            self._send_json({"count": len(mappings), "mappings": list(mappings.values())})
            return
        if parsed.path == "/api/readiness":
            view = build_readiness_view()
            self._send_json({"count": len(view), "frameworks": view})
            return
        if parsed.path == "/api/workflows":
            rows = list_workflows(self.lake_dir)
            self._send_json({"count": len(rows), "workflows": rows})
            return
        if parsed.path == "/api/workflows/actions":
            self._send_json({"actions": action_catalog()})
            return
        workflow_get_match = self._match_workflow_get(parsed.path)
        if workflow_get_match is not None:
            workflow = get_workflow(self.lake_dir, workflow_get_match)
            if workflow is None:
                self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(workflow)
            return
        workflow_runs_match = self._match_workflow_runs(parsed.path)
        if workflow_runs_match is not None:
            rows = list_workflow_runs(self.lake_dir, workflow_runs_match)
            self._send_json({"workflow_id": workflow_runs_match, "runs": rows})
            return
        if parsed.path == "/api/trust-shares":
            include_revoked = (parse_qs(parsed.query).get("include_revoked") or ["false"])[0].lower() in {
                "1",
                "true",
                "yes",
            }
            shares = list_shares(self.lake_dir, include_revoked=include_revoked)
            self._send_json({"count": len(shares), "shares": shares})
            return
        if parsed.path == "/api/audit-log":
            filters = parse_qs(parsed.query)
            category = (filters.get("category") or [None])[0]
            actor = (filters.get("actor") or [None])[0]
            limit = int((filters.get("limit") or ["200"])[0])
            entries = build_audit_log(self.lake_dir, category=category, actor=actor, limit=max(1, min(limit, 1000)))
            self._send_json({"count": len(entries), "entries": entries})
            return
        runs_match = self._match_connector_runs(parsed.path)
        if runs_match is not None:
            rows = list_runs(self.lake_dir, runs_match)
            self._send_json({"connector_id": runs_match, "runs": rows})
            return
        tracking_match = self._match_violation_tracking(parsed.path)
        if tracking_match is not None:
            events = list_events(self.lake_dir, violation_id=tracking_match)
            current = latest_state(self.lake_dir, violation_id=tracking_match)
            self._send_json(
                {
                    "violation_id": tracking_match,
                    "current_state": (current or {}).get("state", "open"),
                    "events": [self._redact(e) for e in events],
                }
            )
            return
        self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if self._role() == AUDITOR_ROLE:
            self._send_json(
                {"error": "forbidden", "reason": "auditor role is read-only"},
                status=HTTPStatus.FORBIDDEN,
            )
            return
        if parsed.path.startswith("/api/v1/"):
            self._handle_v1_post(parsed.path)
            return
        if parsed.path == "/api/snapshots":
            body = self._read_json_body()
            reason = str(body.get("reason") or "api_request")
            path = write_assessment_snapshot(self.lake_dir, reason=reason)
            self._send_json(
                {"snapshot_path": str(path), "reason": reason},
                status=HTTPStatus.CREATED,
            )
            return
        triage_match = self._match_violation_triage(parsed.path)
        if triage_match is not None:
            body = self._read_json_body()
            state = str(body.get("state") or "").lower()
            if state not in ALLOWED_STATES:
                self._send_json(
                    {"error": "bad_request", "reason": f"state must be one of {sorted(ALLOWED_STATES)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            record = append_event(
                self.lake_dir,
                violation_id=triage_match,
                actor=str(body.get("actor") or "anonymous"),
                state=state,
                assignee=body.get("assignee"),
                due_at=body.get("due_at"),
                note=body.get("note"),
            )
            self._send_json({"event": record}, status=HTTPStatus.CREATED)
            return
        verify_match = self._match_evidence_verify(parsed.path)
        if verify_match is not None:
            result = verify_event(self.lake_dir, verify_match)
            self._send_json(result)
            return
        configure_match = self._match_connector_configure(parsed.path)
        if configure_match is not None:
            body = self._read_json_body()
            state = str(body.get("state") or "enabled").lower()
            try:
                record = append_config_event(
                    self.lake_dir,
                    connector_id=configure_match,
                    state=state,
                    actor=str(body.get("actor") or "console"),
                    credentials=body.get("credentials") or {},
                    options=body.get("options") or {},
                )
            except ValueError as exc:
                self._send_json(
                    {"error": "bad_request", "reason": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_json({"event": record}, status=HTTPStatus.CREATED)
            return
        probe_match = self._match_connector_probe(parsed.path)
        if probe_match is not None:
            body = self._read_json_body()
            record = run_probe(
                self.lake_dir,
                connector_id=probe_match,
                actor=str(body.get("actor") or "console"),
            )
            self._send_json({"run": record}, status=HTTPStatus.CREATED)
            return
        if parsed.path == "/api/workflows":
            body = self._read_json_body()
            try:
                record = save_workflow(
                    self.lake_dir,
                    workflow_id=body.get("workflow_id"),
                    name=str(body.get("name") or ""),
                    description=str(body.get("description") or ""),
                    nodes=body.get("nodes") or [],
                    edges=body.get("edges") or [],
                    actor=str(body.get("actor") or "console"),
                )
            except ValueError as exc:
                self._send_json(
                    {"error": "bad_request", "reason": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_json({"workflow": record}, status=HTTPStatus.CREATED)
            return
        if parsed.path == "/api/scheduler/tick":
            results = scheduler_tick(self.lake_dir)
            self._send_json({"fired": len(results), "results": results}, status=HTTPStatus.CREATED)
            return
        if parsed.path == "/api/workflows/actions/run":
            body = self._read_json_body()
            try:
                output = run_action(
                    self.lake_dir,
                    node_type=str(body.get("node_type") or ""),
                    params=body.get("params") or {},
                )
            except ValueError as exc:
                self._send_json(
                    {"error": "bad_request", "reason": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_json({"output": output}, status=HTTPStatus.CREATED)
            return
        workflow_run_match = self._match_workflow_run(parsed.path)
        if workflow_run_match is not None:
            try:
                run = run_workflow(
                    self.lake_dir,
                    workflow_id=workflow_run_match,
                    actor=str(self._read_json_body().get("actor") or "console"),
                )
            except ValueError as exc:
                self._send_json(
                    {"error": "bad_request", "reason": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_json({"run": run}, status=HTTPStatus.CREATED)
            return
        if parsed.path == "/api/trust-shares":
            body = self._read_json_body()
            try:
                share = create_share(
                    self.lake_dir,
                    role=str(body.get("role") or "auditor"),
                    scope=str(body.get("scope") or "posture_full"),
                    expires_in_hours=int(body.get("expires_in_hours") or 24),
                    created_by=str(body.get("created_by") or "console"),
                    framework_id=body.get("framework_id"),
                )
            except ValueError as exc:
                self._send_json(
                    {"error": "bad_request", "reason": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_json({"share": share}, status=HTTPStatus.CREATED)
            return
        revoke_match = self._match_trust_share_revoke(parsed.path)
        if revoke_match is not None:
            revoked = revoke_share(self.lake_dir, revoke_match)
            if revoked is None:
                self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json({"share": revoked}, status=HTTPStatus.CREATED)
            return
        self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_v1_get(self, path: str, query: dict[str, list[str]]) -> None:
        """Versioned API surface for headless clients.

        The legacy `/api/*` routes remain UI-compatible. `/api/v1/*` wraps
        resources in a stable envelope and applies common collection controls.
        """
        if path == "/api/v1/healthz":
            self._send_v1("healthz", {"ok": True, "service": "trustops-assessment"})
            return
        if path == "/api/v1/posture/current":
            self._send_v1("posture.current", build_current_posture(self.lake_dir))
            return
        if path == "/api/v1/controls":
            self._send_v1_collection(
                "controls",
                read_jsonl(self.lake_dir / "gold" / "control_posture.jsonl"),
                query,
            )
            return
        if path == "/api/v1/control-tests":
            self._send_v1_collection(
                "control-tests",
                read_jsonl(self.lake_dir / "gold" / "control_tests.jsonl"),
                query,
            )
            return
        if path == "/api/v1/evidence":
            self._send_v1_collection(
                "evidence",
                read_jsonl(self.lake_dir / "silver" / "normalized_events.jsonl"),
                query,
            )
            return
        if path == "/api/v1/assets":
            self._send_v1_collection(
                "assets",
                read_jsonl(self.lake_dir / "gold" / "asset_risk.jsonl"),
                query,
            )
            return
        if path == "/api/v1/violations":
            self._send_v1_collection("violations", build_current_posture(self.lake_dir)["violations"], query)
            return
        if path == "/api/v1/snapshots":
            self._send_v1_collection("snapshots", self._list_snapshots(), query)
            return
        self._send_v1_error("not_found", status=HTTPStatus.NOT_FOUND, detail=f"unknown route {path}")

    def _handle_v1_post(self, path: str) -> None:
        if path == "/api/v1/snapshots":
            body = self._read_json_body()
            reason = str(body.get("reason") or "api_request")
            snapshot_path = write_assessment_snapshot(self.lake_dir, reason=reason)
            self._send_v1(
                "snapshots",
                {"snapshot_path": str(snapshot_path), "reason": reason},
                status=HTTPStatus.CREATED,
            )
            return
        self._send_v1_error("not_found", status=HTTPStatus.NOT_FOUND, detail=f"unknown route {path}")

    def _send_v1(
        self,
        resource: str,
        data: object,
        *,
        status: HTTPStatus = HTTPStatus.OK,
        meta: dict[str, object] | None = None,
    ) -> None:
        payload = {
            "data": data,
            "meta": {
                "api_version": "v1",
                "resource": resource,
                **(meta or {}),
            },
            "errors": [],
        }
        self._send_json(payload, status=status)

    def _send_v1_error(
        self,
        code: str,
        *,
        status: HTTPStatus,
        detail: str,
        resource: str = "unknown",
    ) -> None:
        self._send_json(
            {
                "data": None,
                "meta": {"api_version": "v1", "resource": resource},
                "errors": [{"code": code, "detail": detail}],
            },
            status=status,
        )

    def _send_v1_collection(self, resource: str, rows: list[dict[str, Any]], query: dict[str, list[str]]) -> None:
        try:
            filtered_rows, applied_filters = self._filter_collection(rows, query)
            sorted_rows, sort = self._sort_collection(filtered_rows, query)
            page_rows, limit, offset = self._paginate_collection(sorted_rows, query)
        except ValueError as exc:
            self._send_v1_error("bad_request", status=HTTPStatus.BAD_REQUEST, detail=str(exc), resource=resource)
            return
        self._send_v1(
            resource,
            page_rows,
            meta={
                "count": len(filtered_rows),
                "returned": len(page_rows),
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "filters": applied_filters,
            },
        )

    @staticmethod
    def _filter_collection(
        rows: list[dict[str, Any]],
        query: dict[str, list[str]],
    ) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
        reserved = {"limit", "offset", "sort"}
        filters = {
            key: [value for raw in values for value in raw.split(",") if value]
            for key, values in query.items()
            if key not in reserved
        }
        if not filters:
            return rows, {}

        def matches(row: dict[str, Any]) -> bool:
            for field, expected_values in filters.items():
                actual = row.get(field)
                if actual is None:
                    return False
                if isinstance(actual, list):
                    actual_values = {str(item) for item in actual}
                    if not any(expected in actual_values for expected in expected_values):
                        return False
                elif str(actual) not in expected_values:
                    return False
            return True

        return [row for row in rows if matches(row)], filters

    @staticmethod
    def _sort_collection(
        rows: list[dict[str, Any]],
        query: dict[str, list[str]],
    ) -> tuple[list[dict[str, Any]], str | None]:
        sort = (query.get("sort") or [None])[0]
        if not sort:
            return rows, None
        reverse = sort.startswith("-")
        field = sort[1:] if reverse else sort
        if not field:
            raise ValueError("sort must name a field, optionally prefixed with '-'")
        sortable = [row for row in rows if row.get(field) is not None]
        missing = [row for row in rows if row.get(field) is None]

        def sort_key(row: dict[str, Any]) -> tuple[int, float | str]:
            value = row[field]
            if isinstance(value, int | float):
                return (0, float(value))
            return (1, str(value))

        return sorted(sortable, key=sort_key, reverse=reverse) + missing, sort

    @staticmethod
    def _paginate_collection(
        rows: list[dict[str, Any]],
        query: dict[str, list[str]],
    ) -> tuple[list[dict[str, Any]], int, int]:
        try:
            limit = int((query.get("limit") or ["100"])[0])
            offset = int((query.get("offset") or ["0"])[0])
        except ValueError as exc:
            raise ValueError("limit and offset must be integers") from exc
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        return rows[offset : offset + limit], limit, offset

    @staticmethod
    def _match_violation_tracking(path: str) -> str | None:
        # /api/violations/{id}/tracking
        if not path.startswith("/api/violations/") or not path.endswith("/tracking"):
            return None
        rest = path[len("/api/violations/") : -len("/tracking")]
        return rest or None

    @staticmethod
    def _match_violation_triage(path: str) -> str | None:
        # /api/violations/{id}/triage
        if not path.startswith("/api/violations/") or not path.endswith("/triage"):
            return None
        rest = path[len("/api/violations/") : -len("/triage")]
        return rest or None

    @staticmethod
    def _match_evidence_verify(path: str) -> str | None:
        # /api/evidence/{id}/verify
        if not path.startswith("/api/evidence/") or not path.endswith("/verify"):
            return None
        rest = path[len("/api/evidence/") : -len("/verify")]
        return rest or None

    @staticmethod
    def _match_connector_configure(path: str) -> str | None:
        # /api/connectors/{id}/configure
        if not path.startswith("/api/connectors/") or not path.endswith("/configure"):
            return None
        rest = path[len("/api/connectors/") : -len("/configure")]
        return rest or None

    @staticmethod
    def _match_connector_probe(path: str) -> str | None:
        # /api/connectors/{id}/probe
        if not path.startswith("/api/connectors/") or not path.endswith("/probe"):
            return None
        rest = path[len("/api/connectors/") : -len("/probe")]
        return rest or None

    @staticmethod
    def _match_connector_runs(path: str) -> str | None:
        # /api/connectors/{id}/runs
        if not path.startswith("/api/connectors/") or not path.endswith("/runs"):
            return None
        rest = path[len("/api/connectors/") : -len("/runs")]
        return rest or None

    @staticmethod
    def _match_workflow_get(path: str) -> str | None:
        # /api/workflows/{id} but exclude /api/workflows/actions and /api/workflows/actions/run
        if not path.startswith("/api/workflows/"):
            return None
        rest = path[len("/api/workflows/") :]
        if rest in {"", "actions"} or rest.startswith("actions/") or "/" in rest:
            return None
        return rest

    @staticmethod
    def _match_workflow_run(path: str) -> str | None:
        # /api/workflows/{id}/run
        if not path.startswith("/api/workflows/") or not path.endswith("/run"):
            return None
        rest = path[len("/api/workflows/") : -len("/run")]
        if not rest or "/" in rest or rest == "actions":
            return None
        return rest

    @staticmethod
    def _match_workflow_runs(path: str) -> str | None:
        # /api/workflows/{id}/runs
        if not path.startswith("/api/workflows/") or not path.endswith("/runs"):
            return None
        rest = path[len("/api/workflows/") : -len("/runs")]
        if not rest or "/" in rest or rest == "actions":
            return None
        return rest

    @staticmethod
    def _match_trust_share_revoke(path: str) -> str | None:
        # /api/trust-shares/{id}/revoke
        if not path.startswith("/api/trust-shares/") or not path.endswith("/revoke"):
            return None
        rest = path[len("/api/trust-shares/") : -len("/revoke")]
        return rest or None

    def _list_snapshots(self) -> list[dict[str, object]]:
        snapshots_dir = self.lake_dir / "gold" / "snapshots"
        if not snapshots_dir.is_dir():
            return []
        out: list[dict[str, object]] = []
        for path in sorted(snapshots_dir.glob("assessment-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            posture = payload.get("posture") or {}
            out.append(
                {
                    "snapshot_path": str(path),
                    "evaluated_at": payload.get("evaluated_at"),
                    "reason": payload.get("snapshot_reason") or "manual",
                    "assessment_hash": payload.get("assessment_hash"),
                    "posture_score": posture.get("score"),
                    "open_violation_count": posture.get("open_violation_count"),
                    "critical_violation_count": posture.get("critical_violation_count"),
                }
            )
        return out

    def _role(self) -> str:
        return (self.headers.get("X-Trust-Role") or "").strip().lower()

    def _redact(self, payload: object) -> object:
        if self._role() != AUDITOR_ROLE:
            return payload
        if isinstance(payload, dict):
            return {k: ("[redacted]" if k in REDACTED_FIELDS else self._redact(v)) for k, v in payload.items()}
        if isinstance(payload, list):
            return [self._redact(item) for item in payload]
        return payload

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
        body = json.dumps(self._redact(payload), indent=2, sort_keys=True, default=str).encode("utf-8")
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
