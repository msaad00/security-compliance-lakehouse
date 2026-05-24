"""Triage persistence + verification + auditor-mode role gating tests."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from security_lakehouse.server import _Handler
from security_lakehouse.tracking import append_event, latest_state, list_events, tracking_path
from security_lakehouse.verification import verify_event

# --- pure-Python tracking module ------------------------------------------------


def test_append_and_list_round_trip(tmp_path: Path) -> None:
    rec = append_event(
        tmp_path,
        violation_id="SOC2-CC6.1:evt-001",
        actor="alice",
        state="triaged",
        assignee="bob",
        due_at="2026-06-01T00:00:00Z",
        note="initial review",
    )
    assert rec["violation_id"] == "SOC2-CC6.1:evt-001"
    assert rec["state"] == "triaged"
    assert tracking_path(tmp_path).is_file()

    events = list_events(tmp_path)
    assert len(events) == 1
    assert events[0]["assignee"] == "bob"

    filtered = list_events(tmp_path, violation_id="SOC2-CC6.1:evt-001")
    assert len(filtered) == 1
    assert list_events(tmp_path, violation_id="missing") == []


def test_latest_state_returns_most_recent(tmp_path: Path) -> None:
    append_event(tmp_path, violation_id="v1", actor="a", state="triaged")
    append_event(tmp_path, violation_id="v1", actor="a", state="in_progress")
    append_event(tmp_path, violation_id="v1", actor="a", state="resolved")
    latest = latest_state(tmp_path, violation_id="v1")
    assert latest is not None
    assert latest["state"] == "resolved"


def test_append_rejects_unknown_state(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        append_event(tmp_path, violation_id="v1", actor="a", state="bogus")


def test_append_requires_violation_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        append_event(tmp_path, violation_id="", actor="a", state="triaged")


# --- verification module --------------------------------------------------------


def _write_bronze_silver(tmp_path: Path) -> str:
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    bronze_dir.mkdir(parents=True)
    silver_dir.mkdir(parents=True)
    raw = {"event_id": "evt-001", "kind": "cloud.config", "payload": {"finding": "x"}}
    import hashlib

    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    bronze_record = {"ingested_at": "2026-05-23T00:00:00Z", "raw_sha256": expected, "raw": raw}
    (bronze_dir / "raw_events.jsonl").write_text(json.dumps(bronze_record) + "\n", encoding="utf-8")
    silver_record = {"event_id": "evt-001", "raw_sha256": expected, "source": "cspm"}
    (silver_dir / "normalized_events.jsonl").write_text(json.dumps(silver_record) + "\n", encoding="utf-8")
    return expected


def test_verify_event_matches(tmp_path: Path) -> None:
    expected = _write_bronze_silver(tmp_path)
    result = verify_event(tmp_path, "evt-001")
    assert result["verified"] is True
    assert result["expected_sha256"] == expected
    assert result["computed_sha256"] == expected


def test_verify_event_detects_drift(tmp_path: Path) -> None:
    _write_bronze_silver(tmp_path)
    silver_path = tmp_path / "silver" / "normalized_events.jsonl"
    rows = [json.loads(line) for line in silver_path.read_text(encoding="utf-8").splitlines() if line]
    rows[0]["raw_sha256"] = "0" * 64
    silver_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    result = verify_event(tmp_path, "evt-001")
    assert result["verified"] is False
    assert result["reason"]


def test_verify_event_missing_silver(tmp_path: Path) -> None:
    result = verify_event(tmp_path, "evt-missing")
    assert result["verified"] is False
    assert result["source_layer"] == "missing"


# --- HTTP server integration ----------------------------------------------------


def _spin_handler(lake: Path) -> ThreadingHTTPServer:
    (lake / "gold").mkdir(parents=True, exist_ok=True)
    (lake / "silver").mkdir(parents=True, exist_ok=True)
    (lake / "console.html").write_bytes(b"<!doctype html>")

    class Handler(_Handler):
        lake_dir = lake
        dashboard_path = lake / "console.html"
        web_dist = None

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _request(
    server: ThreadingHTTPServer,
    method: str,
    path: str,
    *,
    body: dict | None = None,
    role: str | None = None,
) -> tuple[int, dict]:
    host, port = server.server_address
    url = f"http://{host}:{port}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(  # noqa: S310 (local test url)
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    if role:
        req.add_header("X-Trust-Role", role)
    try:
        with urllib.request.urlopen(req) as resp:
            return int(resp.status), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return int(exc.code), json.loads(exc.read().decode("utf-8"))


def test_triage_round_trip_via_http(tmp_path: Path) -> None:
    server = _spin_handler(tmp_path)
    try:
        status, body = _request(
            server,
            "POST",
            "/api/violations/SOC2-CC6.1:evt-001/triage",
            body={"state": "triaged", "actor": "carol", "assignee": "dan"},
        )
        assert status == HTTPStatus.CREATED
        assert body["event"]["state"] == "triaged"

        status, body = _request(server, "GET", "/api/violations/SOC2-CC6.1:evt-001/tracking")
        assert status == HTTPStatus.OK
        assert body["current_state"] == "triaged"
        assert len(body["events"]) == 1
    finally:
        server.shutdown()


def test_triage_rejects_unknown_state(tmp_path: Path) -> None:
    server = _spin_handler(tmp_path)
    try:
        status, body = _request(
            server,
            "POST",
            "/api/violations/v1/triage",
            body={"state": "made-up"},
        )
        assert status == HTTPStatus.BAD_REQUEST
        assert "state must be" in body["reason"]
    finally:
        server.shutdown()


def test_auditor_role_blocks_post(tmp_path: Path) -> None:
    server = _spin_handler(tmp_path)
    try:
        status, body = _request(server, "POST", "/api/snapshots", body={"reason": "audit"}, role="auditor")
        assert status == HTTPStatus.FORBIDDEN
        assert body["error"] == "forbidden"

        status, body = _request(
            server,
            "POST",
            "/api/violations/v1/triage",
            body={"state": "triaged"},
            role="auditor",
        )
        assert status == HTTPStatus.FORBIDDEN
    finally:
        server.shutdown()


def test_auditor_role_redacts_pii_in_responses(tmp_path: Path) -> None:
    append_event(
        tmp_path,
        violation_id="v1",
        actor="alice",
        state="triaged",
        assignee="bob",
        note="sensitive remediation context",
    )
    server = _spin_handler(tmp_path)
    try:
        status, body = _request(server, "GET", "/api/violations/v1/tracking", role="auditor")
        assert status == HTTPStatus.OK
        event = body["events"][0]
        assert event["actor"] == "[redacted]"
        assert event["assignee"] == "[redacted]"
        assert event["note"] == "[redacted]"
        assert event["state"] == "triaged"
    finally:
        server.shutdown()


def test_snapshot_list_endpoint(tmp_path: Path) -> None:
    snapshots_dir = tmp_path / "gold" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "assessment-20260520T000000.json").write_text(
        json.dumps(
            {
                "assessment_type": "point_in_time_snapshot",
                "evaluated_at": "2026-05-20T00:00:00Z",
                "snapshot_reason": "monthly_review",
                "assessment_hash": "abc",
                "posture": {
                    "score": 88.0,
                    "open_violation_count": 4,
                    "critical_violation_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    server = _spin_handler(tmp_path)
    try:
        status, body = _request(server, "GET", "/api/snapshots")
        assert status == HTTPStatus.OK
        assert body["count"] == 1
        assert body["snapshots"][0]["reason"] == "monthly_review"
        assert body["snapshots"][0]["posture_score"] == 88.0
    finally:
        server.shutdown()


def test_verify_endpoint_returns_match_status(tmp_path: Path) -> None:
    _write_bronze_silver(tmp_path)
    server = _spin_handler(tmp_path)
    try:
        status, body = _request(server, "POST", "/api/evidence/evt-001/verify")
        assert status == HTTPStatus.OK
        assert body["verified"] is True
        assert body["source_layer"] == "bronze"
    finally:
        server.shutdown()
