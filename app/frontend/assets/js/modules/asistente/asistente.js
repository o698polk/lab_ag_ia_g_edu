/* global SigaApi, SigaAuth, SigaToast */
(async function () {
  if (!(await SigaAuth.requireAuth())) return;
  const { api, formatError, state } = SigaApi;
  const toast = SigaToast.toast;
  const thread = document.getElementById("ai-thread");
  const input = document.getElementById("ai-message");
  const sendBtn = document.getElementById("btn-ai-send");
  const statusEl = document.getElementById("ai-status");

  function setBusy(busy) {
    if (input) input.disabled = busy;
    if (sendBtn) sendBtn.disabled = busy;
    if (statusEl) {
      statusEl.textContent = busy ? "Consultando al agente…" : "";
      statusEl.classList.toggle("d-none", !busy);
    }
  }

  function appendBubble(role, text, meta, decision) {
    if (!thread) return;
    const empty = document.getElementById("ai-empty");
    if (empty) empty.classList.add("d-none");
    const div = document.createElement("div");
    const cls = decision === "DENY" ? "deny" : decision === "ALLOW" ? "allow" : "";
    div.className = ("siga-bubble " + role + " " + cls).trim();
    div.setAttribute("role", role === "bot" ? "status" : "group");
    const body = document.createElement("div");
    var shown = String(text || "").replace(/^\[Políticas desactivadas\]\s*/i, "");
    shown = shown.replace(/\s*request_id=[0-9a-fA-F-]{8,}\s*/g, " ").trim();
    body.textContent = shown;
    div.appendChild(body);
    if (meta) {
      const m = document.createElement("div");
      m.className = "meta";
      m.textContent = meta;
      div.appendChild(m);
    }
    thread.appendChild(div);
    thread.scrollTop = thread.scrollHeight;
  }

  function readMessage(message) {
    if (message != null && String(message).trim()) return String(message).trim();
    return String((input && input.value) || "").trim();
  }

  async function sendAi(message, caseId) {
    const msg = readMessage(message);
    if (!msg || (sendBtn && sendBtn.disabled)) return;
    if (input) input.value = "";
    appendBubble("user", msg);
    setBusy(true);
    const body = { message: msg };
    if (caseId) body.case_id = caseId;
    if (state.conversationId) body.conversation_id = state.conversationId;
    try {
      const { ok, status, data } = await api("POST", "/ai/chat", body, 45000);
      if (!ok) {
        appendBubble("bot", formatError(data), "HTTP " + status, "DENY");
        toast(formatError(data), "bad");
        return;
      }
      if (data.conversation_id) {
        state.conversationId = data.conversation_id;
        try { sessionStorage.setItem("siga.lab.conversation", String(data.conversation_id)); } catch (e) { /* ignore */ }
      }
      const meta =
        (data.scenario ? "Lab " + data.scenario + " · " : "") +
        (data.decision || "?") +
        " · " +
        (data.reason_code || "") +
        (data.policy_id ? " · " + data.policy_id : "");
      appendBubble("bot", data.reply || "(sin reply)", meta, data.decision);
      if (data.decision === "DENY") toast("Acción denegada por política", "bad");
    } finally {
      setBusy(false);
      if (input) input.focus();
    }
  }

  if (sendBtn) sendBtn.addEventListener("click", function () { sendAi(); });
  if (input) {
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        sendAi();
      }
    });
  }
  window.sigaSendPageQuestion = function (text, caseId) {
    sendAi(text, caseId);
  };
  window.sigaSendEvalQuestion = function (text, caseId) {
    sendAi(text, caseId);
  };
  if (window.SigaEval) SigaEval.mount();
  async function loadHistory() {
    var list = await api("GET", "/ai/conversations");
    if (!list.ok || !list.data || !list.data.length) return;
    var saved = state.conversationId;
    try {
      if (!saved) saved = parseInt(sessionStorage.getItem("siga.lab.conversation") || "", 10);
    } catch (e) {
      saved = null;
    }
    var exists = list.data.some(function (row) { return row.id === saved; });
    var targetId = exists ? saved : list.data[0].id;
    var detail = await api("GET", "/ai/conversations/" + targetId);
    if (!detail.ok || !detail.data) return;
    state.conversationId = detail.data.id;
    try { sessionStorage.setItem("siga.lab.conversation", String(detail.data.id)); } catch (e) { /* ignore */ }
    if (!thread || !detail.data.messages || !detail.data.messages.length) return;
    var empty = document.getElementById("ai-empty");
    if (empty) empty.classList.add("d-none");
    detail.data.messages.forEach(function (msg) {
      appendBubble(msg.role === "user" ? "user" : "bot", msg.content || "");
    });
  }

  var newBtn = document.getElementById("btn-ai-new");
  if (newBtn) {
    newBtn.addEventListener("click", async function () {
      var res = await api("POST", "/ai/conversations");
      if (!res.ok) {
        toast(formatError(res.data), "bad");
        return;
      }
      state.conversationId = res.data.id;
      try { sessionStorage.setItem("siga.lab.conversation", String(res.data.id)); } catch (e) { /* ignore */ }
      if (thread) {
        thread.textContent = "";
        var empty = document.createElement("p");
        empty.className = "empty-state mb-0";
        empty.id = "ai-empty";
        empty.textContent = "Escribe una consulta o usa un atajo.";
        thread.appendChild(empty);
      }
    });
  }

  await loadHistory();

  if (window.SigaChatbot && typeof SigaChatbot.loadGuard === "function") {
    SigaChatbot.loadGuard();
  } else {
    api("GET", "/ai/guard").then(function (res) {
      if (!res.ok || !res.data) return;
      var banner = document.getElementById("ai-guard-banner");
      if (!banner) return;
      var enforced = res.data.policies_enforced !== false;
      banner.textContent = enforced
        ? "El agente aplica políticas de mínimo privilegio y autorizaciones."
        : "Políticas desactivadas: el agente no aplica PDP ni controles de propiedad.";
      banner.classList.toggle("warn", !enforced);
    });
  }
})();
