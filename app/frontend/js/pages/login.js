// Ref: K-022 | Login page — POST /auth/login then navigate to dashboard.html
/* global SigaApi, SigaUi, SigaAuth */

(function () {
  const { api, saveSession, state, formatError } = SigaApi;
  const { $, toast } = SigaUi;

  if (window.SigaAuth) SigaAuth.redirectIfAuthed();

  function showErr(msg) {
    const el = $("login-error");
    if (!el) return;
    el.textContent = msg || "";
    el.classList.toggle("d-none", !msg);
  }
  function showStatus(msg) {
    const el = $("login-status");
    if (!el) return;
    el.textContent = msg || "";
    el.classList.toggle("d-none", !msg);
  }

  function friendly(status, data) {
    const raw = formatError(data);
    if (status === 0 || String(raw).includes("TIMEOUT") || String(raw).includes("NETWORK")) {
      return "No hay respuesta del API. Arranca start-siga.bat.";
    }
    if (status === 401) return "Credenciales incorrectas. Verifica tu usuario y contraseña.";
    if (status === 403) return "La cuenta está inactiva.";
    if (status === 429) return "Demasiados intentos. Espera un minuto.";
    if (status === 422) return "Credenciales inválidas. Completa usuario y contraseña.";
    return raw || "No se pudo iniciar sesión.";
  }

  async function doLogin() {
    if (window.__sigaLoggingIn) return;
    window.__sigaLoggingIn = true;
    const btn = $("btn-login");
    const username = (($("username") && $("username").value) || "").trim();
    const password = ($("password") && $("password").value) || "";
    showErr("");
    showStatus("Conectando…");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Entrando…";
    }
    try {
      if (!username || !password) {
        showStatus("");
        showErr("Completa usuario y contraseña.");
        return;
      }
      const res = await api("POST", "/auth/login", { username, password }, 15000, false);
      if (!res.ok) {
        showStatus("");
        showErr(friendly(res.status, res.data));
        return;
      }
      if (!res.data || !res.data.access_token) {
        showStatus("");
        showErr("El servidor no devolvió token.");
        return;
      }
      state.accessToken = res.data.access_token;
      state.refreshToken = res.data.refresh_token || null;
      saveSession(state.accessToken, state.refreshToken);
      const me = await api("GET", "/auth/me", undefined, 8000, false);
      if (!me.ok || !me.data) {
        showStatus("");
        showErr("Login OK pero /auth/me falló (" + me.status + ").");
        return;
      }
      state.user = me.data;
      location.assign("/ui/pages/dashboard.html");
    } catch (err) {
      showStatus("");
      showErr("No hay respuesta del API. " + (err && err.message ? err.message : ""));
    } finally {
      window.__sigaLoggingIn = false;
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Entrar";
      }
    }
  }

  document.querySelectorAll(".role-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      $("username").value = btn.dataset.user || "";
      $("password").value = btn.dataset.pass || "";
      document.querySelectorAll(".role-chip").forEach((c) => c.classList.toggle("active", c === btn));
    });
  });
  $("btn-login")?.addEventListener("click", () => doLogin());
  $("login-form")?.addEventListener("submit", (ev) => {
    ev.preventDefault();
    doLogin();
  });
  $("btn-health")?.addEventListener("click", async () => {
    const res = await api("GET", "/health");
    toast(res.ok ? "El servicio responde." : "El servicio no respondió.", res.ok ? "ok" : "bad");
  });
})();
