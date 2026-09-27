/* global SigaApi, SigaToast */
(function () {
  if (window.SigaChatbot) return;

  var mounted = false;
  var conversationId = null;
  var sending = false;
  var LOGO = "/ui/assets/img/agent-logo.svg";
  var CONV_KEY = "siga.lab.conversation";

  function el(id) {
    return document.getElementById(id);
  }

  function isAdmin() {
    var user = window.SigaApi && SigaApi.state && SigaApi.state.user;
    var roles = (user && user.roles) || [];
    return roles.indexOf("ADMINISTRATOR") >= 0;
  }

  function canToggleGuard() {
    var user = window.SigaApi && SigaApi.state && SigaApi.state.user;
    if (!user) return false;
    if (user.can_toggle_policies !== false) return true;
    return ((user.permissions || []).indexOf("ai.use") >= 0);
  }

  function isFullChatPage() {
    return /\/asistente\/asistente\.html/i.test(location.pathname || "");
  }

  function toast(msg, kind) {
    if (window.SigaToast && SigaToast.toast) SigaToast.toast(msg, kind);
  }

  function rememberConversation(id) {
    conversationId = id || null;
    if (window.SigaApi) SigaApi.state.conversationId = conversationId;
    try {
      if (conversationId) sessionStorage.setItem(CONV_KEY, String(conversationId));
      else sessionStorage.removeItem(CONV_KEY);
    } catch (e) {
      /* ignore */
    }
  }

  function rememberedConversation() {
    if (window.SigaApi && SigaApi.state && SigaApi.state.conversationId) {
      return SigaApi.state.conversationId;
    }
    try {
      var raw = sessionStorage.getItem(CONV_KEY);
      return raw ? parseInt(raw, 10) : null;
    } catch (e) {
      return null;
    }
  }

  function paintMode(data) {
    var enforced = !data || data.policies_enforced !== false;
    var label = (data && data.label) || (enforced ? "Mínimo privilegio activo" : "Políticas desactivadas");
    var modeEls = document.querySelectorAll("[data-guard-mode]");
    modeEls.forEach(function (node) {
      node.textContent = label;
      node.classList.toggle("open", !enforced);
    });
    document.querySelectorAll("[data-guard-banner]").forEach(function (node) {
      node.textContent = enforced
        ? "El agente aplica políticas de mínimo privilegio y autorizaciones."
        : "Políticas desactivadas: el agente no aplica PDP ni controles de propiedad.";
      node.classList.toggle("warn", !enforced);
      node.classList.toggle("siga-page-banner", node.id === "ai-guard-banner");
      node.classList.toggle("siga-chat-banner", node.id !== "ai-guard-banner");
    });
    var onBtn = el("btn-guard-on");
    var offBtn = el("btn-guard-off");
    var fabOn = el("siga-chat-guard-on");
    var fabOff = el("siga-chat-guard-off");
    if (onBtn) onBtn.disabled = enforced;
    if (offBtn) offBtn.disabled = !enforced;
    if (fabOn) fabOn.disabled = enforced;
    if (fabOff) fabOff.disabled = !enforced;
  }

  async function loadGuard() {
    if (!window.SigaApi) return;
    var res = await SigaApi.api("GET", "/ai/guard");
    if (!res.ok) return;
    paintMode(res.data);
  }

  async function setGuard(enabled) {
    if (!window.SigaApi) return;
    var res = await SigaApi.api("PUT", "/ai/guard", { policies_enforced: enabled });
    if (!res.ok) {
      toast(SigaApi.formatError(res.data), "bad");
      return;
    }
    paintMode(res.data);
    window.dispatchEvent(new CustomEvent("siga-guard-changed", { detail: res.data }));
    toast(enabled ? "Políticas de mínimo privilegio activadas." : "Políticas desactivadas para comparación.", enabled ? "ok" : "bad");
  }

  function clearThread(thread) {
    if (!thread) return;
    thread.textContent = "";
    var empty = document.createElement("p");
    empty.className = "empty-state mb-0";
    empty.id = thread.id === "ai-thread" ? "ai-empty" : "siga-chat-empty";
    empty.textContent = "Pregunte por notas, asistencia o kárdex. El historial se guarda en la base de datos.";
    thread.appendChild(empty);
  }

  function paintStoredMessages(thread, messages) {
    if (!thread) return;
    clearThread(thread);
    if (!messages || !messages.length) return;
    messages.forEach(function (msg) {
      var role = msg.role === "user" ? "user" : "bot";
      appendBubble(thread, role, msg.content || "");
    });
  }

  async function loadHistory(thread) {
    if (!window.SigaApi) return;
    var saved = rememberedConversation();
    var list = await SigaApi.api("GET", "/ai/conversations");
    if (!list.ok || !list.data || !list.data.length) {
      rememberConversation(null);
      return;
    }
    var targetId = saved;
    var exists = list.data.some(function (row) { return row.id === targetId; });
    if (!exists) targetId = list.data[0].id;
    var detail = await SigaApi.api("GET", "/ai/conversations/" + targetId);
    if (!detail.ok || !detail.data) return;
    rememberConversation(detail.data.id);
    paintStoredMessages(thread, detail.data.messages);
  }

  async function startNewConversation(thread) {
    if (!window.SigaApi) return;
    var res = await SigaApi.api("POST", "/ai/conversations");
    if (!res.ok) {
      toast(SigaApi.formatError(res.data), "bad");
      return;
    }
    rememberConversation(res.data.id);
    clearThread(thread);
  }

  function cleanReply(text) {
    var out = String(text || "");
    out = out.replace(/^\[Políticas desactivadas\]\s*/i, "");
    out = out.replace(/\s*request_id=[0-9a-fA-F-]{8,}\s*/g, " ");
    return out.trim();
  }

  function appendBubble(thread, role, text, meta, decision) {
    if (!thread) return;
    var empty = thread.querySelector(".empty-state");
    if (empty) empty.classList.add("d-none");
    var div = document.createElement("div");
    var cls = decision === "DENY" ? "deny" : decision === "ALLOW" ? "allow" : "";
    div.className = ("siga-bubble " + role + " " + cls).trim();
    var body = document.createElement("div");
    body.textContent = cleanReply(text);
    div.appendChild(body);
    if (meta) {
      var m = document.createElement("div");
      m.className = "meta";
      m.textContent = meta;
      div.appendChild(m);
    }
    thread.appendChild(div);
    thread.scrollTop = thread.scrollHeight;
  }

  async function sendFromWidget(preset, caseId) {
    var input = el("siga-chat-input");
    var sendBtn = el("siga-chat-send");
    var thread = el("siga-chat-thread");
    var msg = String(preset || (input && input.value) || "").trim();
    if (!msg || sending) return;
    if (input) input.value = "";
    appendBubble(thread, "user", msg);
    sending = true;
    if (sendBtn) sendBtn.disabled = true;
    var body = { message: msg };
    if (caseId) body.case_id = caseId;
    if (conversationId) body.conversation_id = conversationId;
    try {
      var res = await SigaApi.api("POST", "/ai/chat", body, 45000);
      if (!res.ok) {
        appendBubble(thread, "bot", SigaApi.formatError(res.data), "HTTP " + res.status, "DENY");
        return;
      }
      if (res.data.conversation_id) rememberConversation(res.data.conversation_id);
      if (res.data.policies_enforced === false) {
        paintMode({ policies_enforced: false, label: "Políticas desactivadas" });
      }
      var meta =
        (res.data.scenario ? "Lab " + res.data.scenario + " · " : "") +
        (res.data.decision || "?") +
        " · " +
        (res.data.reason_code || "") +
        (res.data.policy_id ? " · " + res.data.policy_id : "");
      appendBubble(thread, "bot", res.data.reply || "(sin reply)", meta, res.data.decision);
    } finally {
      sending = false;
      if (sendBtn) sendBtn.disabled = false;
      if (input) input.focus();
    }
  }

  function buildDock() {
    if (el("siga-chat-dock")) return;
    var fab = document.createElement("button");
    fab.type = "button";
    fab.id = "siga-fab-chat";
    fab.className = "siga-fab";
    fab.setAttribute("aria-expanded", "false");
    fab.setAttribute("aria-controls", "siga-chat-dock");
    fab.setAttribute("aria-label", "Abrir agente SIGA");
    fab.title = "Agente SIGA";
    var logo = document.createElement("img");
    logo.src = LOGO;
    logo.alt = "";
    logo.width = 64;
    logo.height = 64;
    fab.appendChild(logo);
    var dock = document.createElement("div");
    dock.id = "siga-chat-dock";
    dock.className = "siga-chat-dock";
    dock.hidden = true;
    dock.setAttribute("role", "dialog");
    dock.setAttribute("aria-label", "Chat del agente SIGA");
    var adminBlock = canToggleGuard()
      ? '<div class="siga-chat-guard" id="siga-chat-guard">' +
        "<p>Compare el agente con y sin mínimo privilegio.</p>" +
        '<div class="btn-row">' +
        '<button type="button" class="btn btn-sm btn-siga" id="siga-chat-guard-on">Activar políticas</button>' +
        '<button type="button" class="btn btn-sm btn-outline-danger" id="siga-chat-guard-off">Desactivar políticas</button>' +
        "</div></div>"
      : "";
    dock.innerHTML =
      '<div class="siga-chat-head">' +
      '<div class="siga-chat-head-brand"><img src="' + LOGO + '" alt="" width="36" height="36" />' +
      "<div><strong>Agente SIGA</strong><span class=\"siga-chat-mode\" data-guard-mode>Mínimo privilegio activo</span></div></div>" +
      '<div><button type="button" class="btn btn-sm btn-outline-light" id="siga-chat-new">Nueva</button> ' +
      '<button type="button" class="siga-chat-close" id="siga-chat-close" aria-label="Cerrar chat">×</button></div>' +
      "</div>" +
      '<p class="siga-chat-banner" data-guard-banner>El agente aplica políticas de mínimo privilegio y autorizaciones.</p>' +
      adminBlock +
      '<div class="siga-chat-tabs" role="tablist">' +
      '<button type="button" class="btn btn-sm btn-siga" data-chat-tab="chat">Chat</button>' +
      '<button type="button" class="btn btn-sm btn-outline-secondary" data-chat-tab="eval">Evaluación</button>' +
      "</div>" +
      '<div id="siga-chat-pane">' +
      '<div class="siga-chat-thread" id="siga-chat-thread" aria-live="polite">' +
      '<p class="empty-state mb-0">Use las preguntas de su rol. Con políticas activas las no autorizadas salen DENY; con políticas off, ALLOW.</p>' +
      "</div>" +
      '<div class="siga-eval-hints" id="siga-eval-hints"></div>' +
      '<div class="siga-chat-composer">' +
      '<label class="visually-hidden" for="siga-chat-input">Mensaje al agente</label>' +
      '<input id="siga-chat-input" maxlength="4000" autocomplete="off" placeholder="Escribe al agente" />' +
      '<button type="button" class="btn btn-siga btn-sm" id="siga-chat-send">Enviar</button>' +
      "</div></div>" +
      '<div id="siga-eval-root" class="siga-eval-pane" hidden></div>';
    document.body.appendChild(dock);
    document.body.appendChild(fab);

    function toggle(open) {
      var show = open !== false && dock.hidden;
      if (typeof open === "boolean") show = open;
      dock.hidden = !show;
      if (fab) {
        fab.classList.toggle("open", show);
        fab.setAttribute("aria-expanded", show ? "true" : "false");
      }
      if (show) {
        loadGuard();
        loadHistory(el("siga-chat-thread"));
        var input = el("siga-chat-input");
        if (input) input.focus();
      }
    }

    if (fab) fab.addEventListener("click", function () { toggle(); });
    var closeBtn = el("siga-chat-close");
    if (closeBtn) closeBtn.addEventListener("click", function () { toggle(false); });
    var newBtn = el("siga-chat-new");
    if (newBtn) {
      newBtn.addEventListener("click", function () {
        startNewConversation(el("siga-chat-thread"));
      });
    }
    var sendBtn = el("siga-chat-send");
    if (sendBtn) sendBtn.addEventListener("click", function () { sendFromWidget(); });
    var input = el("siga-chat-input");
    if (input) {
      input.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          sendFromWidget();
        }
      });
    }
    var gOn = el("siga-chat-guard-on");
    var gOff = el("siga-chat-guard-off");
    if (gOn) gOn.addEventListener("click", function () { setGuard(true); });
    if (gOff) {
      gOff.addEventListener("click", function () {
        if (window.confirm("¿Desactivar políticas de mínimo privilegio y controles de seguridad del agente?")) {
          setGuard(false);
        }
      });
    }
    dock.querySelectorAll("[data-chat-tab]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tab = btn.getAttribute("data-chat-tab");
        var chatPane = el("siga-chat-pane");
        var evalPane = el("siga-eval-root");
        if (chatPane) chatPane.hidden = tab !== "chat";
        if (evalPane) evalPane.hidden = tab !== "eval";
        dock.classList.toggle("eval-open", tab === "eval");
        if (tab === "eval") {
          var pageEval = document.getElementById("eval-root");
          if (pageEval) {
            pageEval.scrollIntoView({ behavior: "smooth", block: "start" });
          }
          if (window.SigaEval) SigaEval.mount();
        }
      });
    });
    window.sigaSendEvalQuestion = function (text, caseId) {
      if (typeof window.sigaSendPageQuestion === "function" && document.getElementById("ai-thread")) {
        window.sigaSendPageQuestion(text, caseId);
        return;
      }
      toggle(true);
      var chatPane = el("siga-chat-pane");
      var evalPane = el("siga-eval-root");
      if (chatPane) chatPane.hidden = false;
      if (evalPane) evalPane.hidden = true;
      sendFromWidget(text, caseId);
    };
    loadEvalPanel();
  }

  function wirePageControls() {
    var onBtn = el("btn-guard-on");
    var offBtn = el("btn-guard-off");
    if (onBtn && !onBtn.getAttribute("data-wired")) {
      onBtn.setAttribute("data-wired", "1");
      onBtn.addEventListener("click", function () { setGuard(true); });
    }
    if (offBtn && !offBtn.getAttribute("data-wired")) {
      offBtn.setAttribute("data-wired", "1");
      offBtn.addEventListener("click", function () {
        if (window.confirm("¿Desactivar políticas de mínimo privilegio y controles de seguridad del agente?")) {
          setGuard(false);
        }
      });
    }
  }

  function loadEvalPanel() {
    function boot() {
      if (window.SigaEval) {
        SigaEval.mount();
        SigaEval.loadCases();
      }
    }
    if (window.SigaEval) {
      boot();
      return;
    }
    if (document.querySelector("script[data-siga-eval]")) return;
    var script = document.createElement("script");
    script.src = "/ui/assets/js/components/eval-panel.js";
    script.setAttribute("data-siga-eval", "1");
    script.onload = boot;
    document.body.appendChild(script);
  }

  function mount() {
    if (document.getElementById("login-form")) return;
    if (mounted) {
      loadGuard();
      return;
    }
    mounted = true;
    buildDock();
    wirePageControls();
    loadGuard();
    loadHistory(el("siga-chat-thread"));
    window.addEventListener("siga-guard-changed", function (ev) {
      paintMode(ev.detail || {});
    });
  }

  window.SigaChatbot = { mount: mount, loadGuard: loadGuard, setGuard: setGuard, paintMode: paintMode };
})();
