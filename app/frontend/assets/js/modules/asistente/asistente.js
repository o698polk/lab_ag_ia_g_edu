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
    body.textContent = text;
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

  async function sendAi(message) {
    const msg = readMessage(message);
    if (!msg || (sendBtn && sendBtn.disabled)) return;
    if (input) input.value = "";
    appendBubble("user", msg);
    setBusy(true);
    const body = { message: msg };
    if (state.conversationId) body.conversation_id = state.conversationId;
    try {
      const { ok, status, data } = await api("POST", "/ai/chat", body, 45000);
      if (!ok) {
        appendBubble("bot", formatError(data), "HTTP " + status, "DENY");
        toast(formatError(data), "bad");
        return;
      }
      if (data.conversation_id) state.conversationId = data.conversation_id;
      const meta =
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
  document.querySelectorAll(".ai-hint").forEach(function (btn) {
    btn.addEventListener("click", function () { sendAi(btn.textContent); });
  });
})();
