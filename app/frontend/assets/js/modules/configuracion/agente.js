/* global SigaApi, SigaAuth, SigaToast */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const roles = (state.user && state.user.roles) || [];
  if (!roles.includes("ADMINISTRATOR")) {
    location.replace("/ui/pages/asistente/asistente.html");
    return;
  }

  const el = (id) => document.getElementById(id);

  function paint(data) {
    const configured = Boolean(data && data.configured);
    el("ai-provider").textContent = (data && data.provider) || "deepseek";
    el("ai-status").textContent = configured ? data.status || "CONFIGURED" : "Sin configurar";
    el("ai-hint").textContent = configured ? data.key_hint || "••••" : "No registrada";
    if (el("ai-model") && data && data.model) el("ai-model").value = data.model;
    if (el("ai-base") && data && data.base_url) el("ai-base").value = data.base_url;
    if (el("ai-key")) el("ai-key").value = "";
    const last = data && data.last_validated_at;
    el("ai-last").textContent = last
      ? "Última validación: " + String(last).replace("T", " ").slice(0, 19)
      : configured
        ? "Clave guardada. Valide la conexión cuando desee."
        : "Aún no hay clave registrada.";
  }

  async function load() {
    const { ok, data } = await api("GET", "/ai/settings");
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    paint(data);
  }

  el("ai-settings-form")?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const payload = {
      model: el("ai-model")?.value.trim() || undefined,
      base_url: el("ai-base")?.value.trim() || undefined,
    };
    const key = el("ai-key")?.value.trim();
    if (key) payload.api_key = key;
    const { ok, data } = await api("PUT", "/ai/settings", payload);
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    paint(data);
    toast("Configuración guardada.", "ok");
  });

  el("btn-ai-validate")?.addEventListener("click", async () => {
    const { ok, data } = await api("POST", "/ai/settings/validate");
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    paint(data);
    toast("Conexión DeepSeek válida.", "ok");
  });

  el("btn-ai-clear")?.addEventListener("click", async () => {
    if (!window.confirm("¿Quitar la API Key de DeepSeek?")) return;
    const { ok, data } = await api("DELETE", "/ai/settings");
    if (!ok) {
      toast(formatError(data), "bad");
      return;
    }
    paint(data);
    toast("Clave eliminada.", "ok");
  });

  await load();
})();
