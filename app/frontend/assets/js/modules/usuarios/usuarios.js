/* global SigaApi, SigaAuth, SigaToast, SigaModal, SigaAdminTable, SigaTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) {
    toast("DENY: solo administrador gestiona usuarios.", "bad");
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const COLS = ["id", "first_name", "last_name", "username", "email", "phone", "status", "roles", "created_at"];
  const el = (id) => document.getElementById(id);
  let cache = [];
  let rolesCache = [];

  function roleLabel(role) {
    return SigaTable.formatRef(role.id, role.name || role.code);
  }

  function roleCodeFromSelect(selectId) {
    const val = el(selectId)?.value;
    const role = rolesCache.find((r) => String(r.id) === String(val) || r.code === val);
    return role ? role.code : val || "STUDENT";
  }

  async function loadRoles() {
    const { ok, data } = await api("GET", "/roles");
    rolesCache = ok && Array.isArray(data) ? data : [];
    const fill = (node) => SigaTable.fillSelect(node, rolesCache, roleLabel, (r) => r.id, "Seleccionar rol…");
    fill(el("u-role"));
    fill(el("m-roles"));
  }

  const table = SigaAdminTable.bind({
    tbody: el("users-tbody"),
    columns: COLS,
    searchInput: el("admin-search"),
    filterInput: el("admin-filter"),
    pager: el("admin-pager"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit", "toggle", "del"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") openView(row);
      if (act === "edit") openEdit(row);
      if (act === "toggle") {
        if (el("m-user-id")) el("m-user-id").value = row.id;
        if (el("m-status")) el("m-status").value = row.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
        patchStatus();
      }
      if (act === "del") {
        if (el("m-user-id")) el("m-user-id").value = row.id;
        SigaModal.confirmDelete("¿Está seguro de que desea eliminar este registro?", async () => {
          await softDelete();
        });
      }
    },
  });

  function mapped(list) {
    return list.map((u) => ({
      id: u.id,
      first_name: u.first_name || "",
      last_name: u.last_name || "",
      username: u.username,
      email: u.email,
      phone: u.phone || "",
      status: u.status,
      role_codes: u.roles || [],
      roles: (u.roles || [])
        .map((code) => {
          const role = rolesCache.find((r) => r.code === code);
          return role ? roleLabel(role) : code;
        })
        .join(", "),
      created_at: u.created_at ? String(u.created_at).replace("T", " ").slice(0, 16) : "",
    }));
  }

  async function loadUsers() {
    const { ok, data, status } = await api("GET", "/users");
    if (!ok) {
      const msg = status === 403 ? "DENY: sin permiso users.view" : formatError(data);
      toast(msg, "bad");
      table.setRows([]);
      return;
    }
    cache = Array.isArray(data) ? data : [];
    table.setRows(mapped(cache));
  }

  function openView(row) {
    SigaModal.open({
      title: "Consulta de usuario",
      body:
        "<dl class='view-dl'>" +
        "<dt>Id</dt><dd>" +
        row.id +
        "</dd><dt>Nombres</dt><dd>" +
        SigaModal.escapeHtml(row.first_name) +
        "</dd><dt>Apellidos</dt><dd>" +
        SigaModal.escapeHtml(row.last_name) +
        "</dd><dt>Usuario</dt><dd>" +
        SigaModal.escapeHtml(row.username) +
        "</dd><dt>Correo</dt><dd>" +
        SigaModal.escapeHtml(row.email) +
        "</dd><dt>Teléfono</dt><dd>" +
        SigaModal.escapeHtml(row.phone) +
        "</dd><dt>Estado</dt><dd>" +
        SigaModal.escapeHtml(row.status) +
        "</dd><dt>Rol</dt><dd>" +
        SigaModal.escapeHtml(row.roles) +
        "</dd></dl>",
      footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
    });
  }

  function openCreate() {
    const form = el("user-create-form");
    const sec = form?.closest("section");
    if (!form || !sec) return;
    const dlg = SigaModal.openParked({
      title: "Nuevo usuario",
      node: sec,
      footer: SigaModal.footerCancelSave("Guardar", "user-create-form"),
      wide: true,
    });
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      await createUser(ev);
      if (el("user-create-out")?.textContent?.includes("correctamente")) dlg.close();
    };
  }

  function openEdit(row) {
    if (el("m-user-id")) el("m-user-id").value = row.id;
    if (el("m-first-name")) el("m-first-name").value = row.first_name || "";
    if (el("m-last-name")) el("m-last-name").value = row.last_name || "";
    if (el("m-username")) el("m-username").value = row.username || "";
    if (el("m-email")) el("m-email").value = row.email || "";
    if (el("m-phone")) el("m-phone").value = row.phone || "";
    if (el("m-status")) el("m-status").value = row.status;
    if (el("m-roles")) {
      const code = (row.role_codes || [])[0];
      const role = rolesCache.find((r) => r.code === code);
      el("m-roles").value = role ? String(role.id) : "";
    }
    const manage = el("manage-title")?.closest("section");
    if (!manage) return;
    SigaModal.openParked({
      title: "Editar usuario",
      node: manage,
      footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
      wide: true,
    });
  }

  async function createUser(ev) {
    ev.preventDefault();
    const body = {
      first_name: (el("u-first-name")?.value || "").trim(),
      last_name: (el("u-last-name")?.value || "").trim(),
      username: (el("u-username").value || "").trim(),
      email: (el("u-email").value || "").trim(),
      phone: (el("u-phone")?.value || "").trim(),
      password: el("u-password").value || "",
      role_codes: [roleCodeFromSelect("u-role")],
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
    if (out) out.textContent = "Registro creado correctamente.";
    toast("Registro creado correctamente.", "ok");
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
    const msg = ok ? "Registro actualizado correctamente." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadUsers();
  }

  async function saveUser() {
    const id = Number(el("m-user-id")?.value || 0);
    if (!id) {
      toast("Seleccione un usuario.", "bad");
      return;
    }
    const body = {
      first_name: (el("m-first-name")?.value || "").trim(),
      last_name: (el("m-last-name")?.value || "").trim(),
      username: (el("m-username")?.value || "").trim(),
      email: (el("m-email")?.value || "").trim(),
      phone: (el("m-phone")?.value || "").trim(),
      status: el("m-status")?.value,
      role_codes: [roleCodeFromSelect("m-roles")],
    };
    const { ok, data } = await api("PATCH", `/users/${id}`, body);
    const msg = ok ? "Registro actualizado correctamente." : formatError(data);
    if (el("user-manage-out")) el("user-manage-out").textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadUsers();
  }

  async function assignRoles() {
    const id = Number(el("m-user-id")?.value || 0);
    const raw = roleCodeFromSelect("m-roles");
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
    const msg = ok ? "Registro actualizado correctamente." : formatError(data);
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
    const { ok, data } = await api("DELETE", `/users/${id}`);
    const msg = ok ? "Registro eliminado correctamente." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
    if (ok) await loadUsers();
  }

  async function resetPassword() {
    const id = Number(el("m-user-id")?.value || 0);
    const out = el("user-manage-out");
    if (!id) {
      toast("Indica user id.", "bad");
      return;
    }
    const pwd = window.prompt("Nueva contraseña (mín. 8):", "Temp1234!");
    if (!pwd) return;
    const { ok, data } = await api("POST", `/users/${id}/password`, { new_password: pwd });
    const msg = ok ? "Registro actualizado correctamente." : formatError(data);
    if (out) out.textContent = msg;
    toast(msg, ok ? "ok" : "bad");
  }

  el("btn-new-record")?.addEventListener("click", () => openCreate());
  el("btn-user-password")?.addEventListener("click", () => resetPassword());
  el("user-create-form")?.addEventListener("submit", (e) => createUser(e));
  el("btn-refresh-users")?.addEventListener("click", () => loadUsers());
  el("btn-user-save")?.addEventListener("click", () => saveUser());
  el("btn-user-status")?.addEventListener("click", () => patchStatus());
  el("btn-user-roles")?.addEventListener("click", () => assignRoles());
  el("btn-user-delete")?.addEventListener("click", () => {
    SigaModal.confirmDelete("¿Está seguro de que desea eliminar este registro?", async () => {
      await softDelete();
    });
  });

  await loadRoles();
  await loadUsers();
})();
