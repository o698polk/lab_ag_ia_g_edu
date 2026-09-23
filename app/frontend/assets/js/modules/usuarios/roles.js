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

  const ROLE_COLS = ["id", "name", "description", "users_count", "is_active"];
  const PERM_COLS = ["id", "name", "code", "module", "description", "is_active"];
  const el = (id) => document.getElementById(id);
  let rolesCache = [];
  let allPerms = [];

  function paintPermBoxes(selected) {
    const host = el("perm-boxes");
    if (!host) return;
    const sel = new Set(selected || []);
    const groups = {};
    allPerms.forEach((p) => {
      const mod = p.module || "general";
      if (!groups[mod]) groups[mod] = [];
      groups[mod].push(p);
    });
    host.innerHTML = Object.keys(groups)
      .sort()
      .map((mod) => {
        const items = groups[mod]
          .map((p) => {
            const checked = sel.has(p.code) ? " checked" : "";
            return (
              '<div class="form-check"><input class="form-check-input" type="checkbox" data-perm="' +
              SigaModal.escapeHtml(p.code) +
              '" id="perm-' +
              p.id +
              '"' +
              checked +
              ' /><label class="form-check-label" for="perm-' +
              p.id +
              '">' +
              SigaModal.escapeHtml(SigaTable.formatRef(p.id, p.description || p.name || p.code)) +
              "</label></div>"
            );
          })
          .join("");
        return '<p class="perm-mod">' + SigaModal.escapeHtml(mod) + "</p>" + items;
      })
      .join("");
    host.querySelectorAll("[data-perm]").forEach((box) => {
      box.addEventListener("change", syncPermCodes);
    });
    syncPermCodes();
  }

  function syncPermCodes() {
    const codes = [...document.querySelectorAll("#perm-boxes [data-perm]:checked")].map((b) =>
      b.getAttribute("data-perm")
    );
    if (el("perm-codes")) el("perm-codes").value = codes.join(", ");
  }
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
    actions: () => SigaAdminTable.actionButtons(["view", "edit", "perms", "del"]),
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
      description: r.description || "",
      users_count: r.users_count ?? 0,
      is_active: r.is_active ? "ACTIVE" : "INACTIVE",
      permissions: (r.permissions || []).join(", "),
    }));
    table.setRows(rows);
    fillSelect(el("role-code"), rolesCache, (r) => SigaTable.formatRef(r.id, r.name || r.code), (r) => r.id);
    const selected = el("role-code")?.value;
    const role = rolesCache.find((r) => String(r.id) === String(selected) || r.code === selected);
    if (role) {
      if (el("perm-codes")) el("perm-codes").value = (role.permissions || []).join(", ");
      if (el("edit-role-name")) el("edit-role-name").value = role.name || "";
      if (el("edit-role-desc")) el("edit-role-desc").value = role.description || "";
      paintPermBoxes(role.permissions || []);
    }
  }

  async function loadPermissions() {
    const { ok, data } = await api("GET", "/permissions");
    if (!ok) {
      toast(formatError(data), "bad");
      permsTable.setRows([]);
      return;
    }
    allPerms = Array.isArray(data) ? data : [];
    permsTable.setRows(
      allPerms.map((p) => ({
        ...p,
        name: p.description || p.code,
        is_active: p.is_active === false ? "INACTIVE" : "ACTIVE",
      }))
    );
    const selected = el("role-code")
      ? (rolesCache.find((r) => String(r.id) === String(el("role-code").value) || r.code === el("role-code").value) || {}).permissions || []
      : [];
    paintPermBoxes(selected);
  }

  async function assignPermissions() {
    const picked = rolesCache.find((r) => String(r.id) === String(el("role-code")?.value) || r.code === el("role-code")?.value);
    const role_code = picked ? picked.code : el("role-code")?.value;
    syncPermCodes();
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

  function slugCode(name) {
    return String(name || "")
      .toUpperCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^A-Z0-9]+/g, "_")
      .replace(/^_|_$/g, "")
      .slice(0, 64);
  }

  async function saveRoleMeta() {
    const picked = rolesCache.find((r) => String(r.id) === String(el("role-code")?.value) || r.code === el("role-code")?.value);
    const code = picked ? picked.code : el("role-code")?.value;
    if (!code) return;
    const { ok, data } = await api("PATCH", "/roles/" + encodeURIComponent(code), {
      name: (el("edit-role-name")?.value || "").trim() || undefined,
      description: (el("edit-role-desc")?.value || "").trim(),
    });
    if (!ok) toast(formatError(data), "bad");
  }

  async function createRole(ev) {
    ev.preventDefault();
    const name = (el("new-role-name")?.value || "").trim();
    const code = (el("new-role-code")?.value || "").trim() || slugCode(name);
    if (el("new-role-code")) el("new-role-code").value = code;
    const body = {
      code,
      name,
      description: (el("new-role-desc")?.value || "").trim(),
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
    const picked = rolesCache.find((r) => String(r.id) === String(el("role-code")?.value) || r.code === el("role-code")?.value);
    const code = (picked && picked.code) || el("role-code")?.value || (el("new-role-code")?.value || "").trim();
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
    const role = rolesCache.find((r) => String(r.id) === String(el("role-code").value) || r.code === el("role-code").value);
    if (role) {
      if (el("edit-role-name")) el("edit-role-name").value = role.name || "";
      if (el("edit-role-desc")) el("edit-role-desc").value = role.description || "";
      paintPermBoxes(role.permissions || []);
    }
  });
  el("new-role-name")?.addEventListener("input", () => {
    if (!el("new-role-code") || el("new-role-code").dataset.locked === "1") return;
    el("new-role-code").value = slugCode(el("new-role-name").value);
  });

  await Promise.all([loadRoles(), loadPermissions()]);
})();
