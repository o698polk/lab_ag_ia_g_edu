# Generate multi-page frontend (one-shot). Run from repo root.
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "frontend"
PAGES = ROOT / "pages"
JS_PAGES = ROOT / "js" / "pages"
PAGES.mkdir(parents=True, exist_ok=True)
JS_PAGES.mkdir(parents=True, exist_ok=True)

HEAD = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} · SIGA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="/ui/css/main.css" />
</head>
<body>
  <div id="toast" class="siga-toast" role="status" aria-live="polite"></div>
"""

PUBLIC_NAV = """  <nav class="public-nav" aria-label="Navegación pública">
    <a class="public-nav-link{home}" href="/ui/pages/home.html">Inicio</a>
    <a class="public-nav-link{login}" href="/ui/pages/login.html">Login</a>
    <a class="public-nav-link{registro}" href="/ui/pages/registro.html">Registro</a>
  </nav>
"""

NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("grades", "Notas"),
    ("attendance", "Asistencia"),
    ("ai", "Asistente"),
    ("notifications", "Avisos"),
    ("catalog", "Catálogo"),
    ("reports", "Reportes"),
    ("profile", "Perfil"),
]

ROLE_ATTR = {
    "attendance": ' data-roles="TEACHER,ADMINISTRATOR"',
    "catalog": ' data-roles="ADMINISTRATOR"',
    "reports": ' data-roles="TEACHER,ADMINISTRATOR"',
}


def shell_nav(active: str) -> str:
    links = []
    for key, label in NAV_ITEMS:
        cls = "siga-nav-btn active" if key == active else "siga-nav-btn"
        extra = ROLE_ATTR.get(key, "")
        links.append(
            f'<a class="{cls}" href="/ui/pages/{key}.html"{extra}><span>{label}</span></a>'
        )
    return f"""  <div class="shell">
    <header class="topbar">
      <div class="topbar-row">
        <button id="btn-menu" type="button" class="btn btn-menu" aria-label="Abrir menú" aria-expanded="false">Menú</button>
        <a class="brand" href="/ui/pages/dashboard.html">
          <span class="brand-dot"></span>
          <strong>SIGA</strong>
        </a>
        <h2 class="page-title">{dict(NAV_ITEMS).get(active, "SIGA")}</h2>
        <div class="topbar-user">
          <a href="/ui/pages/profile.html" id="session-chip" class="siga-chip muted">Sin sesión</a>
          <a class="btn btn-outline-secondary btn-sm" href="/ui/pages/profile.html">Perfil</a>
          <button id="btn-logout" type="button" class="btn btn-outline-secondary btn-sm">Cerrar sesión</button>
        </div>
      </div>
      <nav class="siga-navbar" aria-label="Módulos">
        {"".join(links)}
      </nav>
    </header>
    <div class="workspace">
      <main class="content">
"""


def shell_end(scripts: list[str]) -> str:
    tags = "\n".join(f'  <script src="{s}"></script>' for s in scripts)
    return f"""      </main>
    </div>
  </div>
{tags}
</body>
</html>
"""


SCRIPTS_BASE = [
    "/ui/js/api.js",
    "/ui/js/ui-common.js",
    "/ui/js/auth-guard.js",
]

# --- public pages ---
home = HEAD.format(title="Inicio") + f"""  <section class="gate">
{PUBLIC_NAV.format(home=" active", login="", registro="")}
    <div class="gate-card">
      <div class="gate-mark">SIGA</div>
      <h1>Laboratorio Zero Trust</h1>
      <p class="gate-lead">Sistema de gestión académica. La UI no autoriza: el servidor decide ALLOW o DENY.</p>
      <div class="d-grid gap-2">
        <a class="btn btn-siga btn-lg" href="/ui/pages/login.html">Ir a Login</a>
        <a class="btn btn-outline-secondary btn-lg" href="/ui/pages/registro.html">Registro / cuentas</a>
      </div>
      <p class="hint mt-3 mb-0">Home público. El dashboard requiere JWT válido.</p>
    </div>
  </section>
</body>
</html>
"""
(PAGES / "home.html").write_text(home, encoding="utf-8")

login = HEAD.format(title="Login") + f"""  <section class="gate">
{PUBLIC_NAV.format(home="", login=" active", registro="")}
    <div class="gate-card">
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
    </div>
  </section>
  <script src="/ui/js/api.js"></script>
  <script src="/ui/js/ui-common.js"></script>
  <script src="/ui/js/auth-guard.js"></script>
  <script src="/ui/js/pages/login.js"></script>
</body>
</html>
"""
(PAGES / "login.html").write_text(login, encoding="utf-8")

registro = HEAD.format(title="Registro") + f"""  <section class="gate">
{PUBLIC_NAV.format(home="", login="", registro=" active")}
    <div class="gate-card">
      <div class="gate-mark">SIGA</div>
      <h1>Registro</h1>
      <p class="gate-lead">No hay auto-registro público (RF-IAM-001). El administrador da de alta usuarios con <code>POST /users</code>.</p>
      <p class="hint">Cuentas de laboratorio (seed IAM):</p>
      <ul class="hint">
        <li><code>admin</code> / <code>Admin123!</code></li>
        <li><code>teacher1</code> / <code>Teacher123!</code></li>
        <li><code>student1</code> / <code>Student123!</code></li>
      </ul>
      <p class="hint">Tras entrar como administrador, usa Catálogo → Alta de usuario.</p>
      <a class="btn btn-siga w-100" href="/ui/pages/login.html">Ir a Login</a>
    </div>
  </section>
</body>
</html>
"""
(PAGES / "registro.html").write_text(registro, encoding="utf-8")

# --- protected pages content ---
dashboard_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow" id="role-badge">Vista según tu rol</p>
            <p class="hint">Resumen que entrega el servidor. No se calcula en el navegador.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-refresh-dash">Actualizar</button>
        </div>
        <div id="indicators" class="row g-3"></div>
        <p id="context-hint" class="hint mt-3 mb-0"></p>
"""

grades_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Evaluación</p>
            <p class="hint">Consulta tus notas o, si eres docente, registra una calificación.</p>
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
        <div id="grades-table" class="table-wrap mt-3"></div>
"""

attendance_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Clase</p>
            <p class="hint">Crea la sesión del día y marca la asistencia. El servidor valida la asignación.</p>
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

notifications_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Bandeja</p>
            <p class="hint">Avisos dirigidos a tu usuario.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-refresh-notif">Actualizar</button>
        </div>
        <div id="notif-list"></div>
"""

catalog_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Administración</p>
            <p class="hint">Elige una lista. Si no tienes permiso, el servidor responde DENY.</p>
          </div>
        </div>
        <div class="chip-row">
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/careers">Carreras</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/subjects">Materias</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/terms">Periodos</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/teachers">Docentes</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/students">Estudiantes</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/courses">Cursos</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/enrollments">Matrículas</button>
          <button type="button" class="btn btn-sm btn-outline-secondary catalog-load" data-path="/users">Usuarios</button>
        </div>
        <div class="card-soft mt-3">
          <h3>Alta de usuario (POST /users)</h3>
          <div class="row g-2 align-items-end">
            <div class="col-md-3">
              <label class="form-label" for="reg-username">Usuario</label>
              <input id="reg-username" class="form-control" placeholder="nuevo1" />
            </div>
            <div class="col-md-3">
              <label class="form-label" for="reg-email">Correo</label>
              <input id="reg-email" class="form-control" placeholder="nuevo1@siga.local" />
            </div>
            <div class="col-md-2">
              <label class="form-label" for="reg-password">Contraseña</label>
              <input id="reg-password" type="password" class="form-control" placeholder="Min 8" />
            </div>
            <div class="col-md-2">
              <label class="form-label" for="reg-role">Rol</label>
              <select id="reg-role" class="form-select">
                <option value="STUDENT">STUDENT</option>
                <option value="TEACHER">TEACHER</option>
                <option value="ADMINISTRATOR">ADMINISTRATOR</option>
              </select>
            </div>
            <div class="col-md-2">
              <button type="button" class="btn btn-siga w-100" id="btn-create-user">Registrar</button>
            </div>
          </div>
          <p id="reg-out" class="hint mt-2 mb-0"></p>
        </div>
        <div id="catalog-table" class="table-wrap mt-3"></div>
"""

reports_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Informes</p>
            <p class="hint">Elige tipo y formato. El PDF sigue diferido en el laboratorio.</p>
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

profile_body = """
        <div class="panel-head">
          <div>
            <p class="eyebrow">Sesión</p>
            <p class="hint">Identidad revalidada con GET /auth/me. Cerrar sesión invalida el refresh en el servidor.</p>
          </div>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-logout-profile">Cerrar sesión</button>
        </div>
        <div id="profile-body" class="card-soft">
          <p class="empty-state mb-0">Cargando perfil…</p>
        </div>
"""

protected = {
    "dashboard": dashboard_body,
    "grades": grades_body,
    "attendance": attendance_body,
    "ai": ai_body,
    "notifications": notifications_body,
    "catalog": catalog_body,
    "reports": reports_body,
    "profile": profile_body,
}

for name, body in protected.items():
    title = dict(NAV_ITEMS).get(name, name.title())
    html = (
        HEAD.format(title=title)
        + shell_nav(name)
        + body
        + shell_end(SCRIPTS_BASE + [f"/ui/js/pages/{name}.js"])
    )
    (PAGES / f"{name}.html").write_text(html, encoding="utf-8")

print("HTML pages:", sorted(p.name for p in PAGES.glob("*.html")))
