"""Autoscaler dashboard — served at GET /dashboard."""
from flask import Blueprint, render_template_string

dashboard_bp = Blueprint("dashboard", __name__)

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Autoscaler Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: monospace; background: #0f1117; color: #e2e8f0; padding: 24px; }
  h1 { font-size: 1.2rem; color: #7dd3fc; margin-bottom: 20px; letter-spacing: 0.05em; }
  h2 { font-size: 0.75rem; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em; margin-bottom: 10px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .card { background: #1e2330; border: 1px solid #2d3748; border-radius: 8px; padding: 16px; }
  .card .label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
  .card .value { font-size: 1.8rem; font-weight: bold; }

  .green  { color: #4ade80; }
  .yellow { color: #facc15; }
  .red    { color: #f87171; }
  .blue   { color: #60a5fa; }
  .muted  { color: #475569; }

  table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
  th { text-align: left; padding: 8px 12px; color: #64748b; border-bottom: 1px solid #2d3748; font-weight: normal; }
  td { padding: 8px 12px; border-bottom: 1px solid #1a2030; }
  tr:hover td { background: #1a2336; }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }
  .badge-pending    { background: #1e3a5f; color: #60a5fa; }
  .badge-processing { background: #1a3320; color: #4ade80; }
  .badge-fixing     { background: #2d2010; color: #fb923c; }
  .badge-completed  { background: #1a3320; color: #86efac; }
  .badge-failed     { background: #3b1010; color: #f87171; }

  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .dot-active { background: #4ade80; box-shadow: 0 0 6px #4ade80; animation: pulse 1.5s infinite; }
  .dot-idle   { background: #475569; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  .updated { font-size: 0.65rem; color: #334155; margin-top: 16px; }
  .section { margin-bottom: 24px; }

  .controls { display: flex; gap: 10px; margin-bottom: 24px; align-items: center; }
  .btn { padding: 8px 18px; border: none; border-radius: 6px; font-family: monospace; font-size: 0.8rem; cursor: pointer; font-weight: bold; transition: opacity 0.15s; }
  .btn:hover { opacity: 0.85; }
  .btn-pause  { background: #facc15; color: #0f1117; }
  .btn-resume { background: #4ade80; color: #0f1117; }
  .paused-banner { font-size: 0.75rem; color: #facc15; background: #2d2200; border: 1px solid #facc1540; border-radius: 6px; padding: 6px 14px; display: none; }
  .paused-banner.visible { display: inline-block; }
</style>
</head>
<body>
<h1>⬡ Autoscaler Dashboard</h1>

<div class="controls">
  <button class="btn btn-pause"  id="btn-pause"  onclick="doAction('/pause')">⏸ Pause</button>
  <button class="btn btn-resume" id="btn-resume" onclick="doAction('/resume')" style="display:none">▶ Resume</button>
  <span class="paused-banner" id="paused-banner">⚠ Scaling paused — workers will not be adjusted</span>
</div>

<div class="section">
  <h2>RunPod Workers</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Standby</div>
      <div class="value green" id="w-standby">–</div>
    </div>
    <div class="card">
      <div class="label">Min / Max</div>
      <div class="value blue" id="w-minmax">–</div>
    </div>
    <div class="card">
      <div class="label">Stuck Checks</div>
      <div class="value" id="stuck">–</div>
    </div>
  </div>
</div>

<div class="section">
  <h2>Queue</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Active Jobs</div>
      <div class="value blue" id="active-jobs">–</div>
    </div>
    <div class="card">
      <div class="label">Idle For</div>
      <div class="value" id="idle-seconds">–</div>
    </div>
    <div class="card">
      <div class="label">Activity</div>
      <div class="value" id="activity">–</div>
    </div>
  </div>
</div>

<div class="section">
  <h2>Jobs</h2>
  <table>
    <thead>
      <tr>
        <th>Job ID</th>
        <th>Status</th>
        <th>Duration</th>
        <th>Style</th>
        <th>Template</th>
      </tr>
    </thead>
    <tbody id="jobs-tbody">
      <tr><td colspan="5" class="muted" style="padding:16px">Loading...</td></tr>
    </tbody>
  </table>
</div>

<div class="updated">Last updated: <span id="ts">–</span></div>

<script>
async function doAction(path) {
  try {
    await fetch(path, { method: 'POST' });
    await refresh();
  } catch(e) { console.error(e); }
}

async function refresh() {
  try {
    const [statusRes, jobsRes] = await Promise.all([
      fetch('/status'),
      fetch('/jobs'),
    ]);
    const s = await statusRes.json();
    const jobList = await jobsRes.json();

    // Pause state
    const paused = !!s.paused;
    document.getElementById('btn-pause').style.display  = paused ? 'none' : '';
    document.getElementById('btn-resume').style.display = paused ? '' : 'none';
    document.getElementById('paused-banner').classList.toggle('visible', paused);

    // Workers
    const standby = s.workers?.standby ?? '?';
    document.getElementById('w-standby').textContent = standby;
    document.getElementById('w-standby').className = 'value ' + (standby > 0 ? 'green' : 'red');
    document.getElementById('w-minmax').textContent = `${s.workers?.min ?? '?'} / ${s.workers?.max ?? '?'}`;
    const stuck = s.stuck_checks ?? 0;
    document.getElementById('stuck').textContent = stuck + ' / 2';
    document.getElementById('stuck').className = 'value ' + (stuck > 0 ? 'yellow' : 'muted');

    // Queue
    document.getElementById('active-jobs').textContent = s.active_jobs ?? 0;
    const idle = s.idle_seconds ?? 0;
    document.getElementById('idle-seconds').textContent = idle + 's';
    document.getElementById('idle-seconds').className = 'value ' + (idle > 240 ? 'red' : idle > 60 ? 'yellow' : 'green');
    const active = s.has_had_activity;
    document.getElementById('activity').innerHTML =
      `<span class="dot ${active ? 'dot-active' : 'dot-idle'}"></span>${active ? 'Active' : 'Dormant'}`;

    // Jobs table
    const tbody = document.getElementById('jobs-tbody');
    if (!jobList.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="muted" style="padding:16px">No jobs in store</td></tr>';
    } else {
      const sorted = jobList.sort((a,b) => (b.job_id > a.job_id ? 1 : -1));
      tbody.innerHTML = sorted.map(j => `
        <tr>
          <td class="muted">${j.job_id?.slice(0,8)}…</td>
          <td><span class="badge badge-${j.status}">${j.status}</span></td>
          <td>${j.duration_seconds ? j.duration_seconds.toFixed(1) + 's' : '–'}</td>
          <td>${j.style ?? '–'}</td>
          <td>${j.template ?? '–'}</td>
        </tr>
      `).join('');
    }

    document.getElementById('ts').textContent = new Date().toLocaleTimeString();
  } catch(e) {
    console.error(e);
  }
}

refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>"""


@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template_string(_HTML)
