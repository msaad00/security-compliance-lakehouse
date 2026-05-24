"""Framework + control catalog provenance.

Frameworks must be versioned, live, and trusted — not hand-typed lookup
tables. Each framework declares:
  * ``official_source_url``     (e.g. eur-lex.europa.eu/eli/reg/2016/679)
  * ``official_source_name``
  * ``version`` + ``effective_date`` + ``superseded_by``
  * ``source_sha256`` + ``pulled_at`` populated by the sync job
  * ``sync_cadence_days`` (how often the source is expected to be re-checked)

This module joins the registry with the control catalog and computes a
freshness state the UI can render so reviewers can see at a glance:

    "GDPR · pulled 3 days ago · sha256 a1b2c3… · 86 controls mapped · fresh"

The actual source-sync job is intentionally separate (a GitHub Action or
cron) so this module remains pure and deterministic.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from security_lakehouse.catalog import (
    DEFAULT_CONTROL_CATALOG,
    DEFAULT_FRAMEWORK_REGISTRY,
    load_control_catalog,
    load_framework_registry,
)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def _freshness_state(pulled_at: datetime | None, cadence_days: int, now: datetime) -> str:
    if pulled_at is None:
        return "never_pulled"
    age = now - pulled_at
    sla = timedelta(days=cadence_days)
    if age <= sla:
        return "fresh"
    if age <= sla * 2:
        return "stale"
    return "expired"


def build_framework_view(
    registry_path: str | Path | None = None,
    controls_path: str | Path | None = None,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return the framework registry joined with control counts + freshness."""
    frameworks = load_framework_registry(registry_path or DEFAULT_FRAMEWORK_REGISTRY)
    controls = load_control_catalog(controls_path or DEFAULT_CONTROL_CATALOG)
    now_utc = (now or datetime.now(UTC)).astimezone(UTC)

    controls_by_framework: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for control in controls.values():
        framework_id = str(control.get("framework_id") or "")
        if framework_id:
            controls_by_framework[framework_id].append(control)

    out: list[dict[str, Any]] = []
    for framework in frameworks.values():
        framework_id = str(framework.get("framework_id") or "")
        cadence = int(framework.get("sync_cadence_days") or 90)
        pulled_at = _parse_iso(framework.get("pulled_at"))
        freshness = _freshness_state(pulled_at, cadence, now_utc)
        controls = controls_by_framework.get(framework_id, [])
        mapped = sum(1 for c in controls if c.get("implementation_status", "").startswith("implemented"))
        out.append(
            {
                **framework,
                "control_count": len(controls),
                "implemented_control_count": mapped,
                "mapping_coverage_pct": (round(mapped / len(controls) * 100, 1) if controls else 0.0),
                "freshness_state": freshness,
                "pulled_age_days": ((now_utc - pulled_at).days if pulled_at is not None else None),
                "next_pull_due": (
                    (pulled_at + timedelta(days=cadence)).isoformat().replace("+00:00", "Z")
                    if pulled_at is not None
                    else None
                ),
            }
        )
    out.sort(key=lambda f: f.get("framework_id", ""))
    return out
