"""Static dashboard generation."""

from __future__ import annotations

import html
from pathlib import Path

from security_lakehouse.io import read_json


def render_dashboard(lake_dir: str | Path, out_path: str | Path) -> Path:
    lake = Path(lake_dir)
    data = read_json(lake / "gold" / "dashboard_data.json")
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_html(data), encoding="utf-8")
    return output


def _html(data: dict) -> str:
    metrics = data["metrics"]
    controls = data["control_posture"]
    assets = data["asset_risk"]
    events = data["recent_events"]
    stages = data.get("pipeline_stages", [])
    sources = data.get("source_mix", [])
    routes = data.get("backend_routes", [])
    severity = data.get("severity_mix", [])
    failing_controls = [row for row in controls if row["status"] == "fail"]
    ready_controls = [row for row in controls if row["status"] == "pass"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="data:," />
  <title>Internal TrustOps Console</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #eef2f6;
      --panel: #ffffff;
      --panel-2: #f8fafc;
      --text: #151922;
      --muted: #607086;
      --border: #d6dee9;
      --ink: #111827;
      --blue: #1d6fdc;
      --yellow: #c99a00;
      --green: #0f766e;
      --red: #b42318;
      --orange: #b54708;
      --shadow: 0 18px 45px rgba(20, 30, 50, .10);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
    .app {{ min-height: 100vh; display: grid; grid-template-columns: 248px minmax(0, 1fr); }}
    aside {{ background: #101722; color: #e5edf7; padding: 24px 18px; position: sticky; top: 0; height: 100vh; }}
    .brand {{ font-size: 18px; font-weight: 800; letter-spacing: 0; margin-bottom: 28px; }}
    .brand span {{ display: block; color: #93a4ba; font-size: 12px; font-weight: 600; margin-top: 4px; }}
    nav a {{ display: flex; justify-content: space-between; color: #c8d4e3; text-decoration: none; padding: 10px 12px; border-radius: 8px; margin-bottom: 4px; font-size: 14px; }}
    nav a.active {{ background: #1d2a3a; color: white; }}
    .side-card {{ margin-top: 24px; padding: 14px; border: 1px solid #2b3b50; border-radius: 8px; background: #152131; }}
    .side-card strong {{ display: block; font-size: 26px; }}
    .side-card span {{ color: #9fb0c5; font-size: 12px; }}
    main {{ padding: 26px 32px 42px; display: grid; gap: 20px; }}
    .hero {{ display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(520px, .95fr); gap: 20px; align-items: stretch; }}
    .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow); overflow: hidden; }}
    .hero-copy {{ padding: 28px; display: grid; align-content: space-between; min-height: 360px; }}
    .eyebrow {{ color: var(--green); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0; }}
    h1 {{ font-size: 42px; line-height: 1.05; margin: 8px 0 14px; letter-spacing: 0; }}
    p {{ color: var(--muted); line-height: 1.5; margin: 0; }}
    .hero-actions {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 24px; }}
    .metric {{ border: 1px solid var(--border); background: var(--panel-2); border-radius: 8px; padding: 14px; min-height: 92px; }}
    .metric strong {{ display: block; font-size: 28px; line-height: 1.05; color: var(--ink); overflow-wrap: anywhere; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 7px; }}
    .architecture {{ padding: 22px; display: grid; gap: 16px; }}
    .route-grid {{ display: grid; grid-template-columns: 1fr 110px 1fr; gap: 12px; align-items: center; }}
    .lake-box {{ border: 1px solid var(--border); border-radius: 8px; padding: 16px; background: linear-gradient(180deg, #fff, #f8fafc); min-height: 150px; }}
    .lake-box.snow strong {{ color: var(--blue); }}
    .lake-box.click strong {{ color: var(--yellow); }}
    .lake-box strong {{ display: block; font-size: 22px; margin-bottom: 6px; }}
    .lake-box small {{ color: var(--muted); line-height: 1.45; }}
    .router {{ display: grid; gap: 8px; justify-items: center; color: var(--muted); font-size: 12px; font-weight: 700; }}
    .router-line {{ width: 92px; height: 2px; background: var(--border); }}
    .stages {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }}
    .stage {{ background: #111827; color: #f8fafc; border-radius: 8px; padding: 11px; min-height: 84px; }}
    .stage b {{ display: block; font-size: 15px; }}
    .stage em {{ display: block; color: #a8b3c4; font-style: normal; font-size: 11px; margin-top: 4px; }}
    .stage span {{ display: block; font-size: 22px; font-weight: 800; margin-top: 8px; }}
    .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1.12fr .88fr; gap: 20px; }}
    h2 {{ margin: 0; padding: 18px 20px 0; font-size: 18px; }}
    .subhead {{ padding: 4px 20px 14px; color: var(--muted); font-size: 13px; }}
    .rows {{ padding: 0 20px 20px; display: grid; gap: 10px; }}
    .bar-row {{ display: grid; grid-template-columns: 145px minmax(0, 1fr) 44px; gap: 10px; align-items: center; font-size: 13px; }}
    .bar {{ height: 10px; border-radius: 999px; background: #e6ebf2; overflow: hidden; }}
    .bar i {{ display: block; height: 100%; background: var(--green); }}
    .risk i {{ background: var(--red); }}
    .warn i {{ background: var(--orange); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 11px 13px; border-top: 1px solid var(--border); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0; background: #f8fafc; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; }}
    .fail, .critical {{ color: var(--red); font-weight: 800; }}
    .high {{ color: var(--orange); font-weight: 800; }}
    .pass, .low {{ color: var(--green); font-weight: 800; }}
    .pill {{ display: inline-flex; border-radius: 999px; padding: 3px 8px; background: #edf2f7; color: var(--muted); font-size: 12px; font-weight: 700; }}
    .source-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }}
    .source {{ border: 1px solid var(--border); border-radius: 8px; padding: 10px; background: #fbfdff; }}
    .source strong {{ display: block; font-size: 13px; overflow-wrap: anywhere; }}
    .source span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 4px; }}
    .evidence-ref {{ max-width: 360px; overflow-wrap: anywhere; color: var(--muted); }}
    @media (max-width: 1180px) {{
      .app {{ grid-template-columns: 1fr; }}
      aside {{ position: static; height: auto; }}
      .hero, .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">TrustOps Lakehouse<span>Internal compliance automation</span></div>
      <nav>
        <a class="active" href="#overview">Overview <span>{metrics["control_count"]}</span></a>
        <a href="#controls">Controls <span>{len(failing_controls)} fail</span></a>
        <a href="#evidence">Evidence <span>{metrics["total_events"]}</span></a>
        <a href="#lakes">Data Lakes <span>2</span></a>
      </nav>
      <div class="side-card"><strong>{metrics["evidence_coverage"]:.0%}</strong><span>evidence coverage</span></div>
      <div class="side-card"><strong>{metrics["runtime_block_rate"]:.0%}</strong><span>runtime policy block rate</span></div>
    </aside>
    <main id="overview">
      <section class="hero">
        <div class="panel hero-copy">
          <div>
            <div class="eyebrow">Internal trust automation console</div>
            <h1>Continuous compliance evidence for one company.</h1>
            <p>Ingest security signals, normalize them into a common evidence model, map them to controls, route telemetry to ClickHouse, route audit evidence to Snowflake, and give owners a control-by-control remediation view.</p>
          </div>
          <div class="hero-actions">
            {_metric("Controls Ready", len(ready_controls))}
            {_metric("Control Gaps", len(failing_controls))}
            {_metric("Top Risk Asset", metrics["top_risk_asset"])}
          </div>
        </div>
        <div class="panel architecture" id="lakes">
          <h2>Evidence Routing Architecture</h2>
          <div class="route-grid">
            {_lake_panel(routes, "Snowflake", "snow")}
            <div class="router">
              <span>validated events</span>
              <div class="router-line"></div>
              <span>control mappings</span>
              <div class="router-line"></div>
              <span>owner metrics</span>
            </div>
            {_lake_panel(routes, "ClickHouse", "click")}
          </div>
          <div class="stages">{''.join(_stage(row) for row in stages)}</div>
        </div>
      </section>

      <section class="grid-3">
        <div class="panel">
          <h2>Trust KPIs</h2>
          <div class="subhead">Executive posture from the gold model.</div>
          <div class="rows">
            {_progress("Control pass rate", metrics["control_pass_rate"], "warn")}
            {_progress("Evidence coverage", metrics["evidence_coverage"], "")}
            {_progress("Runtime block rate", metrics["runtime_block_rate"], "")}
            {_progress("Average asset risk", min(float(metrics["avg_asset_risk"]) / 100, 1), "risk")}
          </div>
        </div>
        <div class="panel">
          <h2>Severity Mix</h2>
          <div class="subhead">Open and observed risk concentration.</div>
          <div class="rows">{''.join(_severity_row(row, metrics["total_events"]) for row in severity)}</div>
        </div>
        <div class="panel">
          <h2>Evidence Connectors</h2>
          <div class="subhead">Sources are operational inputs, not page decoration.</div>
          <div class="rows source-grid">{''.join(_source_card(row) for row in sources)}</div>
        </div>
      </section>

      <section class="grid-2" id="controls">
        <div class="panel">
          <h2>Control Workbench</h2>
          <div class="subhead">Risk-ranked controls with owner, status, and evidence completeness.</div>
          <table>
            <thead><tr><th>Control</th><th>Framework</th><th>Status</th><th>Risk</th><th>Evidence</th><th>Owner</th></tr></thead>
            <tbody>{''.join(_control_row(row) for row in controls)}</tbody>
          </table>
        </div>
        <div class="panel">
          <h2>Asset Risk Queue</h2>
          <div class="subhead">Owner-ready remediation queue for the highest-risk systems.</div>
          <table>
            <thead><tr><th>Asset</th><th>Owner</th><th>Risk</th><th>Critical</th><th>High</th></tr></thead>
            <tbody>{''.join(_asset_row(row) for row in assets[:8])}</tbody>
          </table>
        </div>
      </section>

      <section class="panel" id="evidence">
        <h2>Evidence Room</h2>
        <div class="subhead">Auditor-facing trail from control to event to retained evidence reference.</div>
        <table>
          <thead><tr><th>Time</th><th>Source</th><th>Type</th><th>Asset</th><th>Severity</th><th>Status</th><th>Evidence</th></tr></thead>
          <tbody>{''.join(_event_row(row) for row in events)}</tbody>
        </table>
      </section>
    </main>
  </div>
</body>
</html>
"""


def _metric(label: str, value: object) -> str:
    return f'<div class="metric"><strong>{html.escape(str(value))}</strong><span>{html.escape(label)}</span></div>'


def _lake_panel(routes: list[dict], name: str, css: str) -> str:
    route = next((row for row in routes if row.get("backend") == name), {})
    tables = route.get("primary_tables", [])
    return (
        f'<div class="lake-box {css}">'
        f"<strong>{html.escape(name)}</strong>"
        f"<small>{html.escape(str(route.get('role', 'security lake')))}</small>"
        f"<div class=\"metric\" style=\"margin-top:12px; box-shadow:none;\"><strong>{html.escape(str(route.get('events', 0)))}</strong><span>routed events</span></div>"
        f"<small>{html.escape(', '.join(str(table) for table in tables[:4]))}</small>"
        "</div>"
    )


def _stage(row: dict) -> str:
    return (
        '<div class="stage">'
        f"<b>{html.escape(str(row.get('name', '')))}</b>"
        f"<em>{html.escape(str(row.get('label', '')))}</em>"
        f"<span>{html.escape(str(row.get('count', 0)))}</span>"
        "</div>"
    )


def _progress(label: str, value: float, css: str) -> str:
    pct = max(0, min(100, round(value * 100)))
    return (
        f'<div class="bar-row {css}">'
        f"<span>{html.escape(label)}</span>"
        f'<div class="bar"><i style="width:{pct}%"></i></div>'
        f"<b>{pct}%</b>"
        "</div>"
    )


def _severity_row(row: dict, total: int) -> str:
    count = int(row.get("count", 0))
    pct = count / total if total else 0
    css = "risk" if row.get("severity") in {"critical", "high"} else "warn" if row.get("severity") == "medium" else ""
    return _progress(f"{row.get('severity', '')} ({count})", pct, css)


def _source_card(row: dict) -> str:
    route = str(row.get("route", "dual"))
    route_label = "Snowflake + ClickHouse" if route == "dual" else route
    return (
        '<div class="source">'
        f"<strong>{html.escape(str(row.get('source', 'unknown')))}</strong>"
        f"<span>{html.escape(str(row.get('events', 0)))} events, {html.escape(str(row.get('open', 0)))} gaps</span>"
        f'<span class="pill">{html.escape(route_label)}</span>'
        "</div>"
    )


def _control_row(row: dict) -> str:
    return (
        "<tr>"
        f"<td><code>{html.escape(row['control_id'])}</code><br>{html.escape(row['title'])}</td>"
        f"<td>{html.escape(row['framework'])}</td>"
        f"<td class=\"{html.escape(row['status'])}\">{html.escape(row['status'])}</td>"
        f"<td>{html.escape(str(row['risk_score']))}</td>"
        f"<td>{html.escape(str(row['evidence_count']))}/{html.escape(str(row['event_count']))}</td>"
        f"<td>{html.escape(row['owner'])}</td>"
        "</tr>"
    )


def _asset_row(row: dict) -> str:
    return (
        "<tr>"
        f"<td><code>{html.escape(row['asset_id'])}</code><br><span class=\"pill\">{html.escape(row['asset_type'])}</span></td>"
        f"<td>{html.escape(row['asset_owner'])}</td>"
        f"<td>{html.escape(str(row['risk_score']))}</td>"
        f"<td class=\"critical\">{html.escape(str(row['critical_open']))}</td>"
        f"<td class=\"high\">{html.escape(str(row['high_open']))}</td>"
        "</tr>"
    )


def _event_row(row: dict) -> str:
    evidence = row.get("evidence_ref") or row.get("evidence_id")
    severity = str(row.get("severity", "info"))
    return (
        "<tr>"
        f"<td>{html.escape(row['event_time'])}</td>"
        f"<td>{html.escape(row['source'])}</td>"
        f"<td>{html.escape(row['event_type'])}</td>"
        f"<td><code>{html.escape(row['asset_id'])}</code></td>"
        f"<td class=\"{html.escape(severity)}\">{html.escape(severity)}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td class=\"evidence-ref\"><code>{html.escape(str(evidence))}</code></td>"
        "</tr>"
    )
