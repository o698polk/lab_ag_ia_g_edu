/* global SigaApi, SigaAuth, SigaToast, SigaTable */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError } = SigaApi;
  const { escapeHtml } = SigaTable;
  const toast = SigaToast.toast;

  async function loadNotifications() {
    const { ok, data } = await api("GET", "/notifications");
    const list = document.getElementById("notif-list");
    const empty = document.getElementById("notif-empty");
    const tpl = document.getElementById("notif-item-tpl");
    list.querySelectorAll(".notif-item").forEach((n) => n.remove());
    if (!ok) {
      if (empty) { empty.textContent = formatError(data); empty.classList.remove("d-none"); }
      toast(formatError(data), "bad");
      return;
    }
    if (!Array.isArray(data) || !data.length) {
      if (empty) { empty.textContent = "No tienes avisos."; empty.classList.remove("d-none"); }
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
          await api("PUT", `/notifications/${n.id}/read`);
          await loadNotifications();
        });
      }
      list.appendChild(node);
    });
  }

  document.getElementById("btn-refresh-notif")?.addEventListener("click", () => loadNotifications());
  await loadNotifications();
})();
