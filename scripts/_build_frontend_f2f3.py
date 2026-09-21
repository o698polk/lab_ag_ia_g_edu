# F2+F3 — generate assets, layout pages, legacy redirects.
# Run: python scripts/_build_frontend_f2f3.py
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "frontend"
ASSETS = ROOT / "assets"
PAGES = ROOT / "pages"

# ---------- CSS ----------
(ASSETS / "css").mkdir(parents=True, exist_ok=True)

(ASSETS / "css" / "base.css").write_text(
    """/* F2 base */
:root {
  --ink: #142033;
  --muted: #5d6b7c;
  --line: #e4eaf1;
  --bg: #f4f7fb;
  --card: #ffffff;
  --accent: #0c6e6a;
  --accent-2: #149089;
  --sidebar: #101a2b;
  --sidebar-text: #d5e2ef;
  --deny: #9b2c2c;
  --allow: #1b6b3a;
  --shadow: 0 16px 40px rgba(16, 26, 43, 0.08);
  --radius: 16px;
  --sidebar-w: 240px;
}
* { box-sizing: border-box; }
.d-none, .is-hidden { display: none !important; }
body {
  margin: 0;
  color: var(--ink);
  background: var(--bg);
  font-family: Manrope, "Segoe UI", sans-serif;
  min-height: 100vh;
}
a { color: inherit; }
""",
    encoding="utf-8",
)

(ASSETS / "css" / "layout.css").write_text(
    """/* F3 app shell: sidebar + topbar + content */
.app-frame {
  display: grid;
  grid-template-columns: var(--sidebar-w) 1fr;
  min-height: 100vh;
}
.app-sidebar {
  background: var(--sidebar);
  color: var(--sidebar-text);
  padding: 1.1rem 0.85rem 1.5rem;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
}
.app-brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 0.35rem 0.6rem 1.1rem;
}
.app-brand-dot {
  width: 12px; height: 12px; border-radius: 50%;
  background: #3dcec4; flex: none;
}
.side-nav { display: flex; flex-direction: column; gap: 0.25rem; }
.side-link {
  display: block;
  text-decoration: none;
  color: var(--sidebar-text);
  border-radius: 12px;
  padding: 0.55rem 0.75rem;
  font-weight: 600;
  font-size: 0.92rem;
}
.side-link:hover { background: rgba(255,255,255,0.08); color: #fff; }
.side-link.active { background: #fff; color: var(--sidebar); }
.side-section {
  margin: 0.85rem 0.6rem 0.35rem;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.55;
}
.app-main { min-width: 0; display: flex; flex-direction: column; }
.app-topbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.25rem;
  background: #fff;
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  z-index: 5;
}
.btn-sidebar {
  display: none;
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 10px;
  padding: 0.4rem 0.7rem;
  font-weight: 600;
}
.topbar-title { margin: 0; font-size: 1.05rem; font-weight: 700; }
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: 0.55rem; }
.breadcrumb {
  display: flex; flex-wrap: wrap; gap: 0.35rem;
  padding: 0.75rem 1.25rem 0;
  color: var(--muted);
  font-size: 0.88rem;
}
.breadcrumb a { color: var(--accent); text-decoration: none; font-weight: 600; }
.breadcrumb span.sep { opacity: 0.45; }
.app-content { padding: 1rem 1.25rem 2rem; max-width: 1100px; }
.app-frame.nav-open .app-sidebar { transform: translateX(0); }

/* Public gate */
.gate {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  position: relative;
  background:
    radial-gradient(800px 400px at 80% 0%, rgba(12, 110, 106, 0.18), transparent 60%),
    linear-gradient(160deg, #0e1a2c 0%, #16324a 45%, #0c6e6a 100%);
}
.public-nav {
  position: absolute; top: 1rem; left: 50%; transform: translateX(-50%);
  display: flex; gap: 0.5rem; z-index: 2;
}
.public-nav-link {
  color: #fff; text-decoration: none; font-weight: 600;
  padding: 0.35rem 0.8rem; border-radius: 999px;
  background: rgba(255,255,255,0.12);
}
.public-nav-link:hover, .public-nav-link.active { background: #fff; color: var(--sidebar); }
.gate-card {
  width: min(440px, 100%);
  background: #fff;
  border-radius: 24px;
  padding: 2rem 1.6rem 1.4rem;
  box-shadow: var(--shadow);
}
.gate-mark { font-weight: 700; letter-spacing: 0.14em; color: var(--accent); }
.gate-card h1 { font-size: 1.7rem; margin: 0.4rem 0; }
.gate-lead { color: var(--muted); margin-bottom: 1.4rem; }
""",
    encoding="utf-8",
)

(ASSETS / "css" / "components.css").write_text(
    """/* Shared UI components */
.btn-siga {
  background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600;
}
.btn-siga:hover { background: var(--accent-2); border-color: var(--accent-2); color: #fff; }
.siga-chip {
  background: #eef6f5; color: var(--accent);
  border-radius: 999px; padding: 0.35rem 0.8rem;
  font-size: 0.85rem; font-weight: 600; text-decoration: none;
}
.siga-toast {
  position: fixed; top: 16px; right: 16px; z-index: 40;
  max-width: min(420px, calc(100vw - 32px));
  padding: 0.85rem 1rem; border-radius: 14px;
  background: #142033; color: #fff; box-shadow: var(--shadow);
  opacity: 0; transform: translateY(-8px); pointer-events: none; transition: 0.2s ease;
}
.siga-toast.show { opacity: 1; transform: none; }
.siga-toast.ok { background: var(--allow); }
.siga-toast.bad { background: var(--deny); }
.panel-head { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }
.eyebrow { margin: 0; font-weight: 700; }
.hint { margin: 0.2rem 0 0; color: var(--muted); font-size: 0.92rem; }
.card-soft, .siga-metric, .notif-item, .empty-state {
  background: var(--card); border: 1px solid var(--line);
  border-radius: var(--radius); box-shadow: 0 8px 24px rgba(16, 26, 43, 0.04);
}
.card-soft { padding: 1.1rem 1.15rem; }
.card-soft h3 { font-size: 1rem; margin: 0 0 0.9rem; }
.siga-metric { padding: 1rem 1.1rem; height: 100%; }
.siga-metric .label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
.siga-metric .value { font-size: 1.6rem; font-weight: 700; margin-top: 0.25rem; }
.empty-state { padding: 1.4rem; color: var(--muted); }
.notif-item { padding: 0.9rem 1rem; margin-bottom: 0.6rem; }
.notif-item.read { opacity: 0.62; }
.chip-row { display: flex; flex-wrap: wrap; gap: 0.45rem; }
.role-chip {
  border: 1px solid var(--line); background: #f7fafc; border-radius: 999px;
  padding: 0.35rem 0.75rem; font-size: 0.85rem;
}
.role-chip:hover, .role-chip.active { border-color: var(--accent); color: var(--accent); }
.gate-roles { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.2rem; }
.login-error {
  margin: 0.9rem 0 0; padding: 0.7rem 0.85rem; border-radius: 12px;
  background: #fdecec; color: var(--deny); font-size: 0.9rem; font-weight: 600;
}
.login-status {
  margin: 0 0 1rem; padding: 0.65rem 0.85rem; border-radius: 12px;
  background: #eef6f5; color: var(--accent); font-size: 0.9rem; font-weight: 600;
}
.siga-thread {
  min-height: 16rem; max-height: 28rem; overflow: auto;
  background: #fff; border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem;
}
.siga-bubble {
  border-radius: 14px; padding: 0.7rem 0.85rem; margin-bottom: 0.65rem;
  max-width: 85%; white-space: pre-wrap; word-break: break-word;
}
.siga-bubble.user { background: #142033; color: #fff; margin-left: auto; }
.siga-bubble.bot { background: #f4f7fb; }
.siga-bubble .meta { font-size: 0.75rem; margin-top: 0.35rem; }
.siga-bubble.deny .meta { color: var(--deny); font-weight: 700; }
.siga-bubble.allow .meta { color: var(--allow); font-weight: 700; }
.composer { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
.composer .form-control { flex: 1; }
.siga-log {
  background: #101a2b; color: #d7e6f0; border-radius: 12px;
  padding: 0.9rem 1rem; font-family: ui-monospace, Consolas, monospace;
  font-size: 0.78rem; white-space: pre-wrap; max-height: 14rem; overflow: auto; margin-top: 0.5rem;
}
""",
    encoding="utf-8",
)

(ASSETS / "css" / "forms.css").write_text(
    """/* Forms */
.form-control, .form-select {
  border-radius: 12px; border-color: #d5dee8; min-height: 44px;
}
.form-label { font-weight: 600; font-size: 0.9rem; }
.gate-health { color: var(--muted); text-decoration: none; margin-top: 0.4rem; }
""",
    encoding="utf-8",
)

(ASSETS / "css" / "tables.css").write_text(
    """/* Tables — structure lives in HTML; JS fills tbody only */
.table-wrap {
  overflow: auto; background: #fff; border: 1px solid var(--line); border-radius: var(--radius);
}
.data-table { margin: 0; width: 100%; }
.data-table thead th {
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.03em;
  color: var(--muted); background: #f8fafc; white-space: nowrap;
}
.data-table td { vertical-align: middle; }
""",
    encoding="utf-8",
)

(ASSETS / "css" / "responsive.css").write_text(
    """/* Responsive */
@media (max-width: 900px) {
  .app-frame { grid-template-columns: 1fr; }
  .app-sidebar {
    position: fixed; left: 0; top: 0; z-index: 20; width: min(280px, 86vw);
    transform: translateX(-105%); transition: transform 0.2s ease;
  }
  .app-frame.nav-open .app-sidebar { transform: translateX(0); }
  .btn-sidebar { display: inline-flex; }
  .composer { flex-direction: column; }
  .topbar-actions .siga-chip { display: none; }
}
""",
    encoding="utf-8",
)

# Keep legacy main.css as import bridge for old links
(ROOT / "css" / "main.css").write_text(
    """/* Bridge → assets/css (F2). Prefer linking assets directly. */
@import url("/ui/assets/css/base.css");
@import url("/ui/assets/css/layout.css");
@import url("/ui/assets/css/components.css");
@import url("/ui/assets/css/forms.css");
@import url("/ui/assets/css/tables.css");
@import url("/ui/assets/css/responsive.css");
""",
    encoding="utf-8",
)

print("CSS OK")

# ---------- Core JS: copy api ----------
api_src = ROOT / "js" / "api.js"
api_dst = ASSETS / "js" / "core" / "api.js"
api_dst.write_text(api_src.read_text(encoding="utf-8"), encoding="utf-8")

(ASSETS / "js" / "core" / "auth.js").write_text(
    """// Ref: K-015/K-022 | UI guard — server authorizes.
/* global SigaApi, SigaToast, SigaNav */
const LOGIN_URL = "/ui/pages/auth/login.html";

async function requireAuth() {
  if (!window.SigaApi) { location.replace(LOGIN_URL); return false; }
  SigaApi.applyStoredTokens();
  const { state, api, clearSession } = SigaApi;
  if (!state.accessToken && !state.refreshToken) {
    clearSession(); location.replace(LOGIN_URL); return false;
  }
  let me = await api("GET", "/auth/me", undefined, 5000);
  if (!me.ok && me.status === 401 && state.refreshToken) {
    const ok = await SigaApi.refreshAccessToken();
    if (ok) me = await api("GET", "/auth/me", undefined, 5000, false);
  }
  if (!me.ok || !me.data || !me.data.username) {
    clearSession(); location.replace(LOGIN_URL); return false;
  }
  state.user = me.data;
  applyRoleVisibility(me.data);
  const chip = document.getElementById("session-chip");
  if (chip) {
    chip.textContent = me.data.username + " · " + ((me.data.roles || []).join(", ") || "sin rol");
    chip.classList.add("ok"); chip.classList.remove("muted");
  }
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) logoutBtn.addEventListener("click", () => logout());
  if (window.SigaNav) SigaNav.wire();
  return true;
}

function applyRoleVisibility(user) {
  const roles = (user && user.roles) || [];
  document.querySelectorAll("[data-roles]").forEach((el) => {
    const wanted = String(el.getAttribute("data-roles") || "").split(",").map((r) => r.trim()).filter(Boolean);
    const show = !wanted.length || wanted.some((r) => roles.includes(r));
    el.classList.toggle("d-none", !show);
  });
}

async function logout() {
  const { state, api, clearSession } = SigaApi;
  if (state.refreshToken) await api("POST", "/auth/logout", { refresh_token: state.refreshToken });
  clearSession(); state.user = null; location.replace(LOGIN_URL);
}

function redirectIfAuthed() {
  if (!window.SigaApi) return;
  SigaApi.applyStoredTokens();
  if (SigaApi.state.accessToken || SigaApi.state.refreshToken) {
    location.replace("/ui/pages/dashboard/dashboard.html");
  }
}

window.SigaAuth = { requireAuth, logout, redirectIfAuthed, applyRoleVisibility, LOGIN_URL };
""",
    encoding="utf-8",
)

(ASSETS / "js" / "core" / "navigation.js").write_text(
    """// Sidebar mobile toggle only — structure is HTML.
function wire() {
  const frame = document.querySelector(".app-frame");
  const btn = document.getElementById("btn-sidebar");
  if (!frame || !btn) return;
  btn.addEventListener("click", () => {
    const open = frame.classList.toggle("nav-open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
}
window.SigaNav = { wire };
""",
    encoding="utf-8",
)

(ASSETS / "js" / "components" / "toast.js").write_text(
    """let _t;
function toast(message, kind) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = message;
  el.className = ("siga-toast show " + (kind || "")).trim();
  clearTimeout(_t);
  _t = setTimeout(() => el.classList.remove("show"), 3400);
}
window.SigaToast = { toast };
""",
    encoding="utf-8",
)

(ASSETS / "js" / "components" / "table.js").write_text(
    """// Fill existing <tbody> only — table/thead must exist in HTML.
const COL_LABEL = {
  id: "Id", score: "Nota", comment: "Comentario", evaluation_id: "Evaluación",
  student_id: "Estudiante", graded_by_teacher_id: "Docente", graded_at: "Fecha",
  academic_status: "Estado académico", final_grade: "Nota final", credits: "Créditos",
  term_id: "Periodo", subject_id: "Materia", course_id: "Curso", code: "Código",
  name: "Nombre", status: "Estado", parallel_code: "Paralelo", capacity: "Cupo",
  title: "Título", body: "Mensaje", type: "Tipo", student_code: "Código estudiante",
  teacher_code: "Código docente", specialty: "Especialidad", level: "Nivel",
  username: "Usuario", email: "Correo",
};

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function fillTbody(tbody, rows, columns) {
  if (!tbody) return;
  if (!rows || !rows.length) {
    tbody.innerHTML = "";
    const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
    if (empty) empty.classList.remove("d-none");
    return;
  }
  const empty = tbody.closest(".table-wrap")?.querySelector("[data-empty]");
  if (empty) empty.classList.add("d-none");
  const keys = columns && columns.length ? columns : Object.keys(rows[0]);
  tbody.innerHTML = rows
    .map((row) => `<tr>${keys.map((k) => `<td>${escapeHtml(row[k] ?? "")}</td>`).join("")}</tr>`)
    .join("");
}

function fillSelect(el, items, labelFn, valueFn) {
  if (!el) return;
  const current = el.value;
  if (!items || !items.length) {
    el.innerHTML = '<option value="">Sin datos</option>';
    return;
  }
  el.innerHTML = items
    .map((item) => `<option value="${valueFn(item)}">${escapeHtml(labelFn(item))}</option>`)
    .join("");
  if (current && [...el.options].some((o) => o.value === current)) el.value = current;
}

window.SigaTable = { fillTbody, fillSelect, escapeHtml, COL_LABEL };
""",
    encoding="utf-8",
)

print("Core JS OK")

# ---------- CSS link helper ----------
CSS_LINKS = """
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="/ui/assets/css/base.css" />
  <link rel="stylesheet" href="/ui/assets/css/layout.css" />
  <link rel="stylesheet" href="/ui/assets/css/components.css" />
  <link rel="stylesheet" href="/ui/assets/css/forms.css" />
  <link rel="stylesheet" href="/ui/assets/css/tables.css" />
  <link rel="stylesheet" href="/ui/assets/css/responsive.css" />
"""

CORE_SCRIPTS = """
  <script src="/ui/assets/js/core/api.js"></script>
  <script src="/ui/assets/js/components/toast.js"></script>
  <script src="/ui/assets/js/components/table.js"></script>
  <script src="/ui/assets/js/core/navigation.js"></script>
  <script src="/ui/assets/js/core/auth.js"></script>
"""

NAV = [
    ("Dashboard", "/ui/pages/dashboard/dashboard.html", "dashboard", None),
    ("Notas", "/ui/pages/notas/notas.html", "notas", None),
    ("Asistencia", "/ui/pages/asistencia/asistencia.html", "asistencia", "TEACHER,ADMINISTRATOR"),
    ("Catálogos", "/ui/pages/catalogos/catalogos.html", "catalogos", "ADMINISTRATOR"),
    ("Reportes", "/ui/pages/reportes/reportes.html", "reportes", "TEACHER,ADMINISTRATOR"),
    ("Avisos", "/ui/pages/avisos/avisos.html", "avisos", None),
    ("Asistente", "/ui/pages/asistente/asistente.html", "asistente", None),
    ("Perfil", "/ui/pages/cuenta/perfil.html", "cuenta", None),
]


def sidebar(active: str) -> str:
    links = []
    for label, href, key, roles in NAV:
        cls = "side-link active" if key == active else "side-link"
        dr = f' data-roles="{roles}"' if roles else ""
        links.append(f'<a class="{cls}" href="{href}"{dr}>{label}</a>')
    return f"""
<aside class="app-sidebar" aria-label="Menú principal">
  <a class="app-brand" href="/ui/pages/dashboard/dashboard.html">
    <span class="app-brand-dot"></span><span>SIGA</span>
  </a>
  <p class="side-section">Módulos</p>
  <nav class="side-nav">{"".join(links)}</nav>
</aside>
"""


def shell(title: str, active: str, crumbs: list[tuple[str, str | None]], body: str, module_js: str) -> str:
    bc = []
    for i, (label, href) in enumerate(crumbs):
        if i:
            bc.append('<span class="sep">/</span>')
        if href:
            bc.append(f'<a href="{href}">{label}</a>')
        else:
            bc.append(f"<span>{label}</span>")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} · SIGA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet" />
{CSS_LINKS}
</head>
<body>
  <div id="toast" class="siga-toast" role="status" aria-live="polite"></div>
  <div class="app-frame">
{sidebar(active)}
    <div class="app-main">
      <header class="app-topbar">
        <button type="button" id="btn-sidebar" class="btn-sidebar" aria-expanded="false" aria-label="Abrir menú">Menú</button>
        <h1 class="topbar-title">{title}</h1>
        <div class="topbar-actions">
          <a href="/ui/pages/cuenta/perfil.html" id="session-chip" class="siga-chip muted">Sin sesión</a>
          <a class="btn btn-outline-secondary btn-sm" href="/ui/pages/cuenta/perfil.html">Perfil</a>
          <button type="button" id="btn-logout" class="btn btn-outline-secondary btn-sm">Cerrar sesión</button>
        </div>
      </header>
      <nav class="breadcrumb" aria-label="Miga de pan">{"".join(bc)}</nav>
      <main class="app-content">
{body}
      </main>
    </div>
  </div>
{CORE_SCRIPTS}
  <script src="{module_js}"></script>
</body>
</html>
"""


def public_page(title: str, active: str, card: str, extra_scripts: str = "") -> str:
    def nav_cls(name: str) -> str:
        return " active" if name == active else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} · SIGA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet" />
{CSS_LINKS}
</head>
<body>
  <div id="toast" class="siga-toast" role="status" aria-live="polite"></div>
  <section class="gate">
    <nav class="public-nav" aria-label="Navegación pública">
      <a class="public-nav-link{nav_cls("home")}" href="/ui/pages/home.html">Inicio</a>
      <a class="public-nav-link{nav_cls("login")}" href="/ui/pages/auth/login.html">Login</a>
      <a class="public-nav-link{nav_cls("registro")}" href="/ui/pages/auth/registro.html">Registro</a>
    </nav>
{card}
  </section>
{extra_scripts}
</body>
</html>
"""


# Home
(PAGES / "home.html").write_text(
    public_page(
        "Inicio",
        "home",
        """    <div class="gate-card">
      <div class="gate-mark">SIGA</div>
      <h1>Laboratorio Zero Trust</h1>
      <p class="gate-lead">Sistema de gestión académica. La UI no autoriza: el servidor decide ALLOW o DENY.</p>
      <div class="d-grid gap-2">
        <a class="btn btn-siga btn-lg" href="/ui/pages/auth/login.html">Ir a Login</a>
        <a class="btn btn-outline-secondary btn-lg" href="/ui/pages/auth/registro.html">Registro / cuentas</a>
      </div>
      <p class="hint mt-3 mb-0">Home público. El dashboard requiere JWT válido.</p>
    </div>""",
    ),
    encoding="utf-8",
)

# Login
(PAGES / "auth").mkdir(parents=True, exist_ok=True)
(PAGES / "auth" / "login.html").write_text(
    public_page(
        "Login",
        "login",
        """    <div class="gate-card">
      <div class="gate-mark">SIGA</div>
      <h1>Iniciar sesión</h1>
      <p class="gate-lead">Entra con tu usuario. El sistema decide qué puedes ver y hacer.</p>
      <p id="login-status" class="login-status d-none" aria-live="polite"></p>
      <form id="login-form" autocomplete="on" onsubmit="return false;">
        <label class="form-label" for="username">Usuario</label>
        <input id="username" name="username" class="form-control form-control-lg" value="admin" autocomplete="username" required />
        <label class="form-label mt-3" for="password">Contraseña</label>
        <input id="password" name="password" type="password" class="form-control form-control-lg" value="Admin123!" autocomplete="current-password" required />
        <p id="login-error" class="login-error d-none" role="alert"></p>
        <button id="btn-login" type="button" class="btn btn-siga btn-lg w-100 mt-4">Entrar</button>
      </form>
      <div class="gate-roles" aria-label="Usuarios de demostración">
        <button type="button" class="role-chip active" data-user="admin" data-pass="Admin123!">Administrador</button>
        <button type="button" class="role-chip" data-user="teacher1" data-pass="Teacher123!">Docente</button>
        <button type="button" class="role-chip" data-user="student1" data-pass="Student123!">Estudiante</button>
      </div>
      <button id="btn-health" type="button" class="btn btn-link btn-sm gate-health">Comprobar servicio</button>
    </div>""",
        CORE_SCRIPTS + '\n  <script src="/ui/assets/js/modules/auth/login.js"></script>',
    ),
    encoding="utf-8",
)

(PAGES / "auth" / "registro.html").write_text(
    public_page(
        "Registro",
        "registro",
        """    <div class="gate-card">
      <div class="gate-mark">SIGA</div>
      <h1>Registro</h1>
      <p class="gate-lead">No hay auto-registro público (RF-IAM-001). El administrador da de alta usuarios con <code>POST /users</code>.</p>
      <p class="hint">Cuentas de laboratorio (seed IAM):</p>
      <ul class="hint">
        <li><code>admin</code> / <code>Admin123!</code></li>
        <li><code>teacher1</code> / <code>Teacher123!</code></li>
        <li><code>student1</code> / <code>Student123!</code></li>
      </ul>
      <p class="hint">Tras entrar como administrador, usa Catálogos → Usuarios.</p>
      <a class="btn btn-siga w-100" href="/ui/pages/auth/login.html">Ir a Login</a>
    </div>""",
    ),
    encoding="utf-8",
)

# Dashboard
dash_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow" id="role-badge">Vista según tu rol</p>
            <p class="hint">Indicadores del servidor. Las tarjetas existen en HTML; JS solo rellena valores.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-refresh-dash">Actualizar</button>
        </div>
        <div id="indicators" class="row g-3">
          <div class="col-6 col-md-3 d-none" data-metric="students"><div class="siga-metric"><div class="label">Estudiantes</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="teachers"><div class="siga-metric"><div class="label">Docentes</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="courses"><div class="siga-metric"><div class="label">Cursos</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="enrollments"><div class="siga-metric"><div class="label">Matrículas</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="users"><div class="siga-metric"><div class="label">Usuarios</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="grades"><div class="siga-metric"><div class="label">Notas</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="assigned_courses"><div class="siga-metric"><div class="label">Cursos asignados</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="my_courses"><div class="siga-metric"><div class="label">Mis cursos</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="my_grades"><div class="siga-metric"><div class="label">Mis notas</div><div class="value" data-value>—</div></div></div>
          <div class="col-6 col-md-3 d-none" data-metric="unread_notifications"><div class="siga-metric"><div class="label">Avisos</div><div class="value" data-value>—</div></div></div>
        </div>
        <p id="dash-empty" class="empty-state mt-3 d-none">Sin indicadores para este rol.</p>
"""
(PAGES / "dashboard" / "dashboard.html").write_text(
    shell(
        "Dashboard",
        "dashboard",
        [("Inicio", "/ui/pages/home.html"), ("Dashboard", None)],
        dash_body,
        "/ui/assets/js/modules/dashboard/dashboard.js",
    ),
    encoding="utf-8",
)

# Notas
notas_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Evaluación</p>
            <p class="hint">Consulta y registro. La tabla está definida en HTML.</p>
          </div>
        </div>
        <div class="row g-3">
          <div class="col-lg-5">
            <div class="card-soft">
              <h3>Consultar</h3>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <button type="button" class="btn btn-siga" id="btn-my-grades">Mis notas</button>
                <button type="button" class="btn btn-outline-secondary" id="btn-my-kardex">Mi kardex</button>
              </div>
              <label class="form-label" for="grades-course-id">Curso</label>
              <div class="input-group">
                <select id="grades-course-id" class="form-select"></select>
                <button type="button" class="btn btn-outline-secondary" id="btn-course-grades">Ver curso</button>
              </div>
            </div>
          </div>
          <div class="col-lg-7" data-roles="TEACHER,ADMINISTRATOR">
            <div class="card-soft">
              <h3>Registrar nota</h3>
              <div class="row g-3">
                <div class="col-md-4">
                  <label class="form-label" for="grade-eval-id">Evaluación</label>
                  <select id="grade-eval-id" class="form-select"></select>
                </div>
                <div class="col-md-4">
                  <label class="form-label" for="grade-student-id">Estudiante</label>
                  <select id="grade-student-id" class="form-select"></select>
                </div>
                <div class="col-md-4">
                  <label class="form-label" for="grade-score">Nota (0 a 100)</label>
                  <input id="grade-score" type="number" class="form-control" min="0" max="100" step="0.01" value="90" />
                </div>
                <div class="col-12">
                  <label class="form-label" for="grade-comment">Comentario</label>
                  <input id="grade-comment" class="form-control" placeholder="Opcional" />
                </div>
                <div class="col-12">
                  <button type="button" class="btn btn-siga" id="btn-upsert-grade">Guardar nota</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="table-wrap mt-3">
          <p class="empty-state mb-0" data-empty>Sin resultados. Usa los botones de consulta.</p>
          <table class="table table-sm table-hover align-middle data-table">
            <thead>
              <tr>
                <th>Id</th><th>Evaluación</th><th>Estudiante</th><th>Nota</th><th>Comentario</th><th>Fecha</th>
              </tr>
            </thead>
            <tbody id="grades-tbody"></tbody>
          </table>
        </div>
"""
(PAGES / "notas" / "notas.html").write_text(
    shell("Notas", "notas", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Notas", None)], notas_body, "/ui/assets/js/modules/notas/notas.js"),
    encoding="utf-8",
)

# Asistencia
att_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Clase</p>
            <p class="hint">Registro rápido de sesión y asistencia.</p>
          </div>
        </div>
        <div class="row g-3">
          <div class="col-lg-6">
            <div class="card-soft">
              <h3>Nueva sesión</h3>
              <div class="row g-3">
                <div class="col-4">
                  <label class="form-label" for="att-course-id">Curso</label>
                  <select id="att-course-id" class="form-select"></select>
                </div>
                <div class="col-4">
                  <label class="form-label" for="att-date">Fecha</label>
                  <input id="att-date" type="date" class="form-control" />
                </div>
                <div class="col-4">
                  <label class="form-label" for="att-topic">Tema</label>
                  <input id="att-topic" class="form-control" placeholder="Clase" />
                </div>
                <div class="col-12">
                  <button type="button" class="btn btn-siga" id="btn-create-session">Crear sesión</button>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="card-soft">
              <h3>Marcar</h3>
              <div class="row g-3">
                <div class="col-md-4">
                  <label class="form-label" for="att-session-id">Sesión (id)</label>
                  <input id="att-session-id" type="number" class="form-control" min="1" value="1" />
                </div>
                <div class="col-md-4">
                  <label class="form-label" for="att-student-id">Estudiante</label>
                  <select id="att-student-id" class="form-select"></select>
                </div>
                <div class="col-md-4">
                  <label class="form-label" for="att-status">Estado</label>
                  <select id="att-status" class="form-select">
                    <option value="PRESENT">Presente</option>
                    <option value="ABSENT">Ausente</option>
                    <option value="LATE">Atraso</option>
                    <option value="JUSTIFIED">Justificado</option>
                  </select>
                </div>
                <div class="col-12">
                  <button type="button" class="btn btn-siga" id="btn-mark-att">Guardar asistencia</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="card-soft mt-3">
          <h3>Porcentaje</h3>
          <div class="row g-2 align-items-end">
            <div class="col-sm-4">
              <label class="form-label" for="pct-course-id">Curso</label>
              <select id="pct-course-id" class="form-select"></select>
            </div>
            <div class="col-sm-4">
              <label class="form-label" for="pct-student-id">Estudiante</label>
              <select id="pct-student-id" class="form-select"></select>
            </div>
            <div class="col-sm-4">
              <button type="button" class="btn btn-outline-secondary w-100" id="btn-att-pct">Consultar</button>
            </div>
          </div>
        </div>
"""
(PAGES / "asistencia" / "asistencia.html").write_text(
    shell("Asistencia", "asistencia", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Asistencia", None)], att_body, "/ui/assets/js/modules/asistencia/asistencia.js"),
    encoding="utf-8",
)

# Catalogos
cat_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Administración</p>
            <p class="hint">Listados vía API. Tabla con thead en HTML.</p>
          </div>
        </div>
        <div class="chip-row mb-3">
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/careers" data-cols="id,code,name,modality">Carreras</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/subjects" data-cols="id,code,name,credits">Materias</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/terms" data-cols="id,code,name,status">Periodos</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/teachers" data-cols="id,teacher_code,specialty">Docentes</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/students" data-cols="id,student_code">Estudiantes</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/courses" data-cols="id,subject_id,parallel_code,capacity,status">Cursos</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/enrollments" data-cols="id,student_id,course_id,status">Matrículas</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/users" data-cols="id,username,email,status">Usuarios</button>
        </div>
        <div class="card-soft mb-3">
          <h3>Alta de usuario (POST /users)</h3>
          <div class="row g-2 align-items-end">
            <div class="col-md-3"><label class="form-label" for="reg-username">Usuario</label><input id="reg-username" class="form-control" /></div>
            <div class="col-md-3"><label class="form-label" for="reg-email">Correo</label><input id="reg-email" class="form-control" /></div>
            <div class="col-md-2"><label class="form-label" for="reg-password">Contraseña</label><input id="reg-password" type="password" class="form-control" /></div>
            <div class="col-md-2">
              <label class="form-label" for="reg-role">Rol</label>
              <select id="reg-role" class="form-select">
                <option value="STUDENT">STUDENT</option>
                <option value="TEACHER">TEACHER</option>
                <option value="ADMINISTRATOR">ADMINISTRATOR</option>
              </select>
            </div>
            <div class="col-md-2"><button type="button" class="btn btn-siga w-100" id="btn-create-user">Registrar</button></div>
          </div>
          <p id="reg-out" class="hint mt-2 mb-0"></p>
        </div>
        <div class="table-wrap">
          <p class="empty-state mb-0" data-empty>Selecciona un catálogo.</p>
          <table class="table table-sm table-hover align-middle data-table">
            <thead><tr id="catalog-thead-row"><th>Datos</th></tr></thead>
            <tbody id="catalog-tbody"></tbody>
          </table>
        </div>
"""
(PAGES / "catalogos" / "catalogos.html").write_text(
    shell("Catálogos", "catalogos", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Catálogos", None)], cat_body, "/ui/assets/js/modules/catalogos/catalogos.js"),
    encoding="utf-8",
)

# Reportes
rep_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Informes</p>
            <p class="hint">Generación vía API existente.</p>
          </div>
        </div>
        <div class="card-soft">
          <div class="row g-3 align-items-end">
            <div class="col-md-5">
              <label class="form-label" for="report-type">Tipo</label>
              <select id="report-type" class="form-select">
                <option value="grades">Notas</option>
                <option value="attendance">Asistencia</option>
                <option value="enrollments">Matrículas</option>
                <option value="students">Estudiantes</option>
                <option value="teachers">Docentes</option>
                <option value="kardex">Kardex</option>
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label" for="report-format">Formato</label>
              <select id="report-format" class="form-select">
                <option value="JSON">JSON</option>
                <option value="CSV">CSV</option>
                <option value="HTML">HTML</option>
              </select>
            </div>
            <div class="col-md-4 d-flex gap-2">
              <button type="button" class="btn btn-siga" id="btn-report">Generar</button>
              <button type="button" class="btn btn-outline-secondary" id="btn-report-logs">Historial</button>
            </div>
          </div>
        </div>
        <pre id="report-out" class="siga-log mt-3"></pre>
"""
(PAGES / "reportes" / "reportes.html").write_text(
    shell("Reportes", "reportes", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Reportes", None)], rep_body, "/ui/assets/js/modules/reportes/reportes.js"),
    encoding="utf-8",
)

# Avisos
avisos_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Bandeja</p>
            <p class="hint">Avisos del usuario autenticado.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-refresh-notif">Actualizar</button>
        </div>
        <div id="notif-list">
          <p class="empty-state mb-0" id="notif-empty">Cargando…</p>
          <template id="notif-item-tpl">
            <div class="notif-item">
              <div class="d-flex justify-content-between gap-2">
                <strong data-field="title"></strong>
                <span class="small text-secondary" data-field="type"></span>
              </div>
              <div class="small mt-1" data-field="body"></div>
              <button type="button" class="btn btn-sm btn-outline-secondary mt-2 d-none" data-action="read">Marcar leída</button>
            </div>
          </template>
        </div>
"""
(PAGES / "avisos" / "avisos.html").write_text(
    shell("Avisos", "avisos", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Avisos", None)], avisos_body, "/ui/assets/js/modules/avisos/avisos.js"),
    encoding="utf-8",
)

# Asistente
ai_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Asistente</p>
            <p class="hint">Puede proponer acciones. Solo se ejecutan si la política lo permite.</p>
          </div>
        </div>
        <div id="ai-thread" class="siga-thread" aria-live="polite"></div>
        <div class="composer">
          <input id="ai-message" class="form-control" placeholder="Escribe tu consulta" maxlength="4000" />
          <button type="button" class="btn btn-siga" id="btn-ai-send">Enviar</button>
        </div>
        <div class="d-flex flex-wrap gap-2 mt-2">
          <button type="button" class="btn btn-sm btn-outline-secondary ai-hint">Cuáles son mis calificaciones?</button>
          <button type="button" class="btn btn-sm btn-outline-danger ai-hint">Cambia la nota del estudiante 2 a 100</button>
        </div>
"""
(PAGES / "asistente" / "asistente.html").write_text(
    shell("Asistente", "asistente", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Asistente", None)], ai_body, "/ui/assets/js/modules/asistente/asistente.js"),
    encoding="utf-8",
)

# Perfil
perfil_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Sesión</p>
            <p class="hint">Campos en HTML; JS solo asigna textContent.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-logout-profile">Cerrar sesión</button>
        </div>
        <div class="row g-3">
          <div class="col-md-6"><div class="siga-metric"><div class="label">Usuario</div><div class="value" style="font-size:1.1rem" id="pf-username">—</div></div></div>
          <div class="col-md-6"><div class="siga-metric"><div class="label">Correo</div><div class="value" style="font-size:1.1rem" id="pf-email">—</div></div></div>
          <div class="col-md-6"><div class="siga-metric"><div class="label">Estado</div><div class="value" style="font-size:1.1rem" id="pf-status">—</div></div></div>
          <div class="col-md-6"><div class="siga-metric"><div class="label">Roles</div><div class="value" style="font-size:1.1rem" id="pf-roles">—</div></div></div>
        </div>
        <p class="hint mt-3 mb-0">La UI no autoriza. Cada acción se revalida en el servidor.</p>
"""
(PAGES / "cuenta" / "perfil.html").write_text(
    shell("Perfil", "cuenta", [("Dashboard", "/ui/pages/dashboard/dashboard.html"), ("Perfil", None)], perfil_body, "/ui/assets/js/modules/cuenta/perfil.js"),
    encoding="utf-8",
)

# Components reference fragments (documentation / future include)
(ROOT / "components" / "sidebar.html").write_text(sidebar("dashboard"), encoding="utf-8")
(ROOT / "components" / "navbar.html").write_text(
    """<!-- Topbar fragment reference — baked into pages by build script -->
<header class="app-topbar">...</header>
""",
    encoding="utf-8",
)

# Index + legacy redirects
(ROOT / "index.html").write_text(
    """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=/ui/pages/home.html" />
  <title>SIGA</title>
  <script>location.replace("/ui/pages/home.html");</script>
</head>
<body><p><a href="/ui/pages/home.html">Ir a SIGA</a></p></body>
</html>
""",
    encoding="utf-8",
)

LEGACY = {
    "login.html": "/ui/pages/auth/login.html",
    "registro.html": "/ui/pages/auth/registro.html",
    "dashboard.html": "/ui/pages/dashboard/dashboard.html",
    "grades.html": "/ui/pages/notas/notas.html",
    "attendance.html": "/ui/pages/asistencia/asistencia.html",
    "catalog.html": "/ui/pages/catalogos/catalogos.html",
    "reports.html": "/ui/pages/reportes/reportes.html",
    "notifications.html": "/ui/pages/avisos/avisos.html",
    "ai.html": "/ui/pages/asistente/asistente.html",
    "profile.html": "/ui/pages/cuenta/perfil.html",
}
for old, new in LEGACY.items():
    (PAGES / old).write_text(
        f"""<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8" /><meta http-equiv="refresh" content="0;url={new}" />
<script>location.replace("{new}");</script>
<title>Redirigiendo…</title></head>
<body><p><a href="{new}">Continuar</a></p></body></html>
""",
        encoding="utf-8",
    )

print("Pages OK")
print("Done F2+F3 structure")
