/* global SigaApi, SigaAuth, SigaToast, SigaModal, SigaAdminTable */
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

  const COLS = ["id", "username", "email", "status", "roles"];
  const el = (id) => document.getElementById(id);
  let cache = [];

  const table = SigaAdminTable.bind({
    tbody: el("users-tbody"),
    columns: COLS,
    searchInput: el("admin-search"),
    filterInput: el("admin-filter"),
    pager: el("admin-pager"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit", "del"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") openView(row);
      if (act === "edit") openEdit(row);
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
      username: u.username,
      email: u.email,
      status: u.status,
      roles: (u.roles || []).join(", "),
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
        "</dd><dt>Usuario</dt><dd>" +
        SigaModal.escapeHtml(row.username) +
        "</dd><dt>Correo</dt><dd>" +
        SigaModal.escapeHtml(row.email) +
        "</dd><dt>Estado</dt><dd>" +
        SigaModal.escapeHtml(row.status) +
        "</dd><dt>Roles</dt><dd>" +
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
    if (el("m-status")) el("m-status").value = row.status;
    if (el("m-roles")) el("m-roles").value = row.roles;
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
  el("btn-user-status")?.addEventListener("click", () => patchStatus());
  el("btn-user-roles")?.addEventListener("click", () => assignRoles());
  el("btn-user-delete")?.addEventListener("click", () => {
    SigaModal.confirmDelete("¿Está seguro de que desea eliminar este registro?", async () => {
      await softDelete();
    });
  });

  await loadUsers();
})();
