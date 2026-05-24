"""Compliance graph, crosswalk, and mockup-fixture tests."""

from __future__ import annotations

import json
import threading
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from security_lakehouse.fixtures import find_fixture, list_fixtures
from security_lakehouse.graph import build_compliance_graph, build_framework_crosswalk
from security_lakehouse.server import _Handler


def _bootstrap_lake(lake: Path) -> None:
    (lake / "silver").mkdir(parents=True, exist_ok=True)
    (lake / "silver" / "normalized_events.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    "event_id": f"evt-{i}",
                    "event_type": "cloud.config",
                    "asset_id": f"aws:role/svc-{i}",
                    "control_ids": ["SOC2-CC6.1"],
                    "status": "passed",
                    "severity": "info",
                }
            )
            for i in range(2)
        )
        + "\n",
        encoding="utf-8",
    )
    (lake / "gold").mkdir(parents=True, exist_ok=True)
    (lake / "gold" / "asset_risk.jsonl").write_text(
        json.dumps(
            {
                "asset_id": "aws:role/svc-0",
                "asset_owner": "platform",
                "asset_type": "iam_role",
                "environment": "prod",
                "risk_score": 12,
                "critical_open": 0,
                "high_open": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_compliance_graph_has_four_layers(tmp_path: Path) -> None:
    _bootstrap_lake(tmp_path)
    graph = build_compliance_graph(tmp_path)
    kinds = {n["kind"] for n in graph["nodes"]}
    assert {"framework", "control", "evidence_type", "asset"}.issubset(kinds)
    assert graph["counts"]["asset"] >= 1
    edge_kinds = {e["kind"] for e in graph["edges"]}
    assert {
        "framework_has_control",
        "control_requires_evidence",
        "evidence_covers_asset",
    }.issubset(edge_kinds)


def test_build_compliance_graph_dedupes_evidence_types(tmp_path: Path) -> None:
    _bootstrap_lake(tmp_path)
    graph = build_compliance_graph(tmp_path)
    evidence_nodes = [n for n in graph["nodes"] if n["kind"] == "evidence_type"]
    assert len(evidence_nodes) == 1
    assert evidence_nodes[0]["event_count"] == 2


def test_crosswalk_returns_self_diagonal_and_shared_dimensions() -> None:
    crosswalk = build_framework_crosswalk()
    fids = crosswalk["frameworks"]
    assert len(fids) >= 2
    for row in crosswalk["matrix"]:
        for cell in row["cells"]:
            if cell["framework_id"] == row["framework_id"]:
                assert cell["is_self"] is True
            else:
                assert isinstance(cell["shared_risk_domains"], list)
                assert isinstance(cell["shared_owners"], list)


def test_list_fixtures_finds_shipped_companies() -> None:
    fixtures = list_fixtures()
    names = {f.company for f in fixtures}
    assert {"saas", "ai_lab"}.issubset(names)
    saas = find_fixture("saas")
    assert saas is not None
    assert saas.event_count > 0
    assert "SOC2-CC6.1" in saas.controls


def test_find_fixture_returns_none_for_unknown() -> None:
    assert find_fixture("does-not-exist") is None


def test_fixture_raw_events_use_only_known_controls() -> None:
    from security_lakehouse.catalog import load_control_catalog

    catalog = set(load_control_catalog().keys())
    for fixture in list_fixtures():
        for control_id in fixture.controls:
            assert control_id in catalog, f"fixture {fixture.company} references unknown control {control_id}"


# --- HTTP smoke -----------------------------------------------------------------


def _spin(lake: Path) -> ThreadingHTTPServer:
    (lake / "console.html").write_bytes(b"<!doctype html>")

    class Handler(_Handler):
        lake_dir = lake
        dashboard_path = lake / "console.html"
        web_dist = None

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict]:
    host, port = server.server_address
    with urllib.request.urlopen(f"http://{host}:{port}{path}") as resp:  # noqa: S310
        return int(resp.status), json.loads(resp.read().decode("utf-8"))


@pytest.mark.parametrize("path", ["/api/graph", "/api/crosswalk"])
def test_graph_endpoints_return_200(tmp_path: Path, path: str) -> None:
    _bootstrap_lake(tmp_path)
    server = _spin(tmp_path)
    try:
        status, body = _get(server, path)
        assert status == HTTPStatus.OK
        assert isinstance(body, dict)
    finally:
        server.shutdown()
