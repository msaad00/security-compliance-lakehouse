"""Violation triage persistence.

Stores the human/agent workflow on top of the immutable violation stream.
Records are append-only JSONL in ``gold/violation_tracking.jsonl`` so the
underlying assessment posture stays deterministic — tracking augments, never
mutates, the source-of-truth evidence facts.

Schema (per record):
    {
        "tracking_id": str  (sha256(violation_id|ts|nonce)[:16]),
        "violation_id": str,
        "actor": str,
        "state": "open" | "triaged" | "in_progress" | "resolved" | "dismissed",
        "assignee": str | None,
        "due_at": str | None  (ISO 8601),
        "note": str | None,
        "occurred_at": str  (ISO 8601 UTC),
    }
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ALLOWED_STATES = {"open", "triaged", "in_progress", "resolved", "dismissed"}


def tracking_path(lake_dir: str | Path) -> Path:
    """Return the JSONL file backing the triage log."""
    return Path(lake_dir) / "gold" / "violation_tracking.jsonl"


def append_event(
    lake_dir: str | Path,
    *,
    violation_id: str,
    actor: str,
    state: str,
    assignee: str | None = None,
    due_at: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Append a triage event for ``violation_id`` and return the record."""
    if state not in ALLOWED_STATES:
        raise ValueError(f"unknown state {state!r}; allowed: {sorted(ALLOWED_STATES)}")
    if not violation_id:
        raise ValueError("violation_id is required")
    occurred_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    nonce = hashlib.sha256(f"{violation_id}|{occurred_at}".encode()).hexdigest()[:16]
    record: dict[str, Any] = {
        "tracking_id": nonce,
        "violation_id": violation_id,
        "actor": actor or "anonymous",
        "state": state,
        "assignee": assignee,
        "due_at": due_at,
        "note": note,
        "occurred_at": occurred_at,
    }
    path = tracking_path(lake_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    return record


def list_events(lake_dir: str | Path, *, violation_id: str | None = None) -> list[dict[str, Any]]:
    """Return all triage events, optionally filtered by ``violation_id``."""
    path = tracking_path(lake_dir)
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if violation_id and payload.get("violation_id") != violation_id:
                continue
            records.append(payload)
    return records


def latest_state(lake_dir: str | Path, *, violation_id: str) -> dict[str, Any] | None:
    """Return the most recent triage event for ``violation_id`` or None."""
    events = list_events(lake_dir, violation_id=violation_id)
    if not events:
        return None
    return max(events, key=lambda r: str(r.get("occurred_at") or ""))
