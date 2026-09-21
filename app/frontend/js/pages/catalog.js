// Ref: K-022 | Catalog page (admin)
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError } = SigaApi;
  const { $, toast, renderTable } = SigaUi;

  async function loadCatalog(path) {
    const { ok, data } = await api("GET", path);
    if (!ok) {
      $("catalog-table").innerHTML = `<p class="empty-state mb-0">${formatError(data)}</p>`;
      toast(formatError(data), "bad");
      return;
    }
    renderTable($("catalog-table"), Array.isArray(data) ? data : [data]);
  }

  async function createLabUser() {
    const username = ($("reg-username")?.value || "").trim();
    const email = ($("reg-email")?.value || "").trim();
    const password = $("reg-password")?.value || "";
    const role = $("reg-role")?.value || "STUDENT";
    const out = $("reg-out");
    if (!username || !email || !password) {
      if (out) out.textContent = "Completa usuario, correo y contraseña.";
      toast("Completa los campos de alta.", "bad");
      return;
    }
    const { ok, status, data } = await api("POST", "/users", {
      username,
      email,
      password,
      role_codes: [role],
    });
    if (!ok) {
      const msg =
        status === 403
          ? "DENY: solo el administrador puede dar de alta usuarios."
          : formatError(data);
      if (out) out.textContent = msg;
      toast(msg, "bad");
      return;
    }
    if (out) out.textContent = `Usuario ${data.username} creado (id ${data.id}).`;
    toast("Registro procesado correctamente.", "ok");
    await loadCatalog("/users");
  }

  document.querySelectorAll(".catalog-load").forEach((btn) => {
    btn.addEventListener("click", () => loadCatalog(btn.dataset.path));
  });
  $("btn-create-user")?.addEventListener("click", () => createLabUser());
})();
