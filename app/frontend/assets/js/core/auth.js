// Ref: K-015/K-022 | UI guard — server authorizes.
/* global SigaApi, SigaToast, SigaNav */
const LOGIN_URL = "/ui/pages/auth/login.html";

function peekTokenUser(token) {
  try {
    const part = String(token || "").split(".")[1];
    if (!part) return null;
    let padded = part.replace(/-/g, "+").replace(/_/g, "/");
    while (padded.length % 4) padded += "=";
    const json = atob(padded);
    const data = JSON.parse(json);
    if (!data || !data.username) return null;
    return { username: data.username, roles: data.roles || [] };
  } catch (e) {
    return null;
  }
}

function paintSessionChip(user) {
  const chip = document.getElementById("session-chip");
  if (!chip || !user) return;
  const name = user.username || user.full_name || "sesión";
  const roles = user.roles || [];
  chip.textContent = name + " · " + (roles.join(", ") || "usuario");
  chip.classList.add("ok");
  chip.classList.remove("muted");
}

let authBoot = null;

async function requireAuth() {
  if (authBoot) return authBoot;
  authBoot = _requireAuthImpl();
  const ok = await authBoot;
  if (!ok) authBoot = null;
  return ok;
}

async function _requireAuthImpl() {
  if (!window.SigaApi) { location.replace(LOGIN_URL); return false; }
  SigaApi.applyStoredTokens();
  const { state, api, clearSession } = SigaApi;
  if (!state.accessToken && !state.refreshToken) {
    clearSession(); location.replace(LOGIN_URL); return false;
  }
  paintSessionChip(state.user || peekTokenUser(state.accessToken));
  let me = await api("GET", "/auth/me", undefined, 12000);
  if (!me.ok && me.status === 401 && state.refreshToken) {
    const ok = await SigaApi.refreshAccessToken();
    if (ok) me = await api("GET", "/auth/me", undefined, 12000, false);
  }
  if (!me.ok || !me.data || !me.data.username) {
    if (me.status === 0 && state.accessToken) {
      paintSessionChip(state.user || peekTokenUser(state.accessToken));
      return true;
    }
    clearSession(); location.replace(LOGIN_URL); return false;
  }
  state.user = me.data;
  paintSessionChip(me.data);
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
  if (window.SigaNav && typeof SigaNav.ensureAgenteNav === "function") {
    SigaNav.ensureAgenteNav(me.data);
  }
  if (window.SigaNav && typeof SigaNav.ensureCatalogExtras === "function") {
    SigaNav.ensureCatalogExtras();
  }
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) logoutBtn.addEventListener("click", () => logout());
  if (window.SigaNav) SigaNav.wire();
  mountImpersonationBanner(me.data);
  mountFloatingChat();
  return true;
}

function mountImpersonationBanner(user) {
  const existing = document.getElementById("impersonation-banner");
  if (!user || !user.impersonating) {
    if (existing) existing.remove();
    document.body.classList.remove("has-impersonation-banner");
    return;
  }
  document.body.classList.add("has-impersonation-banner");
  const who = user.username || user.full_name || "usuario";
  if (existing) {
    existing.querySelector("[data-impersonated]") &&
      (existing.querySelector("[data-impersonated]").textContent = who);
    return;
  }
  const bar = document.createElement("div");
  bar.id = "impersonation-banner";
  bar.className = "impersonation-banner";
  bar.innerHTML =
    '<span>Viendo como <strong data-impersonated></strong></span>' +
    '<button type="button" class="btn btn-sm btn-light" id="btn-return-to-admin">Regresar a mi cuenta</button>';
  bar.querySelector("[data-impersonated]").textContent = who;
  document.body.prepend(bar);
  document.getElementById("btn-return-to-admin")?.addEventListener("click", () => returnToAdmin());
}

async function returnToAdmin() {
  const { state, api, saveSession, formatError } = SigaApi;
  const toast = window.SigaToast && SigaToast.toast ? SigaToast.toast : () => {};
  const { ok, data } = await api("POST", "/auth/return-to-admin", {
    refresh_token: state.refreshToken || null,
  });
  if (!ok) {
    toast(formatError ? formatError(data) : "No se pudo regresar a la cuenta original.", "bad");
    return;
  }
  saveSession(data.access_token, data.refresh_token);
  location.replace("/ui/pages/usuarios/usuarios.html");
}

function mountFloatingChat() {
  if (document.getElementById("login-form")) return;
  function boot() {
    if (window.SigaChatbot && typeof SigaChatbot.mount === "function") {
      SigaChatbot.mount();
    }
  }
  if (window.SigaChatbot) {
    boot();
    return;
  }
  if (!document.querySelector("link[data-siga-chatbot-css]")) {
    var css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "/ui/assets/css/chatbot.css";
    css.setAttribute("data-siga-chatbot-css", "1");
    document.head.appendChild(css);
  }
  if (document.querySelector("script[data-siga-chatbot]")) {
    return;
  }
  var script = document.createElement("script");
  script.src = "/ui/assets/js/components/chatbot.js";
  script.setAttribute("data-siga-chatbot", "1");
  script.onload = boot;
  document.body.appendChild(script);
}

function canTogglePolicies(user) {
  if (!user) return false;
  if (user.can_toggle_policies !== false) return true;
  return ((user.permissions || []).indexOf("ai.use") >= 0);
}

function applyRoleVisibility(user) {
  const roles = (user && user.roles) || [];
  document.querySelectorAll("[data-roles]").forEach((el) => {
    const wanted = String(el.getAttribute("data-roles") || "").split(",").map((r) => r.trim()).filter(Boolean);
    const show = !wanted.length || wanted.some((r) => roles.includes(r));
    el.classList.toggle("d-none", !show);
  });
  document.querySelectorAll("[data-lab-guard]").forEach((el) => {
    el.classList.toggle("d-none", !canTogglePolicies(user));
  });
}

async function logout() {
  const { state, api, clearSession } = SigaApi;
  if (state.refreshToken) await api("POST", "/auth/logout", { refresh_token: state.refreshToken });
  clearSession(); state.user = null; location.replace(LOGIN_URL);
}

function redirectIfAuthed() {
  if (!window.SigaApi) return false;
  SigaApi.applyStoredTokens();
  if (SigaApi.state.accessToken || SigaApi.state.refreshToken) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return true;
  }
  return false;
}

window.SigaAuth = {
  requireAuth,
  logout,
  redirectIfAuthed,
  applyRoleVisibility,
  paintSessionChip,
  mountFloatingChat,
  mountImpersonationBanner,
  returnToAdmin,
  LOGIN_URL,
};

if (document.getElementById("session-chip") && !document.getElementById("login-form")) {
  requireAuth();
}
