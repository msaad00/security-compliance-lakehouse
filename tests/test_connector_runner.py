"""Connector sync runner tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from security_lakehouse.cli import main
from security_lakehouse.connector_runner import CONNECTOR_RAW_FILE, ConnectorSyncError, run_connector_sync
from security_lakehouse.connector_state import append_config_event, latest_run
from security_lakehouse.io import read_jsonl
from security_lakehouse.validation import validate_raw_events

FIXTURE = Path(__file__).parent / "fixtures" / "github-governance"


def test_connector_sync_requires_enabled_connector(tmp_path: Path) -> None:
    with pytest.raises(ConnectorSyncError, match="not enabled") as exc:
        run_connector_sync(
            tmp_path,
            connector_id="github-security",
            repo="acme/model-service",
            fixture_dir=FIXTURE,
        )
    assert exc.value.run["result"] == "error"
    assert latest_run(tmp_path, "github-security", kind="sync")["result"] == "error"


def test_github_connector_sync_writes_raw_and_materializes_lake(tmp_path: Path) -> None:
    append_config_event(tmp_path, connector_id="github-security", state="enabled", actor="alice")
    result = run_connector_sync(
        tmp_path,
        connector_id="github-security",
        repo="acme/model-service",
        fixture_dir=FIXTURE,
    )
    assert result.result == "ok"
    assert result.evidence_count == 5
    assert result.materialized is True

    raw_rows = read_jsonl(tmp_path / CONNECTOR_RAW_FILE)
    assert validate_raw_events(raw_rows) == []
    assert len(raw_rows) == 5
    assert (tmp_path / "bronze" / "raw_events.jsonl").is_file()
    assert (tmp_path / "silver" / "normalized_events.jsonl").is_file()
    assert (tmp_path / "gold" / "current_posture.json").is_file()

    run = latest_run(tmp_path, "github-security", kind="sync")
    assert run["result"] == "ok"
    assert run["evidence_count"] == 5


def test_connector_sync_upserts_stable_event_ids(tmp_path: Path) -> None:
    append_config_event(tmp_path, connector_id="github-security", state="enabled", actor="alice")
    first = run_connector_sync(tmp_path, connector_id="github-security", repo="acme/model-service", fixture_dir=FIXTURE)
    second = run_connector_sync(
        tmp_path,
        connector_id="github-security",
        repo="acme/model-service",
        fixture_dir=FIXTURE,
        materialize=False,
    )
    assert first.evidence_count == second.evidence_count == 5
    assert len(read_jsonl(tmp_path / CONNECTOR_RAW_FILE)) == 5


def test_connector_sync_cli_runs_fixture_connector(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    configure = main(
        [
            "connectors",
            "configure",
            "--lake",
            str(tmp_path),
            "--connector-id",
            "github-security",
            "--state",
            "enabled",
        ]
    )
    assert configure == 0
    capsys.readouterr()
    code = main(
        [
            "connectors",
            "sync",
            "--lake",
            str(tmp_path),
            "--connector-id",
            "github-security",
            "--repo",
            "acme/model-service",
            "--fixture-dir",
            str(FIXTURE),
            "--no-materialize",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["connector_id"] == "github-security"
    assert payload["evidence_count"] == 5
    assert payload["materialized"] is False
    assert len(read_jsonl(tmp_path / CONNECTOR_RAW_FILE)) == 5


def test_connector_configure_cli_persists_schedule_options(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(
        [
            "connectors",
            "configure",
            "--lake",
            str(tmp_path),
            "--connector-id",
            "github-security",
            "--state",
            "enabled",
            "--sync-schedule",
            "every 15m",
            "--repo",
            "acme/model-service",
            "--fixture-dir",
            str(FIXTURE),
            "--token-env",
            "GH_READ_TOKEN",
            "--no-materialize",
        ]
    )

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    options = payload["event"]["options"]
    assert options == {
        "fixture_dir": str(FIXTURE),
        "materialize": False,
        "repo": "acme/model-service",
        "sync_schedule": "every 15m",
        "token_env": "GH_READ_TOKEN",
    }
