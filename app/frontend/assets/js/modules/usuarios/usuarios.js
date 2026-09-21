/* global SigaApi, SigaAuth, SigaToast, SigaTable */
// Ref: PromptMaster FASE 9 | /users CRUD admin
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillTbody } = SigaTable;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) {
    toast("DENY: solo administrador gestiona usuarios.", "bad");
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const COLS = ["id", "username", "email", "status", "roles"];
  const el = (id) => document.getElementById(id);

  async function loadUsers() {
    const { ok, data, status } = await api("GET", "/users");
    if (!ok) {
      const msg = status === 403 ? "DENY: sin permiso users.view" : formatError(data);
      toast(msg, "bad");
      fillTbody(el("users-tbody"), [], COLS);
      return;
    }
    const rows = (Array.isArray(data) ? data : []).map((u) => ({
      id: u.id,
      username: u.username,
      email: u.email,
      status: u.status,
      roles: (u.roles || []).join(", "),
    }));
    fillTbody(el("users-tbody"), rows, COLS);
  }

  async function createUser(ev) {
    ev.preventDefault();
    const body = {
      username: (el("u-username").value || "").trim(),
      email: (el("u-email").value || "").trim(),
      password: el("u-password").value || "",
      role_codes: [el("u-role").value || "STUDENT"],
    };
    const out = el("user-create-out");
    const { ok, status, data } = await api("POST", "/users", body);
    if (!ok) {
      const msg =
        status === 403
          ? "DENY: solo el administrador puede dar de alta usuarios."
          : formatError(data);
      if (out) out.textContent = msg;
      toast(msg, "bad");
      return;
    }
    if (out) out.textContent = "Usuario " + data.username + " creado (id " + data.id + ").";
    toast("Usuario creado.", "ok");
    ev.target.reset();
    await loadUsers();
  }

  async function patchStatus() {
    const id = Number(el("m-user-id")?.value || 0);
    const statusVal = el("m-status")?.value;
    const out = el("user-manage-out");
    if (!id) {
      toast("Indica user id.", "bad");
      return;
    }
    const { ok, data } = await api("PATCH", `/users/${id}/status`, { status: statusVal });
    const msg = ok ? "Estado actualizado." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadUsers();
  }

  async function assignRoles() {
    const id = Number(el("m-user-id")?.value || 0);
    const raw = el("m-roles")?.value || "";
    const role_codes = raw
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);
    const out = el("user-manage-out");
    if (!id || !role_codes.length) {
      toast("Indica user id y al menos un rol.", "bad");
      return;
    }
    const { ok, data } = await api("PUT", `/users/${id}/roles`, { role_codes });
    const msg = ok ? "Roles asignados." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadUsers();
  }

  async function softDelete() {
    const id = Number(el("m-user-id")?.value || 0);
    const out = el("user-manage-out");
    if (!id) {
      toast("Indica user id.", "bad");
      return;
    }
    if (!window.confirm("¿Dar de baja lógica al usuario " + id + "?")) return;
    const { ok, data } = await api("DELETE", `/users/${id}`);
    const msg = ok ? "Usuario en baja lógica." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadUsers();
  }

  el("user-create-form")?.addEventListener("submit", (e) => createUser(e));
  el("btn-refresh-users")?.addEventListener("click", () => loadUsers());
  el("btn-user-status")?.addEventListener("click", () => patchStatus());
  el("btn-user-roles")?.addEventListener("click", () => assignRoles());
  el("btn-user-delete")?.addEventListener("click", () => softDelete());

  await loadUsers();
})();
