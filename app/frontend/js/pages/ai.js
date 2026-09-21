// Ref: K-022 | AI assistant page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { api, formatError, state } = SigaApi;
  const { $, escapeHtml } = SigaUi;

  function appendBubble(role, text, meta, decision) {
    const thread = $("ai-thread");
    const div = document.createElement("div");
    const cls = decision === "DENY" ? "deny" : decision === "ALLOW" ? "allow" : "";
    div.className = `siga-bubble ${role} ${cls}`.trim();
    div.innerHTML = `${escapeHtml(text)}${meta ? `<div class="meta">${escapeHtml(meta)}</div>` : ""}`;
    thread.appendChild(div);
    thread.scrollTop = thread.scrollHeight;
  }

  async function sendAi(message) {
    const msg = (message ?? $("ai-message").value).trim();
    if (!msg) return;
    $("ai-message").value = "";
    appendBubble("user", msg);
    const body = { message: msg };
    if (state.conversationId) body.conversation_id = state.conversationId;
    const { ok, status, data } = await api("POST", "/ai/chat", body);
    if (!ok) {
      appendBubble("bot", formatError(data), `HTTP ${status}`, "DENY");
      return;
    }
    if (data.conversation_id) state.conversationId = data.conversation_id;
    const meta = `${data.decision} · ${data.reason_code}${data.policy_id ? ` · ${data.policy_id}` : ""}`;
    appendBubble("bot", data.reply || "(sin reply)", meta, data.decision);
  }

  $("btn-ai-send")?.addEventListener("click", () => sendAi());
  $("ai-message")?.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") sendAi();
  });
  document.querySelectorAll(".ai-hint").forEach((btn) => {
    btn.addEventListener("click", () => sendAi(btn.textContent));
  });
})();
