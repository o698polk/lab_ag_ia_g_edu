/* global SigaApi, SigaAuth, SigaToast */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  const isAdmin = roles.includes("ADMINISTRATOR");

  async function loadNotifications() {
    const unreadOnly = document.getElementById("filt-unread")?.checked;
    const qs = unreadOnly ? "?unread_only=true" : "";
    const { ok, data } = await api("GET", "/notifications" + qs);
    const list = document.getElementById("notif-list");
    const empty = document.getElementById("notif-empty");
    const tpl = document.getElementById("notif-item-tpl");
    list.querySelectorAll(".notif-item").forEach((n) => n.remove());
    if (!ok) {
      if (empty) {
        empty.textContent = formatError(data);
        empty.classList.remove("d-none");
      }
      toast(formatError(data), "bad");
      return;
    }
    if (!Array.isArray(data) || !data.length) {
      if (empty) {
        empty.textContent = unreadOnly ? "No hay avisos sin leer." : "No tienes avisos.";
        empty.classList.remove("d-none");
      }
      return;
    }
    if (empty) empty.classList.add("d-none");
    data.forEach((n) => {
      const node = tpl.content.cloneNode(true);
      const root = node.querySelector(".notif-item");
      if (n.read_flag) root.classList.add("read");
      root.querySelector('[data-field="title"]').textContent = n.title || n.type || "";
      root.querySelector('[data-field="type"]').textContent = n.type || "";
      root.querySelector('[data-field="body"]').textContent = n.body || "";
      const btn = root.querySelector('[data-action="read"]');
      if (!n.read_flag) {
        btn.classList.remove("d-none");
        btn.addEventListener("click", async () => {
          const res = await api("PUT", "/notifications/" + n.id + "/read");
          if (!res.ok) {
            toast(formatError(res.data), "bad");
            return;
          }
          toast("Marcada como leída", "ok");
          await loadNotifications();
        });
      }
      list.appendChild(node);
    });
  }

  async function wireAdminCreate() {
    const panel = document.getElementById("admin-create-notif");
    if (!panel || !isAdmin) return;
    panel.classList.remove("d-none");

    const sel = document.getElementById("ntf-user");
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

    document.getElementById("notif-create-form")?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const userId = Number(document.getElementById("ntf-user").value);
      const type = document.getElementById("ntf-type").value;
      const title = document.getElementById("ntf-title").value.trim();
      const body = document.getElementById("ntf-body").value.trim();
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
      toast("Aviso creado", "ok");
      ev.target.reset();
      await loadNotifications();
    });
  }

  document.getElementById("btn-refresh-notif")?.addEventListener("click", () => loadNotifications());
  document.getElementById("filt-unread")?.addEventListener("change", () => loadNotifications());
  await wireAdminCreate();
  await loadNotifications();
})();
