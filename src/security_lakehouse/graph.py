"""Build a framework → control → evidence → asset graph from the lake.

The graph is the single source of truth the React /graph canvas renders.
Every node carries its kind so the canvas can shape and colour them, and
every edge carries the relationship name so the canvas can filter.

Node kinds:
    framework, control, evidence_type, asset

Edge kinds:
    framework_has_control, control_requires_evidence, evidence_covers_asset
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from security_lakehouse.catalog import load_control_catalog, load_framework_registry
from security_lakehouse.io import read_jsonl


def _gold_asset_rows(lake_dir: Path) -> list[dict[str, Any]]:
    path = lake_dir / "gold" / "asset_risk.jsonl"
    return read_jsonl(path) if path.is_file() else []


def _silver_event_rows(lake_dir: Path) -> list[dict[str, Any]]:
    path = lake_dir / "silver" / "normalized_events.jsonl"
    return read_jsonl(path) if path.is_file() else []


def build_compliance_graph(lake_dir: str | Path) -> dict[str, Any]:
    """Return a serialisable graph spanning frameworks → controls → evidence → assets."""
    lake = Path(lake_dir)
    frameworks = load_framework_registry()
    controls = load_control_catalog()
    events = _silver_event_rows(lake)
    assets = _gold_asset_rows(lake)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    # Framework nodes
    for framework_id, framework in frameworks.items():
        nodes.append(
            {
                "id": f"framework:{framework_id}",
                "kind": "framework",
                "label": framework.get("name", framework_id),
                "subtitle": framework.get("version"),
                "framework_id": framework_id,
            }
        )

    # Control nodes + framework→control edges
    for control_id, control in controls.items():
        framework_id = control.get("framework_id") or ""
        nodes.append(
            {
                "id": f"control:{control_id}",
                "kind": "control",
                "label": control_id,
                "subtitle": control.get("title"),
                "framework_id": framework_id,
                "owner": control.get("owner"),
            }
        )
        if framework_id:
            edges.append(
                {
                    "id": f"e:f{framework_id}-c{control_id}",
                    "source": f"framework:{framework_id}",
                    "target": f"control:{control_id}",
                    "kind": "framework_has_control",
                }
            )

    # Evidence-type nodes + control→evidence edges (deduped by event_type)
    evidence_count_by_type: Counter[str] = Counter()
    type_to_controls: dict[str, set[str]] = {}
    type_to_assets: dict[str, set[str]] = {}
    for event in events:
        event_type = str(event.get("event_type") or "unknown")
        evidence_count_by_type[event_type] += 1
        controls_for = type_to_controls.setdefault(event_type, set())
        assets_for = type_to_assets.setdefault(event_type, set())
        for cid in event.get("control_ids") or []:
            controls_for.add(str(cid))
        if asset_id := event.get("asset_id"):
            assets_for.add(str(asset_id))

    for event_type, count in evidence_count_by_type.items():
        node_id = f"evidence:{event_type}"
        nodes.append(
            {
                "id": node_id,
                "kind": "evidence_type",
                "label": event_type,
                "subtitle": f"{count} records",
                "event_count": count,
            }
        )
        for cid in type_to_controls.get(event_type, set()):
            if f"control:{cid}" not in {n["id"] for n in nodes}:
                continue
            edges.append(
                {
                    "id": f"e:c{cid}-t{event_type}",
                    "source": f"control:{cid}",
                    "target": node_id,
                    "kind": "control_requires_evidence",
                }
            )

    # Asset nodes + evidence→asset edges
    asset_rows = {str(row.get("asset_id") or ""): row for row in assets}
    seen_assets: set[str] = set()
    for event_type, asset_ids in type_to_assets.items():
        for asset_id in asset_ids:
            if not asset_id:
                continue
            if asset_id not in seen_assets:
                seen_assets.add(asset_id)
                row = asset_rows.get(asset_id, {})
                nodes.append(
                    {
                        "id": f"asset:{asset_id}",
                        "kind": "asset",
                        "label": asset_id,
                        "subtitle": row.get("asset_type") or "asset",
                        "owner": row.get("asset_owner"),
                        "environment": row.get("environment"),
                        "risk_score": row.get("risk_score"),
                    }
                )
            edges.append(
                {
                    "id": f"e:t{event_type}-a{asset_id}",
                    "source": f"evidence:{event_type}",
                    "target": f"asset:{asset_id}",
                    "kind": "evidence_covers_asset",
                }
            )

    counts = {
        "framework": sum(1 for n in nodes if n["kind"] == "framework"),
        "control": sum(1 for n in nodes if n["kind"] == "control"),
        "evidence_type": sum(1 for n in nodes if n["kind"] == "evidence_type"),
        "asset": sum(1 for n in nodes if n["kind"] == "asset"),
    }
    return {"nodes": nodes, "edges": edges, "counts": counts}


def build_framework_crosswalk(controls_path: str | Path | None = None) -> dict[str, Any]:
    """Compute a framework × framework matrix of shared owners and shared risk domains.

    The catalog ships local control IDs only (no licensed text reproduced), so
    the crosswalk currently joins on ``risk_domain`` + ``owner`` heuristics —
    the same dimensions an auditor uses to point at "this maps to that."
    PR 8 swaps this for reviewed control_id↔article mappings once the
    framework sync job lands.
    """
    controls = load_control_catalog(controls_path)
    by_framework: dict[str, list[dict[str, Any]]] = {}
    for control in controls.values():
        framework_id = str(control.get("framework_id") or "")
        by_framework.setdefault(framework_id, []).append(control)

    framework_ids = sorted(by_framework)
    matrix: list[dict[str, Any]] = []
    for left in framework_ids:
        row: dict[str, Any] = {"framework_id": left, "cells": []}
        for right in framework_ids:
            shared_domains = sorted(
                {c.get("risk_domain") for c in by_framework[left] if c.get("risk_domain")}
                & {c.get("risk_domain") for c in by_framework[right] if c.get("risk_domain")}
            )
            shared_owners = sorted(
                {c.get("owner") for c in by_framework[left] if c.get("owner")}
                & {c.get("owner") for c in by_framework[right] if c.get("owner")}
            )
            row["cells"].append(
                {
                    "framework_id": right,
                    "shared_risk_domains": shared_domains,
                    "shared_owners": shared_owners,
                    "is_self": left == right,
                }
            )
        matrix.append(row)
    return {"frameworks": framework_ids, "matrix": matrix}
