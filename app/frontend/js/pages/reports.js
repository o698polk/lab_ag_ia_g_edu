// Ref: K-022 | Reports page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError } = SigaApi;
  const { $, toast } = SigaUi;

  async function generateReport() {
    const body = {
      report_type: $("report-type").value,
      format: $("report-format").value,
      parameters: {},
    };
    const { ok, data } = await api("POST", "/reports", body);
    const box = $("report-out");
    if (!ok) {
      box.textContent = formatError(data);
      toast(formatError(data), "bad");
      return;
    }
    box.textContent = data.content || JSON.stringify(data, null, 2);
    toast("Reporte generado.", "ok");
  }

  async function loadReportLogs() {
    const { ok, data } = await api("GET", "/reports/logs");
    const box = $("report-out");
    if (!ok) {
      box.textContent = formatError(data);
      return;
    }
    box.textContent = JSON.stringify(data, null, 2);
  }

  $("btn-report")?.addEventListener("click", () => generateReport());
  $("btn-report-logs")?.addEventListener("click", () => loadReportLogs());
})();
