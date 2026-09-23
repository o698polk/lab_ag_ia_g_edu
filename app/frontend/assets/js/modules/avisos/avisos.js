/* global SigaApi, SigaAuth, SigaToast, SigaModal, SigaAdminTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  const isAdmin = roles.includes("ADMINISTRATOR");
  const el = (id) => document.getElementById(id);
  let cache = [];

  const table = SigaAdminTable.bind({
    tbody: el("notif-tbody"),
    columns: ["id", "title", "type", "status"],
    searchInput: el("admin-search"),
    pager: el("admin-pager"),
    statusKeys: ["status"],
    actions: (row) =>
      SigaAdminTable.actionButtons(row.status === "No leído" ? ["view", "edit"] : ["view"]),
    onAction: (act, row) => {
      if (!row) return;
      if (act === "view") {
        SigaModal.open({
          title: "Consulta de aviso",
          body: SigaModal.viewDl([
            ["Id", row.id],
            ["Título", row.title],
            ["Tipo", row.type],
            ["Estado", row.status],
            ["Cuerpo", row.body],
          ]),
          footer: '<button type="button" class="btn btn-outline-secondary" data-modal-close>Cerrar</button>',
        });
      }
      if (act === "edit") markRead(row.id);
    },
  });

  async function markRead(id) {
    const res = await api("PUT", "/notifications/" + id + "/read");
    if (!res.ok) {
      toast(formatError(res.data), "bad");
      return;
    }
    toast("Registro actualizado correctamente.", "ok");
    await loadNotifications();
  }

  async function loadNotifications() {
    const unreadOnly = el("filt-unread")?.checked;
    const qs = unreadOnly ? "?unread_only=true" : "";
    const empty = el("notif-empty");
    const { ok, data } = await api("GET", "/notifications" + qs);
    if (!ok) {
      if (empty) {
        empty.textContent = formatError(data);
        empty.classList.remove("d-none");
      }
      toast(formatError(data), "bad");
      table.setRows([]);
      return;
    }
    cache = Array.isArray(data) ? data : [];
    if (!cache.length && empty) {
      empty.textContent = unreadOnly ? "No hay avisos sin leer." : "No tienes avisos.";
    }
    table.setRows(
      cache.map((n) => ({
        id: n.id,
        title: n.title || n.type || "",
        type: n.type || "",
        status: n.read_flag ? "Leído" : "No leído",
        body: n.body || "",
      }))
    );
  }

  async function wireAdminCreate() {
    const panel = el("admin-create-notif");
    const btnNew = el("btn-new-record");
    if (!isAdmin || !panel) return;
    if (btnNew) btnNew.classList.remove("d-none");

    const sel = el("ntf-user");
    const { ok, data } = await api("GET", "/users");
    if (ok && Array.isArray(data) && sel) {
      sel.innerHTML = "";
      const opt0 = document.createElement("option");
      opt0.value = "";
      opt0.textContent = "Selecciona usuario…";
      sel.appendChild(opt0);
      data.forEach((u) => {
        const o = document.createElement("option");
        o.value = String(u.id);
        o.textContent = (u.username || "") + " (#" + u.id + ")";
        sel.appendChild(o);
      });
    }

    el("notif-create-form")?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const userId = Number(el("ntf-user").value);
      const type = el("ntf-type").value;
      const title = el("ntf-title").value.trim();
      const body = el("ntf-body").value.trim();
      if (!userId || !title) {
        toast("Usuario y título son obligatorios", "bad");
        return;
      }
      const res = await api("POST", "/notifications", {
        user_id: userId,
        type,
        title,
        body: body || null,
      });
      if (!res.ok) {
        toast(formatError(res.data), "bad");
        return;
      }
      toast("Registro creado correctamente.", "ok");
      ev.target.reset();
      SigaModal.close();
      await loadNotifications();
    });

    btnNew?.addEventListener("click", () => {
      SigaModal.openParked({
        title: "Nuevo aviso",
        node: panel,
        footer: SigaModal.footerCancelSave("Guardar", "notif-create-form"),
        wide: true,
      });
    });
  }

  el("btn-refresh-notif")?.addEventListener("click", () => loadNotifications());
  el("filt-unread")?.addEventListener("change", () => loadNotifications());
  await wireAdminCreate();
  await loadNotifications();
})();
