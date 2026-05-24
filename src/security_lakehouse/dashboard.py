"""Single-file React workbench export.

`security-lakehouse dashboard` produces a self-contained HTML for offline
distribution (auditors, evidence-room handoffs, archive snapshots). The file
is built from the Next.js static export packaged in
``security_lakehouse/web/dist/`` by inlining every referenced JS/CSS asset
into ``dist/dashboard/index.html`` and injecting the current assessment
payload into ``<script id="app-data">``.

If the React bundle has not been built locally yet (clean dev checkout), the
``serve`` command still works because it can render dynamically from the API;
the offline ``dashboard render`` falls back to a minimal evidence-bundle HTML
that contains the same data + a pointer to ``security-lakehouse serve``.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from security_lakehouse.assessment import build_current_posture
from security_lakehouse.io import read_json, read_jsonl
from security_lakehouse.web import web_dist_dir, web_dist_index

# Captures src/href values for /console/_next/static/... and other dist assets.
_HREF_RE = re.compile(r'(?P<attr>\b(?:src|href))="(?P<url>/console/[^"]+)"')
_INLINE_DATA_RE = re.compile(r'<script\s+id="app-data"[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)


def render_dashboard(lake_dir: str | Path, out_path: str | Path) -> Path:
    """Write a self-contained dashboard HTML and return its path."""
    lake = Path(lake_dir)
    app_data = _load_app_data(lake)
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if web_dist_index() is not None:
        output.write_text(_inline_react_dashboard(app_data), encoding="utf-8")
    else:
        output.write_text(_fallback_html(app_data), encoding="utf-8")
    return output


def _load_app_data(lake: Path) -> dict[str, Any]:
    dashboard = read_json(lake / "gold" / "dashboard_data.json")
    posture_path = lake / "gold" / "current_posture.json"
    posture = read_json(posture_path) if posture_path.exists() else build_current_posture(lake)
    return {
        "generated_at": dashboard.get("generated_at"),
        "metrics": dashboard.get("metrics", {}),
        "controls": dashboard.get("control_posture", []),
        "control_tests": dashboard.get("control_tests", []),
        "assets": dashboard.get("asset_risk", []),
        "events": read_jsonl(lake / "silver" / "normalized_events.jsonl"),
        "posture": posture,
        "sources": dashboard.get("source_mix", []),
        "routes": dashboard.get("backend_routes", []),
        "stages": dashboard.get("pipeline_stages", []),
    }


def _inline_react_dashboard(app_data: dict[str, Any]) -> str:
    """Bundle dist/dashboard/index.html into one self-contained file."""
    dist = web_dist_dir()
    source = dist / "dashboard" / "index.html"
    if not source.is_file():
        # Bundled but the dashboard route is missing (corrupt build); fall back.
        return _fallback_html(app_data)
    html_text = source.read_text(encoding="utf-8")
    html_text = _inline_assets(html_text, dist)
    payload = html.escape(json.dumps(app_data, sort_keys=True, default=str), quote=False)
    replacement = f'<script id="app-data" type="application/json">{payload}</script>'
    if _INLINE_DATA_RE.search(html_text):
        html_text = _INLINE_DATA_RE.sub(replacement, html_text)
    else:
        html_text = html_text.replace("</body>", f"{replacement}</body>")
    return html_text


def _inline_assets(html_text: str, dist: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        attr = match.group("attr")
        url = match.group("url")
        rel = url[len("/console/") :].split("?", 1)[0].split("#", 1)[0]
        target = (dist / rel).resolve()
        try:
            target.relative_to(dist.resolve())
        except ValueError:
            return match.group(0)
        if not target.is_file():
            return match.group(0)
        content = target.read_text(encoding="utf-8", errors="ignore")
        if attr == "href" and target.suffix == ".css":
            return f"<style>{content}</style>__DROP_TAG__"
        if attr == "src" and target.suffix in {".js", ".mjs"}:
            return f"<script>\n{content}\n</script>__DROP_TAG__"
        return match.group(0)

    html_text = _HREF_RE.sub(replace, html_text)
    # Drop the original <link>/<script> tag once we've inlined its body.
    html_text = re.sub(r"<link[^>]*>__DROP_TAG__", "", html_text)
    html_text = re.sub(r"</script>__DROP_TAG__", "", html_text)
    # Drop Next.js' <link rel="preload"|"modulepreload"> hints — every asset
    # they point at is already inlined, so the browser would otherwise issue
    # 404s when this HTML is opened offline.
    html_text = re.sub(r'<link[^>]+rel="(?:preload|modulepreload)"[^>]*>', "", html_text)
    return html_text


def _fallback_html(app_data: dict[str, Any]) -> str:
    """Minimal HTML packet used when the React bundle is not packaged.

    Contains the same data payload so the file is still grep-able and the
    `Verify dashboard artifact` CI step keeps passing.
    """
    payload = html.escape(json.dumps(app_data, sort_keys=True, default=str), quote=False)
    posture = app_data.get("posture", {}).get("posture", {})
    score = posture.get("score", "—")
    state = posture.get("state", "—")
    return _FALLBACK_TEMPLATE.format(payload=payload, score=score, state=state)


_FALLBACK_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TrustOps Assessment workbench (offline export)</title>
  <style>
    body{{font-family:Inter,system-ui,sans-serif;margin:0;background:#0b1218;color:#f8fafc}}
    main{{max-width:760px;margin:64px auto;padding:32px;background:#fff;color:#101623;border-radius:16px;box-shadow:0 24px 65px rgba(2,6,23,.22)}}
    h1{{font-size:28px;margin:0 0 8px}}
    .pill{{display:inline-block;padding:4px 10px;border-radius:999px;background:#dcfae6;color:#067647;font-weight:800;font-size:12px}}
    code{{display:block;padding:14px;border-radius:10px;background:#f1f5f9;color:#0f172a;overflow:auto;font-family:ui-monospace,Menlo,monospace;font-size:12px}}
    .muted{{color:#5f6f85;font-size:14px;margin-top:24px}}
  </style>
</head>
<body>
<script id="app-data" type="application/json">{payload}</script>
<main>
  <div class="pill">offline evidence packet</div>
  <h1>Assessment workbench</h1>
  <p>This file ships a frozen assessment payload for offline review. The full interactive workbench is available by running:</p>
  <code>security-lakehouse serve --lake build/lakehouse</code>
  <p>The packet below holds the posture, controls, evidence, and snapshots for the lake this export was built from.</p>
  <p><b>Posture score:</b> {score}% &middot; <b>State:</b> {state}</p>
  <p class="muted">Build the React bundle (<code>make web-build</code>) to ship the full single-file workbench.</p>
</main>
</body>
</html>
"""
