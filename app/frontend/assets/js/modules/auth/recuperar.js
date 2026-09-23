/* global SigaApi, SigaToast */
(function () {
  const { api, formatError } = SigaApi;
  const toast = SigaToast.toast;
  const el = (id) => document.getElementById(id);

  const params = new URLSearchParams(location.search);
  if (params.get("token") && el("reset-token")) {
    el("reset-token").value = params.get("token");
  }

  el("forgot-form")?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const username = (el("forgot-username")?.value || "").trim();
    const out = el("forgot-out");
    const box = el("reset-token-box");
    if (!username) {
      toast("Indica usuario o correo.", "bad");
      return;
    }
    const { ok, data } = await api("POST", "/auth/forgot-password", { username }, 15000, false);
    if (!ok) {
      const msg = formatError(data);
      if (out) out.textContent = msg;
      toast(msg, "bad");
      return;
    }
    if (out) {
      out.textContent = data.reset_token
        ? "Solicitud aceptada. Token de laboratorio listo para pegar abajo."
        : "Si la cuenta existe, el restablecimiento fue aceptado.";
    }
    if (box) {
      if (data.reset_token) {
        box.textContent = data.reset_token;
        box.classList.remove("d-none");
        if (el("reset-token")) el("reset-token").value = data.reset_token;
      } else {
        box.classList.add("d-none");
      }
    }
    toast("Solicitud enviada.", "ok");
  });

  el("reset-form")?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const token = (el("reset-token")?.value || "").trim();
    const new_password = el("reset-password")?.value || "";
    const out = el("reset-out");
    if (token.length < 10 || new_password.length < 8) {
      toast("Token y contraseña (mín. 8) son obligatorios.", "bad");
      return;
    }
    const { ok, data } = await api(
      "POST",
      "/auth/reset-password",
      { token, new_password },
      15000,
      false
    );
    const msg = ok ? "Contraseña restablecida. Ya puedes iniciar sesión." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) ev.target.reset();
  });
})();
