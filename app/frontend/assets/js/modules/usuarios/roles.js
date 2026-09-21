/* global SigaApi, SigaAuth, SigaToast, SigaTable */
// Ref: PromptMaster FASE 9 | /roles /permissions
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const { fillTbody, fillSelect } = SigaTable;
  const toast = SigaToast.toast;
  const rolesUser = (state.user && state.user.roles) || [];
  if (!rolesUser.includes("ADMINISTRATOR")) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const ROLE_COLS = ["id", "code", "name", "is_active", "permissions"];
  const PERM_COLS = ["id", "code", "module", "description"];
  const el = (id) => document.getElementById(id);
  let rolesCache = [];

  async function loadRoles() {
    const { ok, data } = await api("GET", "/roles");
    if (!ok) {
      toast(formatError(data), "bad");
      fillTbody(el("roles-tbody"), [], ROLE_COLS);
      return;
    }
    rolesCache = Array.isArray(data) ? data : [];
    const rows = rolesCache.map((r) => ({
      id: r.id,
      code: r.code,
      name: r.name,
      is_active: r.is_active ? "sí" : "no",
      permissions: (r.permissions || []).join(", "),
    }));
    fillTbody(el("roles-tbody"), rows, ROLE_COLS);
    fillSelect(el("role-code"), rolesCache, (r) => r.code + " — " + r.name, (r) => r.code);
    const selected = el("role-code")?.value;
    const role = rolesCache.find((r) => r.code === selected);
    if (role && el("perm-codes")) {
      el("perm-codes").value = (role.permissions || []).join(", ");
    }
  }

  async function loadPermissions() {
    const { ok, data } = await api("GET", "/permissions");
    if (!ok) {
      toast(formatError(data), "bad");
      fillTbody(el("perms-tbody"), [], PERM_COLS);
      return;
    }
    fillTbody(el("perms-tbody"), Array.isArray(data) ? data : [], PERM_COLS);
  }

  async function assignPermissions() {
    const role_code = el("role-code")?.value;
    const permission_codes = (el("perm-codes")?.value || "")
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    const out = el("role-assign-out");
    if (!role_code) {
      toast("Selecciona un rol.", "bad");
      return;
    }
    const { ok, data } = await api("PUT", `/roles/${encodeURIComponent(role_code)}/permissions`, {
      permission_codes,
    });
    const msg = ok
      ? "Permisos actualizados (" + (data.permissions || []).length + ")."
      : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadRoles();
  }

  el("btn-refresh-roles")?.addEventListener("click", async () => {
    await Promise.all([loadRoles(), loadPermissions()]);
  });
  el("btn-assign-perms")?.addEventListener("click", () => assignPermissions());
  el("role-code")?.addEventListener("change", () => {
    const role = rolesCache.find((r) => r.code === el("role-code").value);
    if (role && el("perm-codes")) el("perm-codes").value = (role.permissions || []).join(", ");
  });

  await Promise.all([loadRoles(), loadPermissions()]);
})();
