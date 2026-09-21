// Ref: K-015/K-022 | UI guard only — server still authorizes every request.
/* global SigaApi, SigaUi */

const LOGIN_URL = "/ui/pages/login.html";
const HOME_URL = "/ui/pages/home.html";

async function requireAuth() {
  if (!window.SigaApi) {
    location.replace(LOGIN_URL);
    return false;
  }
  SigaApi.applyStoredTokens();
  const { state, api, clearSession } = SigaApi;
  if (!state.accessToken && !state.refreshToken) {
    clearSession();
    location.replace(LOGIN_URL);
    return false;
  }
  let me = await api("GET", "/auth/me", undefined, 5000);
  if (!me.ok && me.status === 401 && state.refreshToken) {
    const ok = await SigaApi.refreshAccessToken();
    if (ok) me = await api("GET", "/auth/me", undefined, 5000, false);
  }
  if (!me.ok || !me.data || !me.data.username) {
    clearSession();
    location.replace(LOGIN_URL);
    return false;
  }
  state.user = me.data;
  if (window.SigaUi) {
    SigaUi.setSessionChip(me.data);
    SigaUi.applyRoleVisibility(me.data);
    SigaUi.wireMobileNav();
  }
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => logout().catch(() => {}));
  }
  return true;
}

async function logout() {
  const { state, api, clearSession } = SigaApi;
  if (state.refreshToken) {
    await api("POST", "/auth/logout", { refresh_token: state.refreshToken });
  }
  clearSession();
  state.user = null;
  location.replace(LOGIN_URL);
}

function redirectIfAuthed() {
  if (!window.SigaApi) return;
  SigaApi.applyStoredTokens();
  if (SigaApi.state.accessToken || SigaApi.state.refreshToken) {
    location.replace("/ui/pages/dashboard.html");
  }
}

window.SigaAuth = {
  requireAuth,
  logout,
  redirectIfAuthed,
  LOGIN_URL,
  HOME_URL,
};
