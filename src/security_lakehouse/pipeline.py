"""End-to-end lakehouse pipeline."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from security_lakehouse.controls import expand_controls, load_control_map
from security_lakehouse.io import read_jsonl, write_json, write_jsonl
from security_lakehouse.models import PipelineResult, SEVERITY_SCORE, parse_event_time, utc_iso
from security_lakehouse.validation import validate_raw_events


def run_pipeline(raw_path: str | Path, out_dir: str | Path, *, mapping_path: str | Path | None = None) -> PipelineResult:
    raw_rows = read_jsonl(raw_path)
    errors = validate_raw_events(raw_rows)
    if errors:
        raise ValueError("raw evidence validation failed:\n" + "\n".join(errors))

    out = Path(out_dir)
    bronze_dir = out / "bronze"
    silver_dir = out / "silver"
    gold_dir = out / "gold"
    mart_dir = out / "mart"
    for directory in (bronze_dir, silver_dir, gold_dir, mart_dir):
        directory.mkdir(parents=True, exist_ok=True)

    bronze_rows = [_bronze_row(row) for row in raw_rows]
    silver_rows = [_silver_row(row, bronze["raw_sha256"]) for row, bronze in zip(raw_rows, bronze_rows)]
    control_map = load_control_map(mapping_path)
    control_rows = _build_control_rows(silver_rows, control_map)
    asset_rows = _build_asset_rows(silver_rows)
    metrics = _build_metrics(silver_rows, control_rows, asset_rows)
    dashboard_data = {
        "generated_at": utc_iso(datetime.now(timezone.utc)),
        "lake_backends": [
            {
                "name": "Snowflake",
                "role": "Governed Evidence Lake",
                "best_for": "audit, GRC, RBAC, retention, executive reporting",
                "artifact": "deploy/snowflake/schema.sql",
            },
            {
                "name": "ClickHouse",
                "role": "Telemetry Analytics Lake",
                "best_for": "runtime events, detections, fast aggregations, dashboards",
                "artifact": "deploy/clickhouse/schema.sql",
            },
        ],
        "metrics": metrics,
        "pipeline_stages": _build_pipeline_stages(raw_rows, bronze_rows, silver_rows, control_rows, asset_rows),
        "source_mix": _build_source_mix(silver_rows),
        "severity_mix": _build_severity_mix(silver_rows),
        "backend_routes": _build_backend_routes(silver_rows),
        "control_posture": control_rows,
        "asset_risk": asset_rows,
        "recent_events": sorted(silver_rows, key=lambda item: item["event_time"], reverse=True)[:10],
    }

    write_jsonl(bronze_dir / "raw_events.jsonl", bronze_rows)
    write_jsonl(silver_dir / "normalized_events.jsonl", silver_rows)
    write_jsonl(gold_dir / "control_posture.jsonl", control_rows)
    write_jsonl(gold_dir / "asset_risk.jsonl", asset_rows)
    write_json(gold_dir / "metrics.json", metrics)
    write_json(gold_dir / "dashboard_data.json", dashboard_data)
    write_json(
        out / "manifest.json",
        {
            "raw_path": str(raw_path),
            "zones": {
                "bronze": str(bronze_dir / "raw_events.jsonl"),
                "silver": str(silver_dir / "normalized_events.jsonl"),
                "gold_metrics": str(gold_dir / "metrics.json"),
                "gold_control_posture": str(gold_dir / "control_posture.jsonl"),
                "gold_asset_risk": str(gold_dir / "asset_risk.jsonl"),
            },
        },
    )

    mart_path = mart_dir / "security_lakehouse.sqlite"
    _write_mart(mart_path, silver_rows, control_rows, asset_rows, metrics)
    from security_lakehouse.assessment import write_current_posture

    write_current_posture(out)
    return PipelineResult(
        output_dir=str(out),
        raw_count=len(raw_rows),
        silver_count=len(silver_rows),
        control_count=len(control_rows),
        asset_count=len(asset_rows),
        mart_path=str(mart_path),
        metrics_path=str(gold_dir / "metrics.json"),
        dashboard_data_path=str(gold_dir / "dashboard_data.json"),
    )


def _bronze_row(row: dict[str, Any]) -> dict[str, Any]:
    canonical = json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)
    return {
        "ingested_at": utc_iso(datetime.now(timezone.utc)),
        "raw_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "raw": row,
    }


def _silver_row(row: dict[str, Any], raw_sha256: str) -> dict[str, Any]:
    entity = row["entity"]
    evidence = row.get("evidence") or {}
    attributes = row.get("attributes") or {}
    asset_id = str(entity.get("asset_id") or entity.get("id") or entity.get("name") or "unknown")
    severity = str(row.get("severity", "info")).lower()
    return {
        "event_id": str(row["event_id"]),
        "tenant_id": str(row["tenant_id"]),
        "event_time": utc_iso(parse_event_time(str(row["event_time"]))),
        "source": str(row["source"]),
        "event_type": str(row["event_type"]),
        "asset_id": asset_id,
        "asset_type": str(entity.get("asset_type") or entity.get("type") or "unknown"),
        "asset_owner": str(entity.get("owner") or attributes.get("owner") or "unassigned"),
        "environment": str(entity.get("environment") or attributes.get("environment") or "unknown"),
        "severity": severity,
        "severity_score": SEVERITY_SCORE[severity],
        "status": str(row.get("status", "observed")).lower(),
        "control_ids": [str(item) for item in row.get("controls", [])],
        "evidence_id": str(evidence.get("evidence_id") or row["event_id"]),
        "evidence_ref": str(evidence.get("uri") or evidence.get("ref") or ""),
        "evidence_collected_at": str(evidence.get("collected_at") or row["event_time"]),
        "raw_sha256": raw_sha256,
    }


def _build_control_rows(silver_rows: list[dict[str, Any]], control_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in silver_rows:
        for control in expand_controls(row["control_ids"], control_map):
            grouped[str(control["control_id"])].append({**row, "_control": control})

    control_rows: list[dict[str, Any]] = []
    for control_id, rows in grouped.items():
        control = rows[0]["_control"]
        failing_rows = [row for row in rows if row["status"] in {"open", "failed", "blocked", "noncompliant"}]
        evidence_rows = [row for row in rows if row["evidence_ref"]]
        max_score = max((row["severity_score"] for row in rows), default=0)
        status = "fail" if failing_rows else "pass"
        coverage = round(len(evidence_rows) / len(rows), 4) if rows else 0
        control_rows.append(
            {
                "control_id": control_id,
                "framework": str(control.get("framework", "unknown")),
                "title": str(control.get("title", "")),
                "risk_domain": str(control.get("risk_domain", "unknown")),
                "owner": str(control.get("owner", "security")),
                "status": status,
                "risk_score": max_score,
                "event_count": len(rows),
                "open_event_count": len(failing_rows),
                "evidence_count": len(evidence_rows),
                "evidence_coverage": coverage,
                "latest_event_time": max(row["event_time"] for row in rows),
            }
        )
    return sorted(control_rows, key=lambda item: (-int(item["risk_score"]), item["control_id"]))


def _build_asset_rows(silver_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in silver_rows:
        grouped[row["asset_id"]].append(row)
    assets: list[dict[str, Any]] = []
    for asset_id, rows in grouped.items():
        sev = Counter(row["severity"] for row in rows if row["status"] in {"open", "failed", "blocked", "noncompliant"})
        risk_score = max((row["severity_score"] for row in rows), default=0) + min(20, len(rows) * 2)
        assets.append(
            {
                "asset_id": asset_id,
                "asset_type": rows[0]["asset_type"],
                "asset_owner": rows[0]["asset_owner"],
                "environment": rows[0]["environment"],
                "risk_score": min(100, risk_score),
                "critical_open": sev["critical"],
                "high_open": sev["high"],
                "event_count": len(rows),
                "latest_event_time": max(row["event_time"] for row in rows),
            }
        )
    return sorted(assets, key=lambda item: (-int(item["risk_score"]), item["asset_id"]))


def _build_metrics(
    silver_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    asset_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    open_rows = [row for row in silver_rows if row["status"] in {"open", "failed", "blocked", "noncompliant"}]
    runtime_rows = [row for row in silver_rows if row["event_type"].startswith("runtime.")]
    blocked_runtime = [row for row in runtime_rows if row["status"] in {"blocked", "failed"}]
    evidence_rows = [row for row in silver_rows if row["evidence_ref"]]
    passing_controls = [row for row in control_rows if row["status"] == "pass"]
    return {
        "total_events": len(silver_rows),
        "open_risk_events": len(open_rows),
        "critical_open": sum(1 for row in open_rows if row["severity"] == "critical"),
        "high_open": sum(1 for row in open_rows if row["severity"] == "high"),
        "control_count": len(control_rows),
        "control_pass_rate": round(len(passing_controls) / len(control_rows), 4) if control_rows else 1,
        "evidence_coverage": round(len(evidence_rows) / len(silver_rows), 4) if silver_rows else 1,
        "runtime_block_rate": round(len(blocked_runtime) / len(runtime_rows), 4) if runtime_rows else 0,
        "asset_count": len(asset_rows),
        "top_risk_asset": asset_rows[0]["asset_id"] if asset_rows else "",
        "avg_asset_risk": round(sum(float(row["risk_score"]) for row in asset_rows) / len(asset_rows), 2) if asset_rows else 0,
    }


def _build_pipeline_stages(
    raw_rows: list[dict[str, Any]],
    bronze_rows: list[dict[str, Any]],
    silver_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    asset_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mapped_controls = sum(len(row["control_ids"]) for row in silver_rows)
    return [
        {"name": "Ingest", "label": "raw evidence", "count": len(raw_rows)},
        {"name": "Bronze", "label": "hashed replay records", "count": len(bronze_rows)},
        {"name": "Silver", "label": "normalized events", "count": len(silver_rows)},
        {"name": "Map", "label": "control links", "count": mapped_controls},
        {"name": "Gold", "label": "controls + assets", "count": len(control_rows) + len(asset_rows)},
        {"name": "Serve", "label": "mart tables", "count": 4},
    ]


def _build_source_mix(silver_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in silver_rows:
        grouped[row["source"]].append(row)
    rows: list[dict[str, Any]] = []
    for source, items in grouped.items():
        open_count = sum(1 for item in items if item["status"] in {"open", "failed", "blocked", "noncompliant"})
        rows.append(
            {
                "source": source,
                "events": len(items),
                "open": open_count,
                "max_severity_score": max(item["severity_score"] for item in items),
                "route": _source_route(source),
            }
        )
    return sorted(rows, key=lambda item: (-int(item["events"]), item["source"]))


def _build_severity_mix(silver_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["severity"] for row in silver_rows)
    order = ["critical", "high", "medium", "low", "info", "none"]
    return [{"severity": severity, "count": counts[severity]} for severity in order if counts[severity]]


def _build_backend_routes(silver_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    route_counts: dict[str, int] = Counter(_source_route(row["source"]) for row in silver_rows)
    return [
        {
            "backend": "Snowflake",
            "role": "governed evidence",
            "events": route_counts["Snowflake"] + route_counts["dual"],
            "primary_tables": ["RAW_EVENTS", "NORMALIZED_EVENTS", "CONTROL_POSTURE", "ASSET_RISK"],
        },
        {
            "backend": "ClickHouse",
            "role": "telemetry analytics",
            "events": route_counts["ClickHouse"] + route_counts["dual"],
            "primary_tables": ["normalized_events", "control_posture", "asset_risk", "runtime_policy_metrics"],
        },
    ]


def _source_route(source: str) -> str:
    clickhouse_sources = {"runtime-gateway", "siem"}
    snowflake_sources = {"audit-log", "compliance-export", "identity-provider", "model-registry"}
    if source in clickhouse_sources:
        return "ClickHouse"
    if source in snowflake_sources:
        return "Snowflake"
    return "dual"


def _write_mart(
    mart_path: Path,
    silver_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    asset_rows: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    if mart_path.exists():
        mart_path.unlink()
    with sqlite3.connect(mart_path) as conn:
        conn.execute(
            """
            CREATE TABLE normalized_events (
                event_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                event_time TEXT NOT NULL,
                source TEXT NOT NULL,
                event_type TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                asset_owner TEXT NOT NULL,
                environment TEXT NOT NULL,
                severity TEXT NOT NULL,
                severity_score INTEGER NOT NULL,
                status TEXT NOT NULL,
                control_ids_json TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                evidence_collected_at TEXT NOT NULL,
                raw_sha256 TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE control_posture (
                control_id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                title TEXT NOT NULL,
                risk_domain TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                event_count INTEGER NOT NULL,
                open_event_count INTEGER NOT NULL,
                evidence_count INTEGER NOT NULL,
                evidence_coverage REAL NOT NULL,
                latest_event_time TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE asset_risk (
                asset_id TEXT PRIMARY KEY,
                asset_type TEXT NOT NULL,
                asset_owner TEXT NOT NULL,
                environment TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                critical_open INTEGER NOT NULL,
                high_open INTEGER NOT NULL,
                event_count INTEGER NOT NULL,
                latest_event_time TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE TABLE metrics (metric TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany(
            """
            INSERT INTO normalized_events VALUES (
                :event_id, :tenant_id, :event_time, :source, :event_type, :asset_id,
                :asset_type, :asset_owner, :environment, :severity, :severity_score,
                :status, :control_ids_json, :evidence_id, :evidence_ref,
                :evidence_collected_at, :raw_sha256
            )
            """,
            [{**row, "control_ids_json": json.dumps(row["control_ids"])} for row in silver_rows],
        )
        conn.executemany(
            "INSERT INTO control_posture VALUES (:control_id,:framework,:title,:risk_domain,:owner,:status,:risk_score,:event_count,:open_event_count,:evidence_count,:evidence_coverage,:latest_event_time)",
            control_rows,
        )
        conn.executemany(
            "INSERT INTO asset_risk VALUES (:asset_id,:asset_type,:asset_owner,:environment,:risk_score,:critical_open,:high_open,:event_count,:latest_event_time)",
            asset_rows,
        )
        conn.executemany("INSERT INTO metrics VALUES (?, ?)", [(key, str(value)) for key, value in metrics.items()])
        conn.commit()
