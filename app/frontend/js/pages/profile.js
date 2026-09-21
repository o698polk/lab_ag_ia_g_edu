// Ref: K-022 | Profile page
/* global SigaApi, SigaUi, SigaAuth */

(async function () {
  const ok = await SigaAuth.requireAuth();
  if (!ok) return;
  const { state } = SigaApi;
  const { $, escapeHtml } = SigaUi;

  const box = $("profile-body");
  const u = state.user;
  if (!box) return;
  if (!u) {
    box.innerHTML = `<p class="empty-state mb-0">No hay sesión.</p>`;
    return;
  }
  box.innerHTML = `
    <div class="row g-3">
      <div class="col-md-6"><div class="siga-metric"><div class="label">Usuario</div><div class="value" style="font-size:1.1rem">${escapeHtml(u.username)}</div></div></div>
      <div class="col-md-6"><div class="siga-metric"><div class="label">Correo</div><div class="value" style="font-size:1.1rem">${escapeHtml(u.email || "")}</div></div></div>
      <div class="col-md-6"><div class="siga-metric"><div class="label">Estado</div><div class="value" style="font-size:1.1rem">${escapeHtml(u.status || "")}</div></div></div>
      <div class="col-md-6"><div class="siga-metric"><div class="label">Roles</div><div class="value" style="font-size:1.1rem">${escapeHtml((u.roles || []).join(", "))}</div></div></div>
    </div>
    <p class="hint mt-3 mb-0">La UI no autoriza. Cada acción se revalida en el servidor (JWT + RBAC/ABAC).</p>
  `;

  $("btn-logout-profile")?.addEventListener("click", () => SigaAuth.logout());
})();
