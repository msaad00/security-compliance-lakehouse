from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from security_lakehouse.assessment import build_current_posture, write_assessment_snapshot
from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.io import read_json, read_jsonl
from security_lakehouse.pipeline import run_pipeline
from security_lakehouse.validation import validate_raw_events


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "security_events.jsonl"


def test_sample_raw_events_are_valid() -> None:
    rows = read_jsonl(RAW)

    assert validate_raw_events(rows) == []
    assert len(rows) == 10


def test_pipeline_writes_bronze_silver_gold_and_mart(tmp_path: Path) -> None:
    result = run_pipeline(RAW, tmp_path / "lake")

    assert result.raw_count == 10
    assert result.silver_count == 10
    assert result.control_count >= 8
    assert Path(result.mart_path).exists()

    bronze = read_jsonl(tmp_path / "lake" / "bronze" / "raw_events.jsonl")
    silver = read_jsonl(tmp_path / "lake" / "silver" / "normalized_events.jsonl")
    metrics = read_json(result.metrics_path)
    dashboard_data = read_json(result.dashboard_data_path)
    current_posture = read_json(tmp_path / "lake" / "gold" / "current_posture.json")

    assert len(bronze[0]["raw_sha256"]) == 64
    assert silver[0]["asset_id"] == "aws:iam:role/ml-prod-agent"
    assert metrics["critical_open"] == 2
    assert metrics["runtime_block_rate"] == 1.0
    assert metrics["top_risk_asset"] == "container:rag-api@sha256:91ab"
    assert [backend["name"] for backend in dashboard_data["lake_backends"]] == ["Snowflake", "ClickHouse"]
    assert current_posture["assessment_type"] == "current_posture"
    assert current_posture["posture"]["state"] == "critical"
    assert current_posture["posture"]["open_violation_count"] > 0

    with sqlite3.connect(result.mart_path) as conn:
        failing = conn.execute("select count(*) from control_posture where status = 'fail'").fetchone()[0]
        top_asset = conn.execute("select asset_id from asset_risk order by risk_score desc limit 1").fetchone()[0]

    assert failing >= 1
    assert top_asset == "container:rag-api@sha256:91ab"


def test_dashboard_render_uses_gold_data(tmp_path: Path) -> None:
    run_pipeline(RAW, tmp_path / "lake")

    output = render_dashboard(tmp_path / "lake", tmp_path / "dashboard" / "index.html")

    html = output.read_text(encoding="utf-8")
    assert "Internal TrustOps Console" in html
    assert "Continuous compliance evidence for one company" in html
    assert "Snowflake" in html
    assert "ClickHouse" in html
    assert "SOC2-CC6.1" in html
    assert "container:rag-api@sha256:91ab" in html


def test_assessment_engine_builds_current_and_point_in_time_posture(tmp_path: Path) -> None:
    run_pipeline(RAW, tmp_path / "lake")

    posture = build_current_posture(
        tmp_path / "lake",
        now=datetime(2026, 5, 22, 12, 0, tzinfo=timezone.utc),
    )
    snapshot = write_assessment_snapshot(
        tmp_path / "lake",
        output=tmp_path / "snapshot.json",
        reason="vendor_due_diligence",
    )

    assert posture["assessment_type"] == "current_posture"
    assert posture["posture"]["state"] == "critical"
    assert posture["posture"]["critical_violation_count"] >= 1
    assert posture["frameworks"][0]["score"] <= 100
    assert any(item["control_id"] == "SOC2-CC6.1" for item in posture["violations"])
    assert len(posture["assessment_hash"]) == 64

    snapshot_payload = read_json(snapshot)
    assert snapshot_payload["assessment_type"] == "point_in_time_snapshot"
    assert snapshot_payload["snapshot_reason"] == "vendor_due_diligence"


def test_validation_rejects_duplicate_event_ids() -> None:
    rows = [
        {
            "event_id": "evt-1",
            "tenant_id": "tenant",
            "event_time": "2026-05-20T00:00:00Z",
            "source": "scanner",
            "event_type": "finding",
            "entity": {"asset_id": "asset-1"},
        },
        {
            "event_id": "evt-1",
            "tenant_id": "tenant",
            "event_time": "2026-05-20T00:00:00Z",
            "source": "scanner",
            "event_type": "finding",
            "entity": {"asset_id": "asset-1"},
        },
    ]

    errors = validate_raw_events(rows)

    assert any("duplicate event_id" in error for error in errors)
