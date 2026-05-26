from __future__ import annotations

from pathlib import Path


def test_source_tree_has_no_editor_copy_artifacts() -> None:
    root = Path("src/security_lakehouse")
    offenders = [
        str(path)
        for path in root.rglob("*")
        if path.is_file()
        and (
            " copy" in path.name or path.suffix in {".bak", ".orig"} or any(f" {i}" in path.stem for i in range(2, 10))
        )
        and "web/dist" not in path.as_posix()
    ]
    assert offenders == []
