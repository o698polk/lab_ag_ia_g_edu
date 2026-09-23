// Ref: K-015/K-022 | UI guard — server authorizes.
/* global SigaApi, SigaToast, SigaNav */
const LOGIN_URL = "/ui/pages/auth/login.html";

async function requireAuth() {
  if (!window.SigaApi) { location.replace(LOGIN_URL); return false; }
  SigaApi.applyStoredTokens();
  const { state, api, clearSession } = SigaApi;
  if (!state.accessToken && !state.refreshToken) {
    clearSession(); location.replace(LOGIN_URL); return false;
  }
  let me = await api("GET", "/auth/me", undefined, 5000);
  if (!me.ok && me.status === 401 && state.refreshToken) {
    const ok = await SigaApi.refreshAccessToken();
    if (ok) me = await api("GET", "/auth/me", undefined, 5000, false);
  }
  if (!me.ok || !me.data || !me.data.username) {
    clearSession(); location.replace(LOGIN_URL); return false;
  }
  state.user = me.data;
  applyRoleVisibility(me.data);
  if (window.SigaNav && typeof SigaNav.ensureAdminNav === "function") {
    SigaNav.ensureAdminNav(me.data);
  }
  if (window.SigaNav && typeof SigaNav.ensureIamNav === "function") {
    SigaNav.ensureIamNav(me.data);
  }
  if (window.SigaNav && typeof SigaNav.ensureSeguridadNav === "function") {
    SigaNav.ensureSeguridadNav(me.data);
  }
  if (window.SigaNav && typeof SigaNav.ensureCatalogExtras === "function") {
    SigaNav.ensureCatalogExtras();
  }
  const chip = document.getElementById("session-chip");
  if (chip) {
    chip.textContent = me.data.username + " · " + ((me.data.roles || []).join(", ") || "sin rol");
    chip.classList.add("ok"); chip.classList.remove("muted");
  }
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) logoutBtn.addEventListener("click", () => logout());
  if (window.SigaNav) SigaNav.wire();
  return true;
}

function applyRoleVisibility(user) {
  const roles = (user && user.roles) || [];
  document.querySelectorAll("[data-roles]").forEach((el) => {
    const wanted = String(el.getAttribute("data-roles") || "").split(",").map((r) => r.trim()).filter(Boolean);
    const show = !wanted.length || wanted.some((r) => roles.includes(r));
    el.classList.toggle("d-none", !show);
  });
}

async function logout() {
  const { state, api, clearSession } = SigaApi;
  if (state.refreshToken) await api("POST", "/auth/logout", { refresh_token: state.refreshToken });
  clearSession(); state.user = null; location.replace(LOGIN_URL);
}

function redirectIfAuthed() {
  if (!window.SigaApi) return;
  SigaApi.applyStoredTokens();
  if (SigaApi.state.accessToken || SigaApi.state.refreshToken) {
    location.replace("/ui/pages/dashboard/dashboard.html");
  }
}

window.SigaAuth = { requireAuth, logout, redirectIfAuthed, applyRoleVisibility, LOGIN_URL };
