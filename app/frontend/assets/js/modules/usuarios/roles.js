/* global SigaApi, SigaAuth, SigaToast, SigaTable, SigaModal, SigaAdminTable */
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
  const permsTable = SigaAdminTable.bind({
    tbody: el("perms-tbody"),
    columns: PERM_COLS,
    searchInput: el("admin-search"),
    pager: el("pager-perms"),
    actions: () => SigaAdminTable.actionButtons(["view"]),
    onAction: (act, row) => {
      if (act !== "view" || !row) return;
      SigaModal.open({
        title: "Consulta de permiso",
        body: SigaModal.viewDl(PERM_COLS.map((k) => [k, row[k]])),
        footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
      });
    },
  });
  const table = SigaAdminTable.bind({
    tbody: el("roles-tbody"),
    columns: ROLE_COLS,
    searchInput: el("admin-search"),
    pager: el("admin-pager"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit", "del"]),
    onAction: (act, row) => {
      if (!row) return;
      if (el("role-code")) el("role-code").value = row.code;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de rol",
          body:
            "<dl class='view-dl'><dt>Código</dt><dd>" +
            SigaModal.escapeHtml(row.code) +
            "</dd><dt>Nombre</dt><dd>" +
            SigaModal.escapeHtml(row.name) +
            "</dd><dt>Activo</dt><dd>" +
            SigaModal.escapeHtml(row.is_active) +
            "</dd><dt>Permisos</dt><dd>" +
            SigaModal.escapeHtml(row.permissions) +
            "</dd></dl>",
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") {
        const sec = el("assign-perm-title")?.closest("section");
        if (!sec) return;
        SigaModal.openParked({
          title: "Editar permisos",
          node: sec,
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
          wide: true,
        });
      }
      if (act === "del") {
        SigaModal.confirmDelete("¿Está seguro de que desea eliminar este registro?", async () => {
          await deactivateRole();
        });
      }
    },
  });

  async function loadRoles() {
    const { ok, data } = await api("GET", "/roles");
    if (!ok) {
      toast(formatError(data), "bad");
      table.setRows([]);
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
    table.setRows(rows);
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
      permsTable.setRows([]);
      return;
    }
    permsTable.setRows(Array.isArray(data) ? data : []);
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

  async function createRole(ev) {
    ev.preventDefault();
    const body = {
      code: (el("new-role-code")?.value || "").trim(),
      name: (el("new-role-name")?.value || "").trim(),
    };
    const { ok, data } = await api("POST", "/roles", body);
    const msg = ok ? "Registro creado correctamente." : formatError(data);
    if (el("role-create-out")) el("role-create-out").textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) {
      ev.target.reset();
      await loadRoles();
      SigaModal.close();
    }
  }

  async function deactivateRole() {
    const code = el("role-code")?.value || (el("new-role-code")?.value || "").trim();
    if (!code) {
      toast("Selecciona un rol.", "bad");
      return;
    }
    const { ok, data } = await api("DELETE", "/roles/" + encodeURIComponent(code));
    const msg = ok ? "Registro eliminado correctamente." : formatError(data);
    if (el("role-create-out")) el("role-create-out").textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadRoles();
  }

  el("btn-new-record")?.addEventListener("click", () => {
    const form = el("role-create-form");
    const sec = form?.closest("section");
    if (!sec) return;
    const dlg = SigaModal.openParked({
      title: "Nuevo rol",
      node: sec,
      footer: SigaModal.footerCancelSave("Guardar", "role-create-form"),
    });
    form.onsubmit = async (e) => {
      await createRole(e);
      if (el("role-create-out")?.textContent?.includes("correctamente")) dlg.close();
    };
  });
  el("role-create-form")?.addEventListener("submit", (e) => createRole(e));
  el("btn-role-deactivate")?.addEventListener("click", () => deactivateRole());
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
