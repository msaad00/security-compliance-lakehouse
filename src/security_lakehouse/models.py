"""Canonical event and analytics models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SEVERITY_SCORE = {
    "critical": 100,
    "high": 80,
    "medium": 50,
    "low": 20,
    "info": 5,
    "none": 0,
}


@dataclass(frozen=True)
class RawSecurityEvent:
    event_id: str
    tenant_id: str
    event_time: str
    source: str
    event_type: str
    entity: dict[str, Any]
    severity: str = "info"
    status: str = "observed"
    controls: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SilverEvent:
    event_id: str
    tenant_id: str
    event_time: str
    source: str
    event_type: str
    asset_id: str
    asset_type: str
    asset_owner: str
    environment: str
    severity: str
    severity_score: int
    status: str
    control_ids: list[str]
    evidence_id: str
    evidence_ref: str
    evidence_collected_at: str
    raw_sha256: str


@dataclass(frozen=True)
class PipelineResult:
    output_dir: str
    raw_count: int
    silver_count: int
    control_count: int
    asset_count: int
    mart_path: str
    metrics_path: str
    dashboard_data_path: str


def parse_event_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
