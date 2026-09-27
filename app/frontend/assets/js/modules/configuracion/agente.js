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

  async function loadGuard() {
    if (window.SigaChatbot && typeof SigaChatbot.loadGuard === "function") {
      await SigaChatbot.loadGuard();
      return;
    }
    const { ok, data } = await api("GET", "/ai/guard");
    if (!ok) return;
    const enforced = data.policies_enforced !== false;
    const label = data.label || (enforced ? "Mínimo privilegio activo" : "Políticas desactivadas");
    document.querySelectorAll("[data-guard-mode]").forEach((node) => {
      node.textContent = label;
    });
    const banner = el("ai-guard-banner");
    if (banner) {
      banner.textContent = enforced
        ? "El agente aplica políticas de mínimo privilegio y autorizaciones."
        : "Políticas desactivadas: el agente no aplica PDP ni controles de propiedad.";
      banner.classList.toggle("warn", !enforced);
    }
    if (el("btn-guard-on")) el("btn-guard-on").disabled = enforced;
    if (el("btn-guard-off")) el("btn-guard-off").disabled = !enforced;
  }

  if (el("btn-guard-on") && !el("btn-guard-on").getAttribute("data-wired")) {
    el("btn-guard-on").setAttribute("data-wired", "1");
    el("btn-guard-on").addEventListener("click", async () => {
      if (window.SigaChatbot) {
        await SigaChatbot.setGuard(true);
        return;
      }
      const { ok, data } = await api("PUT", "/ai/guard", { policies_enforced: true });
      if (!ok) {
        toast(formatError(data), "bad");
        return;
      }
      toast("Políticas de mínimo privilegio activadas.", "ok");
      await loadGuard();
    });
  }
  if (el("btn-guard-off") && !el("btn-guard-off").getAttribute("data-wired")) {
    el("btn-guard-off").setAttribute("data-wired", "1");
    el("btn-guard-off").addEventListener("click", async () => {
      if (!window.confirm("¿Desactivar políticas de mínimo privilegio y controles de seguridad del agente?")) return;
      if (window.SigaChatbot) {
        await SigaChatbot.setGuard(false);
        return;
      }
      const { ok, data } = await api("PUT", "/ai/guard", { policies_enforced: false });
      if (!ok) {
        toast(formatError(data), "bad");
        return;
      }
      toast("Políticas desactivadas para comparación.", "bad");
      await loadGuard();
    });
  }

  await load();
  await loadGuard();
})();
