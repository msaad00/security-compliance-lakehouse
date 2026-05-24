from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8799"


def main() -> int:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "security_lakehouse.cli",
            "serve",
            "--lake",
            str(ROOT / "build" / "lakehouse"),
            "--port",
            "8799",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_health()
        _assert_get("/api/posture/current", "assessment_type")
        _assert_get("/api/control-tests", "control_tests")
        _assert_get("/api/evidence", "evidence")
        _assert_get("/api/assets", "assets")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    return 0


def _wait_for_health() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            payload = _get_json("/api/healthz")
            if payload.get("ok") is True or payload.get("status") == "ok":
                return
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.2)
    raise RuntimeError("server did not become healthy")


def _assert_get(path: str, key: str) -> None:
    payload = _get_json(path)
    if key not in payload:
        raise AssertionError(f"{path} missing {key}")


def _get_json(path: str) -> dict[str, object]:
    with urllib.request.urlopen(BASE_URL + path, timeout=2) as response:
        if response.status != 200:
            raise AssertionError(f"{path} returned HTTP {response.status}")
        value = json.loads(response.read().decode("utf-8"))
        if not isinstance(value, dict):
            raise AssertionError(f"{path} returned non-object JSON")
        return value


if __name__ == "__main__":
    raise SystemExit(main())
