// Ref: K-022 | F6-O5 — UI never authorizes; server decides
const API_BASE = "http://127.0.0.1:8000/api/v1";

let accessToken = null;

function authHeaders() {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

async function checkHealth() {
  const out = document.getElementById("out");
  try {
    const res = await fetch(`${API_BASE}/health`);
    out.textContent = JSON.stringify(await res.json(), null, 2);
  } catch (err) {
    out.textContent = String(err);
  }
}

async function login() {
  const out = document.getElementById("out");
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      out.textContent = JSON.stringify(data, null, 2);
      return;
    }
    accessToken = data.access_token;
    document.getElementById("btn-dashboard").disabled = false;
    out.textContent = `Login OK · roles: ${(data.roles || []).join(", ")}`;
    await loadDashboard();
  } catch (err) {
    out.textContent = String(err);
  }
}

async function loadDashboard() {
  const out = document.getElementById("out");
  const badge = document.getElementById("role-badge");
  const grid = document.getElementById("indicators");
  try {
    const res = await fetch(`${API_BASE}/dashboard`, { headers: authHeaders() });
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
    if (!res.ok) {
      badge.innerHTML = "";
      grid.innerHTML = "";
      return;
    }
    badge.innerHTML = `<span class="badge text-bg-primary">Vista: ${data.role_view}</span>`;
    grid.innerHTML = Object.entries(data.indicators || {})
      .map(
        ([k, v]) =>
          `<div class="col-6 col-md-3"><div class="p-3 bg-white border rounded"><div class="text-muted small">${k}</div><div class="fs-4">${v}</div></div></div>`
      )
      .join("");
  } catch (err) {
    out.textContent = String(err);
  }
}

document.getElementById("btn-health")?.addEventListener("click", checkHealth);
document.getElementById("btn-login")?.addEventListener("click", login);
document.getElementById("btn-dashboard")?.addEventListener("click", loadDashboard);
