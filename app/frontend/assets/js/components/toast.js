let _t;
function toast(message, kind) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = message;
  el.className = ("siga-toast show " + (kind || "")).trim();
  el.setAttribute("role", kind === "bad" ? "alert" : "status");
  el.setAttribute("aria-live", kind === "bad" ? "assertive" : "polite");
  clearTimeout(_t);
  _t = setTimeout(() => {
    el.classList.remove("show");
  }, 3400);
}
window.SigaToast = { toast };
