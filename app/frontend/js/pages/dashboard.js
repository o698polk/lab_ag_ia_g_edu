// Ref: K-022 | Dashboard page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError } = SigaApi;
  const { $, toast, METRIC_LABEL } = SigaUi;

  const VIEW_LABEL = {
    ADMINISTRATOR: "administrador",
    TEACHER: "docente",
    STUDENT: "estudiante",
  };

  async function loadDashboard() {
    const { ok, data } = await api("GET", "/dashboard");
    if (!ok) {
      $("role-badge").textContent = formatError(data);
      $("indicators").innerHTML = `<p class="empty-state mb-0">${formatError(data)}</p>`;
      toast(formatError(data), "bad");
      return;
    }
    const view = VIEW_LABEL[data.role_view] || data.role_view;
    $("role-badge").textContent = `Vista de ${view}`;
    const entries = Object.entries(data.indicators || {});
    $("indicators").innerHTML = entries.length
      ? entries
          .map(
            ([k, v]) =>
              `<div class="col-6 col-md-3"><div class="siga-metric"><div class="label">${METRIC_LABEL[k] || k}</div><div class="value">${v}</div></div></div>`
          )
          .join("")
      : `<p class="empty-state mb-0">Sin indicadores.</p>`;
  }

  $("btn-refresh-dash")?.addEventListener("click", () => loadDashboard());
  await loadDashboard();
})();
