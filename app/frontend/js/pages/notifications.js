// Ref: K-022 | Notifications page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError } = SigaApi;
  const { $, toast, escapeHtml } = SigaUi;

  async function loadNotifications() {
    const { ok, data } = await api("GET", "/notifications");
    const list = $("notif-list");
    if (!ok) {
      list.innerHTML = `<p class="empty-state mb-0">${formatError(data)}</p>`;
      toast(formatError(data), "bad");
      return;
    }
    if (!Array.isArray(data) || !data.length) {
      list.innerHTML = `<p class="empty-state mb-0">No tienes avisos.</p>`;
      return;
    }
    list.innerHTML = data
      .map(
        (n) => `
      <div class="notif-item ${n.read_flag ? "read" : ""}">
        <div class="d-flex justify-content-between gap-2">
          <strong>${escapeHtml(n.title || n.type)}</strong>
          <span class="small text-secondary">${escapeHtml(n.type || "")}</span>
        </div>
        <div class="small mt-1">${escapeHtml(n.body || "")}</div>
        ${
          n.read_flag
            ? ""
            : `<button type="button" class="btn btn-sm btn-outline-secondary mt-2" data-read="${n.id}">Marcar leída</button>`
        }
      </div>`
      )
      .join("");
    list.querySelectorAll("[data-read]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-read");
        await api("PUT", `/notifications/${id}/read`);
        await loadNotifications();
      });
    });
  }

  $("btn-refresh-notif")?.addEventListener("click", () => loadNotifications());
  await loadNotifications();
})();
