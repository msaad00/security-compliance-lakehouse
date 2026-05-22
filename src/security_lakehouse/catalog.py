"""Framework registry and control catalog validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRAMEWORK_REGISTRY = ROOT / "frameworks" / "registry.json"
DEFAULT_CONTROL_CATALOG = ROOT / "controls" / "catalog.json"


def load_framework_registry(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(path or DEFAULT_FRAMEWORK_REGISTRY)
    frameworks = payload.get("frameworks")
    if not isinstance(frameworks, list):
        raise ValueError("framework registry must contain a frameworks list")
    return {str(item["framework_id"]): item for item in frameworks}


def load_control_catalog(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    payload = _read_json(path or DEFAULT_CONTROL_CATALOG)
    controls = payload.get("controls")
    if not isinstance(controls, list):
        raise ValueError("control catalog must contain a controls list")
    return {str(item["control_id"]): item for item in controls}


def validate_catalog(
    *,
    registry_path: str | Path | None = None,
    catalog_path: str | Path | None = None,
) -> list[str]:
    errors: list[str] = []
    registry = load_framework_registry(registry_path)
    catalog = load_control_catalog(catalog_path)
    for framework_id, framework in registry.items():
        for required in ("name", "version", "official_source_url", "implementation_status"):
            if not str(framework.get(required, "")).strip():
                errors.append(f"framework {framework_id} missing {required}")
    for control_id, control in catalog.items():
        framework_id = str(control.get("framework_id") or "")
        if framework_id not in registry:
            errors.append(f"control {control_id} references unknown framework_id {framework_id}")
        for required in (
            "framework",
            "title",
            "risk_domain",
            "owner",
            "evidence_requirement",
            "evaluation_rule",
            "frequency",
            "implementation_status",
            "official_source_ref",
        ):
            if not str(control.get(required, "")).strip():
                errors.append(f"control {control_id} missing {required}")
        if control.get("official_source_ref") != framework_id:
            errors.append(f"control {control_id} official_source_ref must match framework_id")
    return errors


def validate_evidence_controls(control_ids: set[str], catalog_path: str | Path | None = None) -> list[str]:
    catalog = load_control_catalog(catalog_path)
    return [f"evidence references unmapped control {control_id}" for control_id in sorted(control_ids - set(catalog))]


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload
