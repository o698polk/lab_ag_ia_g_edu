/* global SigaApi, SigaAuth, SigaToast, SigaTable */
// Ref: PromptMaster FASE 4 | GET /dashboard, /notifications, /me/history
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const { fillTbody } = SigaTable;
  const VIEW = {
    ADMINISTRATOR: "administrador",
    TEACHER: "docente",
    STUDENT: "estudiante",
  };

  function paintWelcome(roleView) {
    const user = state.user || {};
    const badge = document.getElementById("role-badge");
    const title = document.getElementById("welcome-title");
    const hint = document.getElementById("welcome-hint");
    const name = user.full_name || user.username || "usuario";
    if (badge) badge.textContent = "Vista de " + (VIEW[roleView] || roleView);
    if (title) title.textContent = "Hola, " + name;
    if (hint) {
      hint.textContent =
        "Indicadores del servidor para rol " +
        (VIEW[roleView] || roleView) +
        ". La UI no autoriza.";
    }
  }

  function paintIndicators(indicators) {
    const empty = document.getElementById("dash-empty");
    const loading = document.getElementById("dash-loading");
    if (loading) loading.classList.add("d-none");
    let shown = 0;
    document.querySelectorAll("[data-metric]").forEach((card) => {
      const key = card.getAttribute("data-metric");
      if (Object.prototype.hasOwnProperty.call(indicators, key)) {
        card.classList.remove("d-none");
        const v = card.querySelector("[data-value]");
        if (v) v.textContent = String(indicators[key]);
        shown += 1;
      } else {
        card.classList.add("d-none");
      }
    });
    if (empty) empty.classList.toggle("d-none", shown > 0);
  }

  async function loadDashboard() {
    const loading = document.getElementById("dash-loading");
    if (loading) {
      loading.textContent = "Cargando indicadores…";
      loading.classList.remove("d-none");
    }
    const { ok, data } = await api("GET", "/dashboard");
    if (!ok) {
      if (loading) loading.classList.add("d-none");
      const badge = document.getElementById("role-badge");
      if (badge) badge.textContent = formatError(data);
      toast(formatError(data), "bad");
      return;
    }
    paintWelcome(data.role_view);
    paintIndicators(data.indicators || {});
  }

  async function loadRecentNotifications() {
    const tbody = document.getElementById("dash-notif-tbody");
    const empty = document.getElementById("dash-notif-empty");
    if (!tbody) return;
    const { ok, data } = await api("GET", "/notifications");
    if (!ok) {
      fillTbody(tbody, [], ["title", "type", "status"]);
      if (empty) {
        empty.textContent = formatError(data);
        empty.classList.remove("d-none");
      }
      return;
    }
    const items = Array.isArray(data) ? data.slice(0, 5) : [];
    if (!items.length) {
      fillTbody(tbody, [], ["title", "type", "status"]);
      if (empty) {
        empty.textContent = "No tienes avisos.";
        empty.classList.remove("d-none");
      }
      return;
    }
    if (empty) empty.classList.add("d-none");
    fillTbody(
      tbody,
      items.map((n) => ({
        title: n.title || n.type || "",
        type: n.type || "",
        status: n.read_flag ? "Leído" : "No leído",
      })),
      ["title", "type", "status"]
    );
  }

  async function loadHistory() {
    const tbody = document.getElementById("history-tbody");
    const { ok, data } = await api("GET", "/me/history");
    if (!ok) {
      fillTbody(tbody, [], ["action", "module", "summary", "created_at"]);
      const empty = tbody?.closest(".table-wrap")?.querySelector("[data-empty]");
      if (empty) {
        empty.textContent = formatError(data);
        empty.classList.remove("d-none");
      }
      return;
    }
    const rows = (Array.isArray(data) ? data : [])
      .slice(0, 8)
      .map((h) => ({
        action: h.action || "",
        module: h.module || "",
        summary: h.summary || "",
        created_at: h.created_at
          ? String(h.created_at).replace("T", " ").slice(0, 19)
          : "",
      }));
    fillTbody(tbody, rows, ["action", "module", "summary", "created_at"]);
  }

  async function refreshAll() {
    await Promise.all([loadDashboard(), loadRecentNotifications(), loadHistory()]);
  }

  document.getElementById("btn-refresh-dash")?.addEventListener("click", () => {
    refreshAll().catch(() => toast("No se pudo actualizar el dashboard", "bad"));
  });

  await refreshAll();
})();
