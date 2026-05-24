"""Reviewed control_id ↔ source_article mappings.

Replaces the heuristic crosswalk with auditor-reviewed mappings. Each
mapping points from a local control_id to one or more articles in the
framework's official source, with reviewer attestation and rationale.

Loaded from ``mappings/control_articles.json``; readonly + validated.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAPPINGS = ROOT / "mappings" / "control_articles.json"


def load_control_article_mappings(
    path: str | Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Return a {control_id: mapping_record} dict."""
    payload = json.loads(Path(path or DEFAULT_MAPPINGS).read_text(encoding="utf-8"))
    mappings = payload.get("mappings")
    if not isinstance(mappings, list):
        raise ValueError("control article mappings must contain a `mappings` list")
    out: dict[str, dict[str, Any]] = {}
    for mapping in mappings:
        cid = str(mapping.get("control_id") or "")
        if not cid:
            continue
        out[cid] = mapping
    return out


def validate_control_article_mappings(
    path: str | Path | None = None,
) -> list[str]:
    """Return errors for missing/invalid mapping fields."""
    errors: list[str] = []
    mappings = load_control_article_mappings(path)
    for cid, mapping in mappings.items():
        if not mapping.get("framework_id"):
            errors.append(f"mapping {cid} missing framework_id")
        articles = mapping.get("articles") or []
        if not articles:
            errors.append(f"mapping {cid} has no articles")
        for article in articles:
            for required in ("article_id", "title", "official_source_url", "reviewed_by", "reviewed_at", "rationale"):
                if not str(article.get(required) or "").strip():
                    errors.append(f"mapping {cid} article missing {required}")
    return errors


def build_reviewed_crosswalk(
    mappings_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compute a reviewed framework × framework crosswalk via shared articles.

    The matrix cells list:
      * ``shared_articles``: same article_id appearing in both frameworks'
        mapping tables (rare across frameworks, but supported).
      * ``shared_controls``: same control_id touching both frameworks
        (this matters if a control maps into multiple framework versions).
      * ``mappings_per_framework`` totals on the row header.
    """
    mappings = load_control_article_mappings(mappings_path)
    by_framework: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for cid, mapping in mappings.items():
        framework_id = str(mapping.get("framework_id") or "")
        if framework_id:
            by_framework[framework_id][cid] = mapping

    frameworks = sorted(by_framework)
    matrix: list[dict[str, Any]] = []
    for left in frameworks:
        left_articles = {
            article["article_id"]
            for mapping in by_framework[left].values()
            for article in (mapping.get("articles") or [])
        }
        left_controls = set(by_framework[left])
        row: dict[str, Any] = {
            "framework_id": left,
            "mapping_count": len(by_framework[left]),
            "article_count": len(left_articles),
            "cells": [],
        }
        for right in frameworks:
            right_articles = {
                article["article_id"]
                for mapping in by_framework[right].values()
                for article in (mapping.get("articles") or [])
            }
            right_controls = set(by_framework[right])
            row["cells"].append(
                {
                    "framework_id": right,
                    "is_self": left == right,
                    "shared_articles": sorted(left_articles & right_articles),
                    "shared_controls": sorted(left_controls & right_controls),
                }
            )
        matrix.append(row)
    return {"frameworks": frameworks, "matrix": matrix}
