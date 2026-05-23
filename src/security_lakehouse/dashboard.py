"""Interactive TrustOps console generation."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from security_lakehouse.assessment import build_current_posture
from security_lakehouse.io import read_json, read_jsonl


def render_dashboard(lake_dir: str | Path, out_path: str | Path) -> Path:
    lake = Path(lake_dir)
    app_data = _load_app_data(lake)
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_html(app_data), encoding="utf-8")
    return output


def _load_app_data(lake: Path) -> dict[str, Any]:
    dashboard = read_json(lake / "gold" / "dashboard_data.json")
    posture_path = lake / "gold" / "current_posture.json"
    posture = read_json(posture_path) if posture_path.exists() else build_current_posture(lake)
    return {
        "generated_at": dashboard.get("generated_at"),
        "metrics": dashboard.get("metrics", {}),
        "controls": dashboard.get("control_posture", []),
        "assets": dashboard.get("asset_risk", []),
        "events": read_jsonl(lake / "silver" / "normalized_events.jsonl"),
        "posture": posture,
        "sources": dashboard.get("source_mix", []),
        "routes": dashboard.get("backend_routes", []),
        "stages": dashboard.get("pipeline_stages", []),
    }


def _html(app_data: dict[str, Any]) -> str:
    payload = html.escape(json.dumps(app_data, sort_keys=True, default=str), quote=False)
    return _TEMPLATE.replace("__APP_DATA__", payload)


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="data:," />
  <title>TrustOps Assessment Console</title>
  <style>
    :root{--bg:#eef2f6;--panel:#fff;--panel2:#f8fafc;--ink:#121722;--muted:#64748b;--line:#d7dee8;--nav:#0f1724;--blue:#1d6fdc;--green:#0f766e;--red:#b42318;--orange:#b54708;--yellow:#c99a00;--shadow:0 18px 45px rgba(20,30,50,.10)}
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif} button,input,select{font:inherit}
    .app{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh}.nav{background:var(--nav);color:#dbe7f6;padding:22px 16px;position:sticky;top:0;height:100vh}.brand{font-size:21px;font-weight:850;letter-spacing:0;margin-bottom:3px}.tagline{color:#96a6ba;font-size:12px;font-weight:650;margin-bottom:24px}.nav button{width:100%;display:flex;justify-content:space-between;align-items:center;color:#c9d6e6;background:transparent;border:0;border-radius:8px;padding:11px 12px;margin:3px 0;cursor:pointer;text-align:left}.nav button.active{background:#1d2a3a;color:#fff}.nav .chip{background:#29384d;color:#dce8f7;border-radius:999px;padding:2px 8px;font-size:12px}.navcard{border:1px solid #2e4058;background:#162234;border-radius:8px;padding:14px;margin-top:18px}.navcard strong{font-size:28px;display:block}.navcard span{font-size:12px;color:#a9b8c9}.main{padding:24px 30px 38px;display:grid;gap:18px}.topbar{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.title h1{font-size:30px;line-height:1.1;margin:0 0 6px}.title p{margin:0;color:var(--muted)}.actions{display:flex;gap:10px;flex-wrap:wrap}.btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:10px 13px;cursor:pointer;font-weight:750}.btn.primary{background:#111827;color:#fff;border-color:#111827}.btn.good{background:#ecfdf5;color:var(--green);border-color:#b7e4cf}.status{display:inline-flex;gap:8px;align-items:center}.dot{width:9px;height:9px;border-radius:999px;background:var(--orange)}.dot.ok{background:var(--green)}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.metric,.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:var(--shadow)}.metric{padding:16px;min-height:110px}.metric .label{color:var(--muted);font-size:12px;font-weight:750;text-transform:uppercase}.metric strong{display:block;font-size:34px;line-height:1.05;margin-top:8px;overflow-wrap:anywhere}.metric small{color:var(--muted)}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}.toolbar input,.toolbar select{border:1px solid var(--line);border-radius:8px;padding:9px 10px;background:#fff;min-width:180px}.panel h2{font-size:18px;margin:0;padding:17px 18px 0}.sub{padding:4px 18px 14px;color:var(--muted);font-size:13px}.split{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px}.list{display:grid;gap:10px;padding:0 18px 18px}.item{border:1px solid var(--line);background:#fbfdff;border-radius:8px;padding:12px;cursor:pointer}.item:hover{border-color:#9fb4d2}.item.active{border-color:#111827;box-shadow:0 0 0 2px rgba(17,24,39,.08)}.row{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}.item h3{font-size:15px;margin:0 0 6px}.muted{color:var(--muted)}.pills{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.pill{display:inline-flex;border-radius:999px;background:#edf2f7;color:#53657c;padding:3px 8px;font-size:12px;font-weight:750}.pill.fail,.pill.critical{background:#fee4e2;color:var(--red)}.pill.high{background:#fff1df;color:var(--orange)}.pill.pass,.pill.ready{background:#dcfce7;color:var(--green)}.drawer{position:sticky;top:20px;align-self:start}.drawer .body{padding:16px 18px 18px;display:grid;gap:12px}.kv{display:grid;grid-template-columns:110px 1fr;gap:8px;font-size:13px}.kv span:first-child{color:var(--muted)}.bars{display:grid;gap:10px;padding:0 18px 18px}.barrow{display:grid;grid-template-columns:150px 1fr 48px;gap:10px;align-items:center;font-size:13px}.bar{height:10px;border-radius:999px;background:#e6ebf2;overflow:hidden}.bar i{display:block;height:100%;background:var(--green)}.bar.risk i{background:var(--red)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:11px 13px;border-top:1px solid var(--line);text-align:left;vertical-align:top}th{font-size:11px;text-transform:uppercase;color:var(--muted);background:#f8fafc}code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px}.hidden{display:none!important}.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:0 18px 18px}.source{border:1px solid var(--line);border-radius:8px;padding:12px;background:#fbfdff}.toast{position:fixed;right:22px;bottom:22px;background:#111827;color:white;border-radius:8px;padding:12px 14px;box-shadow:var(--shadow);display:none;max-width:420px}.toast.show{display:block}@media(max-width:1180px){.app{grid-template-columns:1fr}.nav{height:auto;position:static}.grid4,.split,.cards{grid-template-columns:1fr}.topbar{display:grid}.drawer{position:static}}
  </style>
</head>
<body>
<script id="app-data" type="application/json">__APP_DATA__</script>
<div class="app">
  <aside class="nav">
    <div class="brand">TrustOps</div><div class="tagline">Continuous assessment console</div>
    <button class="active" data-view="overview">Current posture <span class="chip" id="navState">live</span></button>
    <button data-view="controls">Controls <span class="chip" id="navControls">0</span></button>
    <button data-view="violations">Violations <span class="chip" id="navViolations">0</span></button>
    <button data-view="evidence">Evidence <span class="chip" id="navEvidence">0</span></button>
    <button data-view="snapshots">Snapshots <span class="chip">JIT</span></button>
    <button data-view="agents">Agent API <span class="chip">JSON</span></button>
    <div class="navcard"><strong id="sideScore">--</strong><span>current posture score</span></div>
    <div class="navcard"><strong id="sideState">--</strong><span>assessment state</span></div>
  </aside>
  <main class="main">
    <div class="topbar">
      <div class="title"><h1>Current compliance and risk assessment</h1><p>Live posture from local evidence, framework controls, violations, and point-in-time snapshots.</p></div>
      <div class="actions"><span class="btn good status"><span class="dot" id="apiDot"></span><span id="apiState">API checking</span></span><button class="btn" id="refreshBtn">Refresh posture</button><button class="btn primary" id="snapshotBtn">Create snapshot</button></div>
    </div>
    <section id="overview" class="view"></section>
    <section id="controls" class="view hidden"></section>
    <section id="violations" class="view hidden"></section>
    <section id="evidence" class="view hidden"></section>
    <section id="snapshots" class="view hidden"></section>
    <section id="agents" class="view hidden"></section>
  </main>
</div>
<div id="toast" class="toast"></div>
<script>
const app=JSON.parse(document.getElementById('app-data').textContent);let selectedControl=null;let filter={framework:'all',severity:'all',query:''};
const $=s=>document.querySelector(s);const $$=s=>Array.from(document.querySelectorAll(s));const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function violations(){return app.posture.violations||[]}function controls(){return app.controls||[]}function assets(){return app.assets||[]}function events(){return app.events||[]}
function boot(){selectedControl=controls()[0]?.control_id;renderShell();renderAll();checkApi();}
function renderShell(){const p=app.posture.posture;$('#navControls').textContent=controls().length;$('#navViolations').textContent=p.open_violation_count;$('#navEvidence').textContent=events().length;$('#sideScore').textContent=p.score;$('#sideState').textContent=p.state;$('#navState').textContent=p.state;$$('.nav button[data-view]').forEach(b=>b.onclick=()=>showView(b.dataset.view));$('#refreshBtn').onclick=()=>{checkApi(true);toast('Posture refreshed from local assessment data')};$('#snapshotBtn').onclick=createSnapshot;}
function showView(id){$$('.view').forEach(v=>v.classList.toggle('hidden',v.id!==id));$$('.nav button[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===id));}
function renderAll(){renderOverview();renderControls();renderViolations();renderEvidence();renderSnapshots();renderAgents();}
function metric(label,value,sub=''){return `<div class="metric"><span class="label">${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(sub)}</small></div>`}
function renderOverview(){const p=app.posture.posture;const fw=app.posture.frameworks||[];$('#overview').innerHTML=`<div class="grid4">${metric('Posture score',p.score,'weighted framework score')}${metric('Assessment state',p.state,'current posture')}${metric('Open violations',p.open_violation_count,'owner action required')}${metric('Snapshots','on demand','audit/vendor/release')}</div><div class="split" style="margin-top:18px"><div class="panel"><h2>Framework posture</h2><div class="sub">Implemented scope: SOC 2-oriented controls and NIST AI RMF.</div><div class="bars">${fw.map(f=>bar(f.framework,f.score,`${f.failing_control_count} failing / ${f.violation_count} violations`)).join('')}</div></div><div class="panel"><h2>Top risk assets</h2><div class="sub">Owner-ready remediation queue.</div><div class="list">${assets().slice(0,5).map(a=>`<div class="item"><div class="row"><h3>${esc(a.asset_id)}</h3><span class="pill critical">${a.risk_score}</span></div><div class="muted">${esc(a.asset_owner)} · ${esc(a.asset_type)} · ${esc(a.environment)}</div><div class="pills"><span class="pill critical">${a.critical_open} critical</span><span class="pill high">${a.high_open} high</span></div></div>`).join('')}</div></div></div>`}
function bar(label,pct,sub){const cls=pct<50?'risk':pct<80?'warn':'';return `<div class="barrow"><span>${esc(label)}<br><small class="muted">${esc(sub)}</small></span><div class="bar ${cls}"><i style="width:${Math.max(0,Math.min(100,pct))}%"></i></div><b>${esc(pct)}%</b></div>`}
function toolbar(){const frameworks=['all',...new Set(controls().map(c=>c.framework))];return `<div class="toolbar"><input id="q" placeholder="Search controls, assets, evidence" value="${esc(filter.query)}"><select id="fw">${frameworks.map(f=>`<option ${filter.framework===f?'selected':''}>${esc(f)}</option>`).join('')}</select><select id="sev"><option>all</option><option ${filter.severity==='critical'?'selected':''}>critical</option><option ${filter.severity==='high'?'selected':''}>high</option><option ${filter.severity==='medium'?'selected':''}>medium</option></select></div>`}
function bindToolbar(){if($('#q'))$('#q').oninput=e=>{filter.query=e.target.value;renderActive()};if($('#fw'))$('#fw').onchange=e=>{filter.framework=e.target.value;renderActive()};if($('#sev'))$('#sev').onchange=e=>{filter.severity=e.target.value;renderActive()}}
function renderActive(){const id=$$('.view').find(v=>!v.classList.contains('hidden'))?.id||'overview';if(id==='controls')renderControls();if(id==='violations')renderViolations();if(id==='evidence')renderEvidence()}
function filteredControls(){return controls().filter(c=>(filter.framework==='all'||c.framework===filter.framework)&&JSON.stringify(c).toLowerCase().includes(filter.query.toLowerCase()))}
function renderControls(){const rows=filteredControls();const sel=controls().find(c=>c.control_id===selectedControl)||rows[0]||controls()[0];if(sel)selectedControl=sel.control_id;$('#controls').innerHTML=`${toolbar()}<div class="split"><div class="panel"><h2>Control workbench</h2><div class="sub">Click a control to inspect evidence, violations, owner, and API-safe facts.</div><div class="list">${rows.map(c=>controlItem(c)).join('')}</div></div><div class="panel drawer"><h2>Control detail</h2>${sel?controlDetail(sel):'<div class="sub">No control selected.</div>'}</div></div>`;bindToolbar();$$('[data-control]').forEach(el=>el.onclick=()=>{selectedControl=el.dataset.control;renderControls()})}
function controlItem(c){return `<div class="item ${c.control_id===selectedControl?'active':''}" data-control="${esc(c.control_id)}"><div class="row"><h3><code>${esc(c.control_id)}</code></h3><span class="pill ${c.status}">${esc(c.status)}</span></div><div>${esc(c.title)}</div><div class="pills"><span class="pill">${esc(c.framework)}</span><span class="pill">${esc(c.owner)}</span><span class="pill ${c.risk_score>=80?'critical':''}">risk ${esc(c.risk_score)}</span><span class="pill">evidence ${esc(c.evidence_count)}/${esc(c.event_count)}</span></div></div>`}
function controlDetail(c){const v=violations().filter(x=>x.control_id===c.control_id);const ev=events().filter(e=>e.control_ids.includes(c.control_id));return `<div class="body"><div class="kv"><span>Framework</span><b>${esc(c.framework)}</b><span>Owner</span><b>${esc(c.owner)}</b><span>Status</span><b class="${esc(c.status)}">${esc(c.status)}</b><span>Risk</span><b>${esc(c.risk_score)}</b><span>Evidence</span><b>${esc(c.evidence_count)}/${esc(c.event_count)}</b></div><div><b>Open violations</b>${v.map(x=>`<div class="item"><code>${esc(x.event_id)}</code> · ${esc(x.asset_id)}<div class="pills"><span class="pill ${x.severity}">${esc(x.severity)}</span><span class="pill">${esc(x.asset_owner)}</span></div></div>`).join('')||'<p class="muted">No open violations.</p>'}</div><div><b>Evidence</b>${ev.map(e=>`<div class="item"><code>${esc(e.evidence_id)}</code><br><span class="muted">${esc(e.evidence_ref)}</span></div>`).join('')}</div></div>`}
function filteredViolations(){return violations().filter(v=>(filter.framework==='all'||(controls().find(c=>c.control_id===v.control_id)?.framework===filter.framework))&&(filter.severity==='all'||v.severity===filter.severity)&&JSON.stringify(v).toLowerCase().includes(filter.query.toLowerCase()))}
function renderViolations(){const rows=filteredViolations();$('#violations').innerHTML=`${toolbar()}<div class="panel"><h2>Violation queue</h2><div class="sub">Actionable control failures grouped with owner, asset, source, and evidence reference.</div><table><thead><tr><th>Violation</th><th>Owner</th><th>Asset</th><th>Severity</th><th>Evidence</th></tr></thead><tbody>${rows.map(v=>`<tr><td><code>${esc(v.violation_id)}</code><br>${esc(v.event_type)}</td><td>${esc(v.asset_owner)}</td><td><code>${esc(v.asset_id)}</code></td><td><span class="pill ${v.severity}">${esc(v.severity)}</span></td><td><code>${esc(v.evidence_ref)}</code></td></tr>`).join('')}</tbody></table></div>`;bindToolbar()}
function renderEvidence(){const rows=events().filter(e=>(filter.severity==='all'||e.severity===filter.severity)&&JSON.stringify(e).toLowerCase().includes(filter.query.toLowerCase()));$('#evidence').innerHTML=`${toolbar()}<div class="panel"><h2>Evidence explorer</h2><div class="sub">Normalized evidence facts. Expand through API or snapshot for audit use.</div><table><thead><tr><th>Time</th><th>Source</th><th>Asset</th><th>Controls</th><th>Status</th><th>Evidence ref</th></tr></thead><tbody>${rows.map(e=>`<tr><td>${esc(e.event_time)}</td><td>${esc(e.source)}</td><td><code>${esc(e.asset_id)}</code></td><td>${e.control_ids.map(c=>`<span class="pill">${esc(c)}</span>`).join(' ')}</td><td><span class="pill ${e.status==='passed'?'pass':e.severity}">${esc(e.status)}</span></td><td><code>${esc(e.evidence_ref)}</code></td></tr>`).join('')}</tbody></table></div>`;bindToolbar()}
function renderSnapshots(){const p=app.posture;$('#snapshots').innerHTML=`<div class="panel"><h2>Point-in-time snapshots</h2><div class="sub">Freeze the current posture for vendor diligence, audit requests, release gates, or incident review.</div><div class="list"><div class="item"><div class="row"><h3>Current assessment hash</h3><span class="pill">sha256</span></div><code>${esc(p.assessment_hash)}</code></div><div class="item"><div class="row"><h3>Create snapshot through API</h3><button class="btn primary" onclick="createSnapshot()">Create snapshot</button></div><p class="muted">POST /api/snapshots with a reason. The local static file mode still shows the current hash.</p></div></div></div>`}
function renderAgents(){const routes=['GET /api/posture/current','GET /api/violations','GET /api/controls','GET /api/assets','POST /api/snapshots'];$('#agents').innerHTML=`<div class="panel"><h2>Agent API</h2><div class="sub">Use these contracts for coding agents, SOC analysts, and framework-specific skills. Agents should read API data, not infer from pixels.</div><div class="cards">${routes.map(r=>`<div class="source"><strong>${esc(r)}</strong><span>JSON assessment contract</span></div>`).join('')}</div></div><div class="panel" style="margin-top:18px"><h2>Framework skills</h2><div class="sub">SOC analyst, SOC 2, PCI, ISO, and AI governance skills are guardrailed to use official sources and local evidence.</div></div>`}
async function checkApi(show=false){try{const r=await fetch('/api/healthz',{cache:'no-store'});if(!r.ok)throw new Error('bad');$('#apiDot').classList.add('ok');$('#apiState').textContent='API live';if(show)toast('API live: posture can refresh and snapshots can be created')}catch(e){$('#apiDot').classList.remove('ok');$('#apiState').textContent='static mode';if(show)toast('Static mode: serve with security-lakehouse serve for API actions')}}
async function createSnapshot(){try{const r=await fetch('/api/snapshots',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({reason:'console_request'})});if(!r.ok)throw new Error('snapshot failed');const j=await r.json();toast(`Snapshot created: ${j.snapshot_path}`)}catch(e){toast('Snapshot API unavailable. Run: security-lakehouse serve --lake build/lakehouse --port 8787')}}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),4200)}
boot();
</script>
</body>
</html>"""
