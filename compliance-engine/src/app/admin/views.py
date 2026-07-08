"""HTML views for the administrator dashboard."""

from html import escape

from app.config import settings


def login_page(error: str | None = None) -> str:
    """Return the administrator login page."""
    error_html = (
        f'<div class="notice error" role="alert">{escape(error)}</div>'
        if error is not None
        else ""
    )
    disabled = "" if settings.admin_dashboard_configured else "disabled"
    configuration_notice = (
        ""
        if settings.admin_dashboard_configured
        else (
            '<div class="notice error" role="alert">'
            "Administrator login is not configured. Set ADMIN_USERNAME, "
            "ADMIN_PASSWORD_HASH, and ADMIN_SESSION_SECRET."
            "</div>"
        )
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Compflow Admin Login</title>
  <style>{_base_css()}</style>
</head>
<body class="login-body">
  <main class="login-card" aria-labelledby="login-title">
    <p class="eyebrow">Administrator console</p>
    <h1 id="login-title">Compflow Control Desk</h1>
    <p class="muted">
      Maintenance, monitoring, and alerting tools are restricted to administrators.
      An active network session is required.
    </p>
    {configuration_notice}
    {error_html}
    <form method="post" action="/admin/login" class="login-form">
      <label>
        Username
        <input name="username" autocomplete="username" required {disabled}>
      </label>
      <label>
        Password
        <input name="password" type="password" autocomplete="current-password" required {disabled}>
      </label>
      <button type="submit" {disabled}>Sign in</button>
    </form>
  </main>
</body>
</html>"""


def dashboard_page() -> str:
    """Return the administrator dashboard page."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Compflow Admin Dashboard</title>
  <style>{_base_css()}{_dashboard_css()}</style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <p class="eyebrow">Compflow</p>
      <h1>Admin Dashboard</h1>
      <p>
        Desktop operations console for maintenance, monitoring, and alerts.
        Access is restricted to administrators only.
      </p>
      <nav aria-label="Admin sections">
        <a href="#overview">Overview</a>
        <a href="#alerts">Alerts</a>
        <a href="#runs">Recent runs</a>
        <a href="#maintenance">Maintenance</a>
        <a href="#audit">Admin audit</a>
      </nav>
      <form method="post" action="/admin/logout">
        <button class="ghost" type="submit">Sign out</button>
      </form>
    </aside>

    <main>
      <section class="hero" id="overview">
        <div>
          <p class="eyebrow">Online administrator tools</p>
          <h2>Mobile app operations control</h2>
          <p class="muted">
            This console monitors the backend services your application depends on.
            If the network drops, maintenance controls are intentionally unavailable.
          </p>
        </div>
        <div id="connection" class="status-pill">Checking network...</div>
      </section>

      <section class="grid cards" aria-label="System metrics">
        <article class="card"><span>Database</span><strong id="database">...</strong></article>
        <article class="card"><span>Ruleset</span><strong id="ruleset">...</strong></article>
        <article class="card"><span>Total runs</span><strong id="runs-total">...</strong></article>
        <article class="card"><span>Failed 24h</span><strong id="failed-24h">...</strong></article>
        <article class="card"><span>Admin role</span><strong id="admin-role">...</strong></article>
        <article class="card"><span>Alert delivery</span><strong id="alert-delivery">...</strong></article>
      </section>

      <section class="panel" id="alerts">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Alerts</p>
            <h3>Operational attention</h3>
          </div>
          <button id="refresh">Refresh</button>
        </div>
        <div id="alerts-list" class="alerts-list">Loading alerts...</div>
      </section>

      <section class="panel" id="runs">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Monitoring</p>
            <h3>Recent compliance runs</h3>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Company</th>
                <th>Status</th>
                <th>Employees</th>
                <th>Errors</th>
                <th>Warnings</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody id="recent-runs">
              <tr><td colspan="7">Loading recent runs...</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel" id="maintenance">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Maintenance</p>
            <h3>Admin tools</h3>
          </div>
        </div>
        <div class="actions">
          <button id="readiness-check">Run readiness check</button>
          <button id="reset-rate-limit" class="secondary">Reset rate limiter</button>
          <button id="test-alert" class="secondary">Send test alert</button>
        </div>
        <pre id="maintenance-output" aria-live="polite">No maintenance action run yet.</pre>
      </section>

      <section class="panel" id="audit">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Accountability</p>
            <h3>Recent admin audit events</h3>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Admin</th>
                <th>Role</th>
                <th>Event</th>
                <th>Status</th>
                <th>Request</th>
              </tr>
            </thead>
            <tbody id="admin-audit-events">
              <tr><td colspan="6">Loading audit events...</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
  <script>{_dashboard_js()}</script>
</body>
</html>"""


def _base_css() -> str:
    return """
:root {
  --bg: #0d1222;
  --panel: #151c31;
  --panel-2: #1d2740;
  --text: #f8fafc;
  --muted: #9aa7bd;
  --line: rgba(255, 255, 255, 0.1);
  --accent: #68e1fd;
  --accent-2: #9dffcb;
  --danger: #ff7a90;
  --warning: #ffd166;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(104, 225, 253, 0.18), transparent 32rem),
    radial-gradient(circle at bottom right, rgba(157, 255, 203, 0.12), transparent 28rem),
    var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
h1, h2, h3, p { margin-top: 0; }
.eyebrow {
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin-bottom: 0.6rem;
  text-transform: uppercase;
}
.muted { color: var(--muted); line-height: 1.6; }
button {
  border: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #08111f;
  cursor: pointer;
  font-weight: 800;
  padding: 0.8rem 1.2rem;
}
button:disabled {
  cursor: not-allowed;
  filter: grayscale(1);
  opacity: 0.5;
}
.secondary, .ghost {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text);
  border: 1px solid var(--line);
}
.notice {
  border-radius: 1rem;
  margin: 1rem 0;
  padding: 0.9rem 1rem;
}
.notice.error {
  background: rgba(255, 122, 144, 0.12);
  border: 1px solid rgba(255, 122, 144, 0.35);
  color: #ffd7de;
}
.login-body {
  align-items: center;
  display: flex;
  justify-content: center;
  padding: 2rem;
}
.login-card {
  background: rgba(21, 28, 49, 0.9);
  border: 1px solid var(--line);
  border-radius: 2rem;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
  max-width: 30rem;
  padding: 2.2rem;
  width: 100%;
}
.login-card h1 { font-size: clamp(2rem, 6vw, 3.2rem); }
.login-form { display: grid; gap: 1rem; margin-top: 1.5rem; }
label {
  color: var(--muted);
  display: grid;
  font-size: 0.9rem;
  gap: 0.45rem;
}
input {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--line);
  border-radius: 0.9rem;
  color: var(--text);
  font: inherit;
  padding: 0.85rem 1rem;
}
"""


def _dashboard_css() -> str:
    return """
.app-shell {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 20rem minmax(0, 1fr);
  min-height: 100vh;
  padding: 1.5rem;
}
.sidebar {
  align-self: start;
  background: rgba(21, 28, 49, 0.88);
  border: 1px solid var(--line);
  border-radius: 1.6rem;
  padding: 1.4rem;
  position: sticky;
  top: 1.5rem;
}
.sidebar h1 { font-size: 2rem; }
.sidebar p { color: var(--muted); line-height: 1.55; }
.sidebar nav {
  display: grid;
  gap: 0.35rem;
  margin: 1.5rem 0;
}
.sidebar a {
  border-radius: 0.9rem;
  color: var(--text);
  padding: 0.75rem 0.9rem;
  text-decoration: none;
}
.sidebar a:hover { background: rgba(255, 255, 255, 0.07); }
main { display: grid; gap: 1.2rem; }
.hero, .panel, .card {
  background: rgba(21, 28, 49, 0.88);
  border: 1px solid var(--line);
  border-radius: 1.6rem;
  box-shadow: 0 18px 55px rgba(0, 0, 0, 0.24);
}
.hero {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 1.5rem;
}
.hero h2 { font-size: clamp(2rem, 4vw, 4rem); line-height: 1; }
.status-pill {
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--accent-2);
  padding: 0.65rem 1rem;
  white-space: nowrap;
}
.status-pill.offline { color: var(--danger); }
.grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.card { padding: 1.2rem; }
.card span {
  color: var(--muted);
  display: block;
  font-size: 0.82rem;
  margin-bottom: 0.65rem;
}
.card strong { font-size: 1.7rem; }
.panel { padding: 1.3rem; }
.panel-heading {
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
.panel h3 { margin-bottom: 0; }
.alerts-list { display: grid; gap: 0.75rem; }
.alert {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--line);
  border-left: 0.35rem solid var(--accent);
  border-radius: 1rem;
  padding: 0.9rem 1rem;
}
.alert.critical { border-left-color: var(--danger); }
.alert.warning { border-left-color: var(--warning); }
.alert h4 { margin: 0 0 0.25rem; }
.alert p { color: var(--muted); margin: 0; }
.table-wrap { overflow-x: auto; }
table {
  border-collapse: collapse;
  min-width: 55rem;
  width: 100%;
}
th, td {
  border-bottom: 1px solid var(--line);
  padding: 0.85rem 0.6rem;
  text-align: left;
}
th {
  color: var(--muted);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.actions { display: flex; flex-wrap: wrap; gap: 0.8rem; }
pre {
  background: #080d18;
  border: 1px solid var(--line);
  border-radius: 1rem;
  color: #dce9ff;
  margin-bottom: 0;
  margin-top: 1rem;
  overflow: auto;
  padding: 1rem;
}
@media (max-width: 980px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { position: static; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
"""


def _dashboard_js() -> str:
    return """
const connection = document.getElementById("connection");
const output = document.getElementById("maintenance-output");

function setConnection() {
  if (navigator.onLine) {
    connection.textContent = "Network online";
    connection.classList.remove("offline");
  } else {
    connection.textContent = "Network required";
    connection.classList.add("offline");
  }
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[char]);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {"Accept": "application/json"},
    ...options
  });
  if (response.status === 401) {
    window.location.assign("/admin/login");
    return null;
  }
  const body = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(body));
  return body;
}

async function loadOverview() {
  setConnection();
  if (!navigator.onLine) {
    document.getElementById("alerts-list").innerHTML =
      '<div class="alert critical"><h4>Network required</h4><p>The admin console cannot load maintenance tools while offline.</p></div>';
    return;
  }

  const data = await fetchJson("/admin/api/overview");
  if (!data) return;

  document.getElementById("database").textContent = data.system.database;
  document.getElementById("ruleset").textContent = data.system.current_ruleset;
  document.getElementById("runs-total").textContent = data.metrics.runs_total;
  document.getElementById("failed-24h").textContent = data.metrics.failed_runs_24h;
  document.getElementById("admin-role").textContent = data.session?.role ?? "unknown";
  document.getElementById("alert-delivery").textContent = data.system.alert_delivery;

  const alerts = data.alerts.length ? data.alerts : [{
    severity: "info",
    title: "No active alerts",
    message: "The service reports no operational alerts at this time."
  }];
  document.getElementById("alerts-list").innerHTML = alerts.map((alert) => `
    <article class="alert ${escapeHtml(alert.severity)}">
      <h4>${escapeHtml(alert.title)}</h4>
      <p>${escapeHtml(alert.message)}</p>
    </article>
  `).join("");

  const rows = data.recent_runs.length ? data.recent_runs.map((run) => `
    <tr>
      <td>${escapeHtml(run.run_id)}</td>
      <td>${escapeHtml(run.company_id)}</td>
      <td>${escapeHtml(run.status)}</td>
      <td>${escapeHtml(run.employee_count)}</td>
      <td>${escapeHtml(run.errors)}</td>
      <td>${escapeHtml(run.warnings)}</td>
      <td>${escapeHtml(formatDate(run.created_at))}</td>
    </tr>
  `).join("") : '<tr><td colspan="7">No compliance runs have been recorded yet.</td></tr>';
  document.getElementById("recent-runs").innerHTML = rows;

  const auditRows = data.admin_audit_events.length ? data.admin_audit_events.map((event) => `
    <tr>
      <td>${escapeHtml(formatDate(event.created_at))}</td>
      <td>${escapeHtml(event.admin_username ?? "-")}</td>
      <td>${escapeHtml(event.admin_role ?? "-")}</td>
      <td>${escapeHtml(event.event_type)}</td>
      <td>${escapeHtml(event.status)}</td>
      <td>${escapeHtml(event.request_id ?? "-")}</td>
    </tr>
  `).join("") : '<tr><td colspan="6">No administrator audit events have been recorded yet.</td></tr>';
  document.getElementById("admin-audit-events").innerHTML = auditRows;
}

document.getElementById("refresh").addEventListener("click", () => {
  loadOverview().catch((error) => {
    output.textContent = `Refresh failed: ${error.message}`;
  });
});

document.getElementById("readiness-check").addEventListener("click", async () => {
  output.textContent = "Running readiness check...";
  try {
    const result = await fetchJson("/admin/api/maintenance/readiness");
    output.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    output.textContent = `Readiness check failed: ${error.message}`;
  }
});

document.getElementById("reset-rate-limit").addEventListener("click", async () => {
  output.textContent = "Resetting rate limiter...";
  try {
    const result = await fetchJson("/admin/api/maintenance/rate-limit/reset", {method: "POST"});
    output.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    output.textContent = `Rate limiter reset failed: ${error.message}`;
  }
});

document.getElementById("test-alert").addEventListener("click", async () => {
  output.textContent = "Sending test alert...";
  try {
    const result = await fetchJson("/admin/api/maintenance/alerts/test", {method: "POST"});
    output.textContent = JSON.stringify(result, null, 2);
    await loadOverview();
  } catch (error) {
    output.textContent = `Test alert failed: ${error.message}`;
  }
});

window.addEventListener("online", loadOverview);
window.addEventListener("offline", setConnection);
loadOverview().catch((error) => {
  document.getElementById("alerts-list").innerHTML =
    `<div class="alert critical"><h4>Dashboard load failed</h4><p>${escapeHtml(error.message)}</p></div>`;
});
"""
