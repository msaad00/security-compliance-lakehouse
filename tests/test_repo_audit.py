"""Public repository audit tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from security_lakehouse.cli import main
from security_lakehouse.io import read_jsonl
from security_lakehouse.repo_audit import audit_public_repo, parse_repo_spec
from security_lakehouse.validation import validate_raw_events


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "github-fixture"
    _write_json(
        fixture / "repo.json",
        {
            "archived": False,
            "default_branch": "main",
            "fork": False,
            "full_name": "acme/agent-api",
            "language": "TypeScript",
            "license": {"spdx_id": "Apache-2.0"},
            "name": "agent-api",
            "owner": {"login": "acme"},
            "private": False,
            "pushed_at": "2026-05-20T15:00:00Z",
            "topics": ["ai", "agents", "security"],
            "visibility": "public",
        },
    )
    _write_json(fixture / "languages.json", {"Python": 1200, "TypeScript": 8800})
    paths = [
        ".github/CODEOWNERS",
        ".github/workflows/ci.yml",
        "SECURITY.md",
        "app/package.json",
        "deploy/helm/values.yaml",
        "infra/main.tf",
        "Dockerfile",
        "models/model-card.md",
        "src/index.ts",
    ]
    _write_json(fixture / "tree.json", {"tree": [{"path": path, "type": "blob"} for path in paths]})
    (fixture / "files" / ".github").mkdir(parents=True)
    (fixture / "files" / ".github" / "CODEOWNERS").write_text("* @acme/security\n", encoding="utf-8")
    (fixture / "files" / "SECURITY.md").write_text("Report issues. token=super-secret-value\n", encoding="utf-8")
    (fixture / "files" / "app").mkdir(parents=True)
    (fixture / "files" / "app" / "package.json").write_text('{"dependencies":{"next":"15.0.0"}}\n', encoding="utf-8")
    return fixture


def test_parse_repo_spec_accepts_url_and_slug() -> None:
    assert parse_repo_spec("https://github.com/acme/agent-api").slug == "acme/agent-api"
    assert parse_repo_spec("acme/agent-api.git").slug == "acme/agent-api"


def test_audit_public_repo_fixture_emits_valid_raw_events(tmp_path: Path) -> None:
    rows = audit_public_repo(
        "acme/agent-api",
        fixture_dir=_fixture(tmp_path),
        collected_at=datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
    )
    assert validate_raw_events(rows) == []
    by_type = {row["event_type"]: row for row in rows}
    assert "repository.metadata" in by_type
    assert "repository.code_graph" in by_type
    assert "repository.codeowners" in by_type
    assert "repository.security_policy" in by_type
    assert "repository.authenticated_signal_gap" in by_type
    assert by_type["repository.codeowners"]["controls"] == ["SOC2-CC6.1", "ISO27001-A.5.15"]
    assert by_type["repository.authenticated_signal_gap"]["status"] == "requires_authenticated_connector"
    assert by_type["repository.code_graph"]["attributes"]["counts"]["signals"] >= 6


def test_audit_public_repo_redacts_secret_like_sample_text(tmp_path: Path) -> None:
    rows = audit_public_repo(
        "https://github.com/acme/agent-api",
        fixture_dir=_fixture(tmp_path),
        collected_at=datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
    )
    policy = next(row for row in rows if row["event_type"] == "repository.security_policy")
    assert "super-secret-value" not in policy["attributes"]["sample_excerpt"]
    assert "[redacted]" in policy["attributes"]["sample_excerpt"]


def test_audit_public_repo_event_ids_are_stable(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    first = audit_public_repo("acme/agent-api", fixture_dir=fixture, collected_at=datetime(2026, 5, 24, tzinfo=UTC))
    second = audit_public_repo("acme/agent-api", fixture_dir=fixture, collected_at=datetime(2026, 5, 25, tzinfo=UTC))
    assert [row["event_id"] for row in first] == [row["event_id"] for row in second]
    assert [row["evidence"]["evidence_id"] for row in first] == [row["evidence"]["evidence_id"] for row in second]


def test_repo_audit_cli_writes_jsonl(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "repo-audit.jsonl"
    code = main(["repo", "audit", "acme/agent-api", "--fixture-dir", str(_fixture(tmp_path)), "--out", str(out)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 5
    assert out.is_file()
    rows = read_jsonl(out)
    assert validate_raw_events(rows) == []
