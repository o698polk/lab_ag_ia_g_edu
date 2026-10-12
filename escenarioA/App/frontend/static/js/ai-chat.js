/** SPEC-017 / SPEC-018 / SPEC-020 / SPEC-027 / SPEC-031: chat IA + typing/APA7 */
const AIChatStore = {
  conversationId: localStorage.getItem("ai_conversation_id") || null,
  pendingAction: null,
  messages: [],
  history: [],
  loading: false,
  thinking: false,
  insecureMode: false,
  _typeTimers: [],

  async loadSecurityMode() {
    try {
      const data = await API.get("/ai/security-mode");
      this.insecureMode = !!data.insecure;
    } catch {
      this.insecureMode = false;
    }
    this.renderInsecureBanners();
    return this.insecureMode;
  },

  renderInsecureBanners() {
    const ids = ["aiInsecureBanner", "floatInsecureBanner"];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (!el) continue;
      if (this.insecureMode) {
        el.classList.remove("hidden");
        el.textContent =
          "MODO LABORATORIO INSEGURO — controles del agente desactivados. No usar con datos reales.";
      } else {
        el.classList.add("hidden");
        el.textContent = "";
      }
    }
  },

  _saveId(id) {
    this.conversationId = id || null;
    if (id) localStorage.setItem("ai_conversation_id", id);
    else localStorage.removeItem("ai_conversation_id");
  },

  async loadActive() {
    const q = this.conversationId
      ? `?conversation_id=${encodeURIComponent(this.conversationId)}`
      : "";
    const data = await API.get(`/ai/conversations/active${q}`);
    this._saveId(data.id);
    this.pendingAction = data.pending_action || null;
    this.messages = (data.messages || []).filter((m) => m.role !== "tool");
    return data;
  },

  async loadHistory() {
    try {
      this.history = await API.get("/ai/conversations?limit=40");
    } catch {
      this.history = [];
    }
    this.renderHistory();
    return this.history;
  },

  async newConversation() {
    const data = await API.post("/ai/conversations", {});
    this._saveId(data.id);
    this.pendingAction = null;
    this.messages = [];
    this.renderAll();
    await this.loadHistory();
    toast("Nueva conversación — la anterior quedó en el historial", "success");
    return data;
  },

  async openConversation(id) {
    if (!id || this.loading) return null;
    this.loading = true;
    try {
      const data = await API.post(`/ai/conversations/${encodeURIComponent(id)}/open`, {});
      this._saveId(data.id);
      this.pendingAction = data.pending_action || null;
      this.messages = (data.messages || []).filter((m) => m.role !== "tool");
      this.renderAll();
      await this.loadHistory();
      toast("Conversación restaurada", "success");
      return data;
    } finally {
      this.loading = false;
    }
  },

  renderAll() {
    this.renderBox("aiMessages");
    this.renderBox("floatChatMessages");
    this.renderHistory();
  },

  renderHistory() {
    const box = document.getElementById("aiHistoryList");
    if (!box) return;
    if (!this.history.length) {
      box.innerHTML = `<p class="ai-history-empty">Sin conversaciones aún. Escribe un mensaje o crea una nueva.</p>`;
      return;
    }
    box.innerHTML = this.history
      .map((c) => {
        const active = c.id === this.conversationId;
        const title = esc(c.title || "Sin título");
        const when = esc((c.updated_at || c.created_at || "").slice(0, 16).replace("T", " "));
        const n = c.message_count != null ? c.message_count : 0;
        const badge = c.is_archived ? `<span class="ai-hist-badge">historial</span>` : `<span class="ai-hist-badge active">activa</span>`;
        const idEnc = encodeURIComponent(c.id);
        return `<div class="ai-history-item ${active ? "is-active" : ""}">
          <button type="button" class="ai-history-open" onclick="AIChatStore.openConversation(decodeURIComponent('${idEnc}'))" title="${title}">
            <span class="ai-hist-title">${title}</span>
            <span class="ai-hist-meta">${badge} · ${n} msg · ${when || "—"}</span>
          </button>
          <div class="ai-history-actions">
            <button type="button" class="btn-icon" title="Renombrar" onclick="AIChatStore.renameConversation(decodeURIComponent('${idEnc}'))"><i class="bi bi-pencil"></i></button>
            <button type="button" class="btn-icon danger" title="Eliminar" onclick="AIChatStore.deleteConversation(decodeURIComponent('${idEnc}'))"><i class="bi bi-trash"></i></button>
          </div>
        </div>`;
      })
      .join("");
  },

  async renameConversation(id) {
    const cur = (this.history || []).find((c) => c.id === id);
    const next = prompt("Nuevo título de la conversación:", cur?.title || "");
    if (next == null) return;
    const title = next.trim();
    if (!title) {
      toast("Título vacío", "error");
      return;
    }
    try {
      await API.patch(`/ai/conversations/${encodeURIComponent(id)}`, { title });
      toast("Conversación renombrada", "success");
      await this.loadHistory();
    } catch (err) {
      toast(err.message, "error");
    }
  },

  async deleteConversation(id) {
    if (!confirm("¿Eliminar esta conversación y sus mensajes? Esta acción no se puede deshacer.")) return;
    try {
      await API.del(`/ai/conversations/${encodeURIComponent(id)}?hard=1`);
      toast("Conversación eliminada", "success");
      if (this.conversationId === id) {
        this._saveId(null);
        this.messages = [];
        await this.newConversation();
      } else {
        await this.loadHistory();
      }
    } catch (err) {
      toast(err.message, "error");
    }
  },

  clearTypeTimers() {
    (this._typeTimers || []).forEach((id) => clearTimeout(id));
    this._typeTimers = [];
  },

  thinkingHtml() {
    return `<div class="ai-bubble bot ai-thinking" aria-live="polite" aria-busy="true">
      <span class="ai-thinking-icon" title="Pensando"><i class="bi bi-lightbulb-fill"></i></span>
      <span class="ai-thinking-label">El asistente está elaborando la respuesta</span>
      <span class="ai-typing-dots" aria-hidden="true"><span></span><span></span><span></span></span>
    </div>`;
  },

  renderBox(boxId) {
    const box = document.getElementById(boxId);
    if (!box) return;
    if (!this.messages.length && !this.thinking) {
      box.innerHTML = `<div class="ai-bubble bot">Buenos días. Puedo consultar datos, ejecutar acciones (con su confirmación) y generar reportes en PDF, Excel, JSON o Markdown. El historial se conserva: al crear una nueva conversación, la anterior permanece en el panel Historial.</div>`;
      return;
    }
    let html = this.messages.map((m) => this.bubbleHtml(m)).join("");
    if (this.thinking) html += this.thinkingHtml();
    box.innerHTML = html;
    box.scrollTop = box.scrollHeight;
  },

  /** SPEC-027: quita markdown residual en cliente (red de seguridad). */
  formatDisplayText(text) {
    let t = String(text || "");
    t = t.replace(/```[\w]*\n?([\s\S]*?)```/g, "$1");
    t = t.replace(/`([^`]+)`/g, "$1");
    t = t.replace(/\*\*([^*]+)\*\*/g, "$1");
    t = t.replace(/__([^_]+)__/g, "$1");
    t = t.replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,]|$)/g, "$1$2");
    t = t.replace(/^#{1,6}\s+/gm, "");
    let n = 0;
    t = t
      .split("\n")
      .map((line) => {
        const m = line.match(/^[\t ]*[-*•–—]\s+(.*)$/);
        if (m) {
          n += 1;
          return `${n}. ${m[1]}`;
        }
        if (!line.trim()) n = 0;
        return line;
      })
      .join("\n");
    t = t.replace(/[\u{1F300}-\u{1F9FF}\u{2700}-\u{27BF}\u{1F600}-\u{1F64F}]/gu, "");
    t = t.replace(/[★☆✦✧]+/g, "");
    t = t.replace(/\n{3,}/g, "\n\n");
    return t.trim();
  },

  /** Convierte URLs/paths de descarga en <a> clicables (tras esc). */
  linkify(text) {
    const escaped = esc(this.formatDisplayText(text) || "");
    // http(s) y paths /api/v1/ai/artifacts/<id>/download?...
    const re =
      /(https?:\/\/[^\s<>"']+|\/api\/v1\/ai\/artifacts\/\d+\/download(?:\?[^\s<>"']*)?)/g;
    return escaped.replace(re, (raw) => {
      // esc convirtió & → &amp; en query; el href HTML necesita eso
      const href = raw;
      return `<a class="ai-inline-link" href="${href}" target="_blank" rel="noopener" download>${href}</a>`;
    });
  },

  isRawToolDump(text) {
    const t = (text || "").trim();
    if (!t) return false;
    if (t.startsWith("[Tool ")) return true;
    if (t.startsWith("{") && (t.includes('"ok"') || t.includes("download_url"))) return true;
    // SPEC-023: markup DSML / invoke de tools
    if (/DSML|invoke\s+name\s*=|<\||\|>|tool_call|function_call/i.test(t)) return true;
    return false;
  },

  isSecurityBlockMessage(text, explicit) {
    if (explicit) return true;
    const t = (text || "").trim();
    if (!t) return false;
    return (
      /fue bloquead/i.test(t) ||
      /pol[ií]tica de (seguridad|m[ií]nimo privilegio)/i.test(t) ||
      /no es posible (ejecutar|cambiar roles|elevar permisos)/i.test(t) ||
      /no dispone de permisos suficientes/i.test(t)
    );
  },

  bubbleHtml(m) {
    if (m.role === "tool") return "";
    if (m.role === "assistant" && this.isRawToolDump(m.content)) {
      // SPEC-022: no mostrar dumps técnicos; si hay artifact, solo el bloque de descarga
      const art = m.artifact;
      if (!art || !art.id) return "";
      const fn = esc(art.filename || "reporte");
      const path = art.download_url || art.download_path || `/api/v1/ai/artifacts/${art.id}/download`;
      const href = esc(path);
      return `<div class="ai-bubble bot">${this.linkify(
        `Listo. Generé el reporte ${art.filename || "solicitado"}.\nDescarga: ${path}`
      )}</div>
      <div class="ai-artifact">
        <a class="btn-ghost" href="${href}" download target="_blank" rel="noopener"><i class="bi bi-download"></i> ${fn}</a>
        <div class="ai-artifact-link"><a class="ai-inline-link" href="${href}" target="_blank" rel="noopener" download>${href}</a></div>
      </div>`;
    }
    const role = m.role === "user" ? "user" : "bot";
    const blocked =
      role === "bot" && this.isSecurityBlockMessage(m.content, m.blocked);
    const blockClass = blocked ? " blocked" : "";
    let html = `<div class="ai-bubble ${role}${blockClass}">${this.linkify(m.content || "")}</div>`;
    const art = m.artifact;
    if (art && art.id) {
      const fn = esc(art.filename || "reporte");
      const path = art.download_url || art.download_path || `/api/v1/ai/artifacts/${art.id}/download`;
      const href = esc(path);
      const enc = encodeURIComponent(path);
      html += `<div class="ai-artifact">
        <a class="btn-ghost" href="${href}" download target="_blank" rel="noopener"><i class="bi bi-download"></i> ${fn}</a>
        <button type="button" class="btn-ghost" title="Copiar link" onclick="AIChatStore.copyDownloadLink(decodeURIComponent('${enc}'))"><i class="bi bi-link-45deg"></i></button>
        <div class="ai-artifact-link">
          <a class="ai-inline-link" href="${href}" target="_blank" rel="noopener" download>${href}</a>
        </div>
      </div>`;
    }
    return html;
  },

  copyDownloadLink(path) {
    const full = path.startsWith("http") ? path : `${location.origin}${path}`;
    navigator.clipboard?.writeText(full).then(
      () => toast("Link de descarga copiado", "success"),
      () => toast(full, "success")
    );
  },

  async typewriteAssistant(fullText, artifact, blocked = false) {
    const text = this.formatDisplayText(fullText || "");
    const maxAnim = 420;
    const isBlocked = this.isSecurityBlockMessage(text, blocked);
    // Textos largos: mostrar completo (sin retrasar UX)
    if (text.length > maxAnim) {
      this.messages.push({ role: "assistant", content: text, artifact, blocked: isBlocked });
      this.renderAll();
      return;
    }
    const msg = { role: "assistant", content: "", artifact, blocked: isBlocked, _typing: true };
    this.messages.push(msg);
    this.renderAll();
    const step = Math.max(12, Math.floor(text.length / 40));
    let i = 0;
    await new Promise((resolve) => {
      const tick = () => {
        i = Math.min(text.length, i + step);
        msg.content = text.slice(0, i);
        this.renderAll();
        if (i >= text.length) {
          msg._typing = false;
          resolve();
          return;
        }
        const id = setTimeout(tick, 28);
        this._typeTimers.push(id);
      };
      tick();
    });
  },

  async send(message, channel = "panel", confirm = false) {
    if (this.loading) return null;
    this.loading = true;
    this.thinking = true;
    this.clearTypeTimers();
    // Optimista: mostrar mensaje del usuario al instante + indicador
    this.messages.push({ role: "user", content: message, channel });
    this.renderAll();
    try {
      const res = await API.post("/ai/chat", {
        message,
        conversation_id: this.conversationId,
        channel,
        confirm,
      });
      if (res.conversation_id) this._saveId(res.conversation_id);
      this.pendingAction = res.pending_action || null;
      // Fuente de verdad: recargar desde BD (sin el último assistant aún para typewrite)
      await this.loadActive();
      if (res.artifacts && res.artifacts.length) {
        const last = [...this.messages].reverse().find((m) => m.role === "assistant");
        if (last) last.artifact = res.artifacts[0];
      }
      // Extraer última respuesta del asistente para efecto escribiendo
      const lastAssistant = [...this.messages].reverse().find((m) => m.role === "assistant");
      const replyText = (res.reply != null ? res.reply : lastAssistant?.content) || "";
      const art = lastAssistant?.artifact || (res.artifacts && res.artifacts[0]) || null;
      if (lastAssistant) {
        this.messages = this.messages.filter((m) => m !== lastAssistant);
      }
      this.thinking = false;
      await this.typewriteAssistant(replyText, art, !!res.blocked);
      await this.loadHistory();
      return res;
    } catch (err) {
      this.thinking = false;
      this.renderAll();
      throw err;
    } finally {
      this.thinking = false;
      this.loading = false;
    }
  },

  async downloadArtifact(id, filename, signedPath) {
    // Preferir link firmado (SPEC-021); fallback JWT
    if (signedPath) {
      window.location.href = signedPath;
      return;
    }
    await downloadAuth(new Event("click"), `/api/v1/ai/artifacts/${id}/download`);
  },
};

async function initAIChat() {
  if (!hasPerm("ai.use")) return;
  try {
    await AIChatStore.loadSecurityMode();
    await AIChatStore.loadActive();
    AIChatStore.renderAll();
    await AIChatStore.loadHistory();
  } catch (err) {
    console.warn("AI chat init:", err);
  }
}

async function sendAI(e) {
  e.preventDefault();
  const input = document.getElementById("aiInput");
  const msg = input.value.trim();
  if (!msg) return false;
  input.value = "";
  const confirm =
    !!AIChatStore.pendingAction && /^(si|sí|yes|confirma|confirmar|confirmo|ok)$/i.test(msg);
  try {
    await AIChatStore.send(msg, "panel", confirm);
  } catch (err) {
    toast(err.message, "error");
    await AIChatStore.loadActive().catch(() => {});
    AIChatStore.renderAll();
  }
  return false;
}

function initFloatChat() {
  const toggle = document.getElementById("floatChatToggle");
  const panel = document.getElementById("floatChatPanel");
  const closeBtn = document.getElementById("floatChatClose");
  const form = document.getElementById("floatChatForm");
  if (!toggle || !panel) return;

  toggle.addEventListener("click", async () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden") && hasPerm("ai.use")) {
      try {
        await AIChatStore.loadSecurityMode();
        await AIChatStore.loadActive();
        AIChatStore.renderAll();
      } catch {
        /* ignore */
      }
    }
  });
  closeBtn?.addEventListener("click", () => panel.classList.add("hidden"));

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!hasPerm("ai.use")) {
      toast("Sin permiso para usar el asistente IA", "error");
      return;
    }
    const input = document.getElementById("floatChatInput");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    const confirm =
      !!AIChatStore.pendingAction && /^(si|sí|yes|confirma|confirmar|confirmo|ok)$/i.test(msg);
    try {
      await AIChatStore.send(msg, "float", confirm);
    } catch (err) {
      toast(err.message, "error");
      await AIChatStore.loadActive().catch(() => {});
      AIChatStore.renderAll();
    }
  });
}
