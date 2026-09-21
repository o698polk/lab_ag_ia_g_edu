// Ref: BL-O5 / RF-AUTH-002…004 / RNF-UX | Skill: K-022/K-015 | Fase: post-F12
// UI client — never authorizes; server returns ALLOW/DENY.
const API_BASE =
  typeof location !== "undefined" && /^https?:/i.test(String(location.origin || ""))
    ? location.origin + "/api/v1"
    : "http://127.0.0.1:8000/api/v1";

const SESSION_KEY = "siga.lab.session";
const PANEL_KEY = "siga.lab.panel";

const state = {
  accessToken: null,
  refreshToken: null,
  user: null,
  conversationId: null,
  bootChecked: false,
  context: {
    courses: [],
    students: [],
    evaluations: [],
    subjects: [],
  },
};

function saveSession(accessToken, refreshToken) {
  try {
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: accessToken || null,
        refreshToken: refreshToken || null,
        savedAt: Date.now(),
      })
    );
  } catch (e) {
    /* private mode */
  }
}

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data || typeof data !== "object") return null;
    if (!data.accessToken && !data.refreshToken) return null;
    return data;
  } catch (e) {
    return null;
  }
}

function clearSession() {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (e) {
    /* ignore */
  }
  state.accessToken = null;
  state.refreshToken = null;
}

function savePanel(name) {
  try {
    if (name) localStorage.setItem(PANEL_KEY, name);
  } catch (e) {
    /* ignore */
  }
}

function loadPanel() {
  try {
    return localStorage.getItem(PANEL_KEY) || "dashboard";
  } catch (e) {
    return "dashboard";
  }
}

function applyStoredTokens() {
  const saved = loadSession();
  if (!saved) {
    state.accessToken = null;
    state.refreshToken = null;
    return false;
  }
  state.accessToken = saved.accessToken || null;
  state.refreshToken = saved.refreshToken || null;
  return !!(state.accessToken || state.refreshToken);
}

function authHeaders(json) {
  const headers = {};
  if (json !== false) headers["Content-Type"] = "application/json";
  if (state.accessToken) headers.Authorization = "Bearer " + state.accessToken;
  return headers;
}

let refreshInFlight = null;

async function refreshAccessToken() {
  if (!state.refreshToken) return false;
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async function () {
    const ctrl = new AbortController();
    const timer = setTimeout(function () {
      ctrl.abort();
    }, 5000);
    try {
      const res = await fetch(API_BASE + "/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: state.refreshToken }),
        signal: ctrl.signal,
      });
      const text = await res.text();
      let data = null;
      try {
        data = text ? JSON.parse(text) : null;
      } catch (e) {
        data = null;
      }
      if (!res.ok || !data || !data.access_token) return false;
      state.accessToken = data.access_token;
      if (data.refresh_token) state.refreshToken = data.refresh_token;
      saveSession(state.accessToken, state.refreshToken);
      return true;
    } catch (e) {
      return false;
    } finally {
      clearTimeout(timer);
    }
  })().finally(function () {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

async function api(method, path, body, timeoutMs, allowRefresh) {
  timeoutMs = timeoutMs || 20000;
  if (allowRefresh === undefined) allowRefresh = true;
  const opts = { method: method, headers: authHeaders(body !== undefined) };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const ctrl = new AbortController();
  const timer = setTimeout(function () {
    ctrl.abort();
  }, timeoutMs);
  opts.signal = ctrl.signal;
  try {
    const res = await fetch(API_BASE + path, opts);
    let data = null;
    const text = await res.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = text;
      }
    }
    const isAuthPath = path === "/auth/login" || path === "/auth/refresh" || path === "/auth/logout";
    if (res.status === 401 && allowRefresh && !isAuthPath) {
      const refreshed = await refreshAccessToken();
      if (refreshed) return api(method, path, body, timeoutMs, false);
    }
    return { ok: res.ok, status: res.status, data: data };
  } catch (err) {
    const aborted = err && (err.name === "AbortError" || String(err).indexOf("abort") >= 0);
    return {
      ok: false,
      status: 0,
      data: {
        detail: aborted
          ? "TIMEOUT: el servidor no respondió a tiempo"
          : "NETWORK: " + (err && err.message ? err.message : String(err)),
      },
    };
  } finally {
    clearTimeout(timer);
  }
}

function formatError(data) {
  if (!data) return "(sin cuerpo)";
  if (typeof data === "string") return data;
  if (data.detail && typeof data.detail === "object") {
    const d = data.detail;
    return (d.decision || "DENY") + " · " + (d.reason_code || JSON.stringify(d));
  }
  if (data.detail) {
    const detail = String(data.detail);
    if (detail === "Method Not Allowed") {
      return "Método incorrecto. Use la pantalla /ui/ (login es POST JSON).";
    }
    return detail;
  }
  return JSON.stringify(data, null, 2);
}

applyStoredTokens();

window.SigaApi = {
  api: api,
  authHeaders: authHeaders,
  formatError: formatError,
  state: state,
  API_BASE: API_BASE,
  SESSION_KEY: SESSION_KEY,
  saveSession: saveSession,
  loadSession: loadSession,
  clearSession: clearSession,
  savePanel: savePanel,
  loadPanel: loadPanel,
  applyStoredTokens: applyStoredTokens,
  refreshAccessToken: refreshAccessToken,
};
