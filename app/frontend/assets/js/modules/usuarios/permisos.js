/* global SigaApi, SigaAuth, SigaToast, SigaModal, SigaAdminTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) {
    location.replace("/ui/pages/dashboard/dashboard.html");
    return;
  }

  const COLS = ["id", "name", "code", "module", "description", "is_active"];
  const el = (id) => document.getElementById(id);
  let cache = [];

  const table = SigaAdminTable.bind({
    tbody: el("perms-page-tbody"),
    columns: COLS,
    searchInput: el("admin-search"),
    filterInput: el("admin-filter"),
    filterKey: "is_active",
    pager: el("admin-pager"),
    actions: () => SigaAdminTable.actionButtons(["view", "edit", "del"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de permiso",
          body: SigaModal.viewDl(COLS.map((k) => [k, row[k]])),
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") openEdit(row);
      if (act === "del") {
        SigaModal.confirmDelete("¿Está seguro de que desea eliminar este registro?", async () => {
          const { ok, data } = await api("DELETE", "/permissions/" + row.id);
          toast(ok ? "Registro eliminado correctamente." : formatError(data), ok ? "ok" : "bad");
          if (ok) await loadList();
        });
      }
    },
  });

  function slugCode(name) {
    return String(name || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, ".")
      .replace(/^\.|\.$/g, "")
      .slice(0, 128);
  }

  function mapped(list) {
    return list.map((p) => ({
      id: p.id,
      name: p.description || p.code,
      code: p.code,
      module: p.module,
      description: p.description || "",
      is_active: p.is_active === false ? "INACTIVE" : "ACTIVE",
    }));
  }

  async function loadList() {
    const { ok, data } = await api("GET", "/permissions");
    if (!ok) {
      toast(formatError(data), "bad");
      table.setRows([]);
      return;
    }
    cache = Array.isArray(data) ? data : [];
    table.setRows(mapped(cache));
  }

  function openCreate() {
    const wrap = el("perm-create-wrap");
    const form = el("perm-create-form");
    if (!wrap || !form) return;
    form.reset();
    const dlg = SigaModal.openParked({
      title: "Nuevo permiso",
      node: wrap,
      footer: SigaModal.footerCancelSave("Guardar", "perm-create-form"),
    });
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      const name = (el("p-name")?.value || "").trim();
      const code = (el("p-code")?.value || "").trim() || slugCode(name);
      const { ok, data } = await api("POST", "/permissions", {
        code,
        module: (el("p-module")?.value || "").trim(),
        description: (el("p-desc")?.value || "").trim() || name,
      });
      const msg = ok ? "Registro creado correctamente." : formatError(data);
      if (el("perm-create-out")) el("perm-create-out").textContent = msg;
      toast(msg, ok ? "ok" : "bad");
      if (ok) {
        form.reset();
        dlg.close();
        await loadList();
      }
    };
  }

  function openEdit(row) {
    if (el("p-edit-id")) el("p-edit-id").value = row.id;
    if (el("p-edit-name")) el("p-edit-name").value = row.description || row.name || "";
    if (el("p-edit-module")) el("p-edit-module").value = row.module || "";
    if (el("p-edit-status")) el("p-edit-status").value = row.is_active === "INACTIVE" ? "false" : "true";
    const wrap = el("perm-edit-wrap");
    if (!wrap) return;
    SigaModal.openParked({
      title: "Editar permiso · ID " + row.id,
      node: wrap,
      footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
    });
  }

  async function saveEdit() {
    const id = Number(el("p-edit-id")?.value || 0);
    if (!id) return;
    const { ok, data } = await api("PATCH", "/permissions/" + id, {
      description: (el("p-edit-name")?.value || "").trim(),
      module: (el("p-edit-module")?.value || "").trim(),
      is_active: el("p-edit-status")?.value !== "false",
    });
    toast(ok ? "Registro actualizado correctamente." : formatError(data), ok ? "ok" : "bad");
    if (ok) {
      SigaModal.close();
      await loadList();
    }
  }

  el("btn-new-record")?.addEventListener("click", () => openCreate());
  el("btn-refresh-perms")?.addEventListener("click", () => loadList());
  el("btn-perm-save")?.addEventListener("click", () => saveEdit());
  el("p-name")?.addEventListener("input", () => {
    if (el("p-code") && !el("p-code").value) el("p-code").value = slugCode(el("p-name").value);
  });

  await loadList();
})();
