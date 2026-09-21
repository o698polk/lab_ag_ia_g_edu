/* global SigaApi, SigaAuth, SigaToast */
// Ref: PromptMaster FASE 9 | perfil + change-password
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const u = state.user;
  if (!u) return;

  const set = (id, v) => {
    const el = document.getElementById(id);
    if (el) el.textContent = v || "—";
  };
  set("pf-username", u.username);
  set("pf-email", u.email);
  set("pf-status", u.status);
  set("pf-roles", (u.roles || []).join(", "));

  const host = document.getElementById("pf-permissions");
  if (host) {
    host.innerHTML = "";
    const perms = u.permissions || [];
    if (!perms.length) {
      host.innerHTML = '<span class="role-chip">Sin permisos listados</span>';
    } else {
      perms.forEach((p) => {
        const span = document.createElement("span");
        span.className = "role-chip";
        span.textContent = p;
        host.appendChild(span);
      });
    }
  }

  document.getElementById("btn-logout-profile")?.addEventListener("click", () => SigaAuth.logout());

  document.getElementById("change-password-form")?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const current_password = document.getElementById("pwd-current")?.value || "";
    const new_password = document.getElementById("pwd-new")?.value || "";
    const out = document.getElementById("pwd-out");
    if (new_password.length < 8) {
      if (out) out.textContent = "La nueva contraseña debe tener al menos 8 caracteres.";
      toast("Contraseña demasiado corta.", "bad");
      return;
    }
    const { ok, data } = await api("POST", "/auth/change-password", {
      current_password,
      new_password,
    });
    if (!ok) {
      const msg = formatError(data);
      if (out) out.textContent = msg;
      toast(msg, "bad");
      return;
    }
    if (out) out.textContent = "Contraseña actualizada.";
    toast("Contraseña actualizada.", "ok");
    ev.target.reset();
  });
})();
