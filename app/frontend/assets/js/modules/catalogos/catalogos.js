/* global SigaApi, SigaAuth, SigaToast, SigaTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError } = SigaApi;
  const { fillTbody, COL_LABEL } = SigaTable;
  const toast = SigaToast.toast;

  async function loadCatalog(path, cols) {
    const { ok, data } = await api("GET", path);
    const theadRow = document.getElementById("catalog-thead-row");
    const tbody = document.getElementById("catalog-tbody");
    if (!ok) {
      toast(formatError(data), "bad");
      fillTbody(tbody, []);
      return;
    }
    const rows = Array.isArray(data) ? data : [data];
    const keys = cols && cols.length ? cols : Object.keys(rows[0] || { id: 1 });
    if (theadRow) {
      theadRow.innerHTML = keys.map((k) => `<th>${COL_LABEL[k] || k}</th>`).join("");
    }
    fillTbody(tbody, rows, keys);
  }

  async function createLabUser() {
    const username = (document.getElementById("reg-username")?.value || "").trim();
    const email = (document.getElementById("reg-email")?.value || "").trim();
    const password = document.getElementById("reg-password")?.value || "";
    const role = document.getElementById("reg-role")?.value || "STUDENT";
    const out = document.getElementById("reg-out");
    if (!username || !email || !password) {
      if (out) out.textContent = "Completa usuario, correo y contraseña.";
      toast("Completa los campos de alta.", "bad");
      return;
    }
    const { ok, status, data } = await api("POST", "/users", {
      username, email, password, role_codes: [role],
    });
    if (!ok) {
      const msg = status === 403 ? "DENY: solo el administrador puede dar de alta usuarios." : formatError(data);
      if (out) out.textContent = msg;
      toast(msg, "bad");
      return;
    }
    if (out) out.textContent = `Usuario ${data.username} creado (id ${data.id}).`;
    toast("Registro procesado correctamente.", "ok");
    await loadCatalog("/users", ["id", "username", "email", "status"]);
  }

  document.querySelectorAll(".catalog-load").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cols = (btn.dataset.cols || "").split(",").map((c) => c.trim()).filter(Boolean);
      loadCatalog(btn.dataset.path, cols);
    });
  });
  document.getElementById("btn-create-user")?.addEventListener("click", () => createLabUser());
})();
