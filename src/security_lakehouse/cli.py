"""Command line interface for TrustOps Security Data Lake."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from security_lakehouse.dashboard import render_dashboard
from security_lakehouse.io import read_jsonl
from security_lakehouse.pipeline import run_pipeline
from security_lakehouse.validation import validate_raw_events


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="security-lakehouse")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate raw JSONL evidence")
    validate.add_argument("--raw", required=True, help="raw security events JSONL")
    validate.set_defaults(func=_validate)

    pipeline = sub.add_parser("pipeline", help="pipeline commands")
    pipeline_sub = pipeline.add_subparsers(dest="pipeline_command", required=True)
    run = pipeline_sub.add_parser("run", help="run bronze/silver/gold pipeline")
    run.add_argument("--raw", required=True, help="raw security events JSONL")
    run.add_argument("--out", required=True, help="security data lake output directory")
    run.add_argument("--mapping", default=None, help="optional control mapping JSON")
    run.set_defaults(func=_run_pipeline)

    connectors = sub.add_parser("connectors", help="connector catalog commands")
    connectors_sub = connectors.add_subparsers(dest="connectors_command", required=True)
    connectors_validate = connectors_sub.add_parser("validate", help="validate connector access contracts")
    connectors_validate.add_argument("--catalog", default=None, help="optional connector catalog JSON")
    connectors_validate.set_defaults(func=_connectors_validate)
    connectors_list = connectors_sub.add_parser("list", help="list connector access contracts")
    connectors_list.add_argument("--catalog", default=None, help="optional connector catalog JSON")
    connectors_list.set_defaults(func=_connectors_list)

    dashboard = sub.add_parser("dashboard", help="render static dashboard HTML")
    dashboard.add_argument("--lake", required=True, help="security data lake output directory")
    dashboard.add_argument("--out", required=True, help="dashboard HTML output path")
    dashboard.set_defaults(func=_dashboard)

    query = sub.add_parser("query", help="run read-only SQL against the analytics mart")
    query.add_argument("--lake", required=True, help="security data lake output directory")
    query.add_argument("--engine", choices=["sqlite", "duckdb"], default="sqlite", help="local mart engine")
    query.add_argument("sql", help="SQL SELECT statement")
    query.set_defaults(func=_query)

    serve = sub.add_parser("serve", help="serve the interactive console and assessment API")
    serve.add_argument("--lake", required=True, help="security data lake output directory")
    serve.add_argument("--host", default="127.0.0.1", help="bind host")
    serve.add_argument("--port", type=int, default=8787, help="bind port")
    serve.set_defaults(func=_serve)

    assessment = sub.add_parser("assessment", help="continuous compliance assessment commands")
    assessment_sub = assessment.add_subparsers(dest="assessment_command", required=True)
    status = assessment_sub.add_parser("status", help="print current posture")
    status.add_argument("--lake", required=True, help="security data lake output directory")
    status.add_argument("--freshness-days", type=int, default=7, help="evidence freshness window")
    status.set_defaults(func=_assessment_status)
    snapshot = assessment_sub.add_parser("snapshot", help="write point-in-time assessment snapshot")
    snapshot.add_argument("--lake", required=True, help="security data lake output directory")
    snapshot.add_argument("--out", default=None, help="snapshot output path")
    snapshot.add_argument("--freshness-days", type=int, default=7, help="evidence freshness window")
    snapshot.add_argument("--reason", default="manual", help="snapshot reason")
    snapshot.set_defaults(func=_assessment_snapshot)
    violations = assessment_sub.add_parser("violations", help="list open framework/control violations")
    violations.add_argument("--lake", required=True, help="security data lake output directory")
    violations.add_argument("--framework", default=None, help="optional framework filter")
    violations.set_defaults(func=_assessment_violations)
    return parser


def _validate(args: argparse.Namespace) -> int:
    rows = read_jsonl(args.raw)
    errors = validate_raw_events(rows)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"valid raw evidence: {len(rows)} records")
    return 0


def _run_pipeline(args: argparse.Namespace) -> int:
    result = run_pipeline(args.raw, args.out, mapping_path=args.mapping)
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


def _connectors_validate(args: argparse.Namespace) -> int:
    from security_lakehouse.connectors import validate_connector_catalog

    errors = validate_connector_catalog(args.catalog)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("valid connector catalog")
    return 0


def _connectors_list(args: argparse.Namespace) -> int:
    from security_lakehouse.connectors import load_connector_catalog

    connectors = load_connector_catalog(args.catalog)
    rows = [
        {
            "connector_id": connector["connector_id"],
            "name": connector["name"],
            "collection_mode": connector["collection_mode"],
            "access_boundary": connector["access_boundary"],
            "default_route": connector["default_route"],
            "freshness_slo_minutes": connector["freshness_slo_minutes"],
        }
        for connector in connectors.values()
    ]
    print(json.dumps({"connectors": rows, "count": len(rows)}, indent=2, sort_keys=True))
    return 0


def _dashboard(args: argparse.Namespace) -> int:
    output = render_dashboard(args.lake, args.out)
    print(f"wrote dashboard: {output}")
    return 0


def _query(args: argparse.Namespace) -> int:
    sql = args.sql.strip()
    if not sql.lower().startswith("select"):
        raise ValueError("query command only allows SELECT statements")
    if args.engine == "duckdb":
        rows = _query_duckdb(Path(args.lake) / "mart" / "security_data_lake.duckdb", sql)
        print(json.dumps({"count": len(rows), "engine": args.engine, "rows": rows}, indent=2, sort_keys=True, default=str))
        return 0

    mart = Path(args.lake) / "mart" / "security_lakehouse.sqlite"
    with sqlite3.connect(mart) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(sql).fetchall()]
    print(json.dumps({"count": len(rows), "engine": args.engine, "rows": rows}, indent=2, sort_keys=True))
    return 0


def _query_duckdb(mart: Path, sql: str) -> list[dict]:
    if not mart.exists():
        raise ValueError("DuckDB mart not found. Install with `pip install -e '.[analytics]'` and rerun the pipeline.")
    try:
        import duckdb  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ValueError("DuckDB is not installed. Install with `pip install -e '.[analytics]'`.") from exc

    with duckdb.connect(str(mart), read_only=True) as conn:
        cursor = conn.execute(sql)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _serve(args: argparse.Namespace) -> int:
    from security_lakehouse.server import serve

    print(f"serving TrustOps console: http://{args.host}:{args.port}/")
    serve(args.lake, host=args.host, port=args.port)
    return 0


def _assessment_status(args: argparse.Namespace) -> int:
    from security_lakehouse.assessment import build_current_posture

    posture = build_current_posture(args.lake, freshness_days=args.freshness_days)
    print(json.dumps(posture, indent=2, sort_keys=True))
    return 0


def _assessment_snapshot(args: argparse.Namespace) -> int:
    from security_lakehouse.assessment import write_assessment_snapshot

    path = write_assessment_snapshot(args.lake, output=args.out, freshness_days=args.freshness_days, reason=args.reason)
    print(f"wrote assessment snapshot: {path}")
    return 0


def _assessment_violations(args: argparse.Namespace) -> int:
    from security_lakehouse.assessment import build_current_posture

    posture = build_current_posture(args.lake)
    framework_controls = {
        control["control_id"]: control["framework"]
        for control in read_jsonl(Path(args.lake) / "gold" / "control_posture.jsonl")
    }
    rows = [
        violation
        for violation in posture["violations"]
        if args.framework is None or framework_controls.get(violation["control_id"]) == args.framework
    ]
    print(json.dumps({"count": len(rows), "violations": rows}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
