from __future__ import annotations

import json

from security_lakehouse.framework_coverage import (
    build_framework_coverage,
    framework_coverage_summary,
    render_framework_coverage_markdown,
)
from security_lakehouse.cli import main


def test_framework_coverage_ledger_counts_seeded_mappings(capsys) -> None:
    rows = build_framework_coverage()
    summary = framework_coverage_summary(rows)

    assert summary["framework_count"] == 8
    assert summary["seeded_control_count"] == 34
    assert summary["reviewed_mapping_count"] == 34
    assert summary["missing_mapping_count"] == 0
    assert summary["seeded_mapping_coverage_pct"] == 100.0
    assert summary["official_logo_count"] == 0
    assert summary["certification_seal_count"] == 0
    assert all(row["asset_policy"].startswith("neutral label") for row in rows)

    assert main(["frameworks", "coverage"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["summary"] == summary


def test_framework_coverage_markdown_is_source_linked_not_logo_based() -> None:
    markdown = render_framework_coverage_markdown(build_framework_coverage())

    assert "Seeded mapping coverage: 100.0%" in markdown
    assert "Official source" in markdown
    assert "official logo" not in markdown.lower()
    assert "certification seal" not in markdown.lower()
    assert "EUR-Lex - Regulation (EU) 2016/679" in markdown
