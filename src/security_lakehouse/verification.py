"""Evidence integrity verification.

Recomputes a SHA-256 hash over the bronze raw record for an evidence event
and compares it to the stored ``raw_sha256`` value so reviewers (and agents)
can confirm the silver/gold layers have not drifted from the immutable
input.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from security_lakehouse.io import read_jsonl


def _bronze_paths(lake_dir: str | Path) -> list[Path]:
    bronze = Path(lake_dir) / "bronze"
    if not bronze.is_dir():
        return []
    return sorted(bronze.glob("*.jsonl"))


def _silver_record(lake_dir: str | Path, event_id: str) -> dict[str, Any] | None:
    silver = Path(lake_dir) / "silver" / "normalized_events.jsonl"
    if not silver.is_file():
        return None
    for row in read_jsonl(silver):
        if row.get("event_id") == event_id:
            return row
    return None


def _bronze_record(lake_dir: str | Path, event_id: str) -> dict[str, Any] | None:
    for path in _bronze_paths(lake_dir):
        for row in read_jsonl(path):
            raw = row.get("raw") or {}
            if row.get("event_id") == event_id or raw.get("event_id") == event_id:
                return row
    return None


def verify_event(lake_dir: str | Path, event_id: str) -> dict[str, Any]:
    """Verify a silver event's hash against its bronze source.

    Returns a payload of the form::

        {
            "event_id": str,
            "verified": bool,
            "expected_sha256": str | None,    # value stored on the silver row
            "computed_sha256": str | None,    # rehash of bronze raw bytes
            "source_layer": "bronze" | "missing",
            "reason": str | None,
        }
    """
    silver = _silver_record(lake_dir, event_id)
    if silver is None:
        return {
            "event_id": event_id,
            "verified": False,
            "expected_sha256": None,
            "computed_sha256": None,
            "source_layer": "missing",
            "reason": "no silver record found for event_id",
        }
    expected = str(silver.get("raw_sha256") or "")
    bronze = _bronze_record(lake_dir, event_id)
    if bronze is None:
        return {
            "event_id": event_id,
            "verified": False,
            "expected_sha256": expected or None,
            "computed_sha256": None,
            "source_layer": "missing",
            "reason": "bronze source row missing",
        }
    raw_payload = bronze.get("raw") or bronze
    canonical = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"), default=str)
    computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    verified = bool(expected) and computed == expected
    return {
        "event_id": event_id,
        "verified": verified,
        "expected_sha256": expected or None,
        "computed_sha256": computed,
        "source_layer": "bronze",
        "reason": None if verified else "computed hash does not match stored raw_sha256",
    }
